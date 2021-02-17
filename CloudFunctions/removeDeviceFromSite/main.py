
#Author(s): Connor Williams
#Date: 1/22/2021
#Purpose: Take in arguments from an HTTP request for site_id , device_id, and uid and run sql queries to delete the device from the site as well as delete the data from the device that it has stored.
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/removeDeviceFromSite?<arguments>
#input: site_id, device_name, uid
#output: returns status code 500 if server cannot create new site or 200 on success
import sqlalchemy
import pymysql
import firebase_admin
from firebase_admin import auth
default_app = firebase_admin.initialize_app()
def removeDeviceFromSite(request):
   res_headers = {
      'Access-Control-Allow-Origin': 'https://storage.googleapis.com',
      'Access-Control-Allow-Headers': 'Authorization'
   }
   #get arguments to http request
   req_headers = request.headers
   if req_headers and 'Authorization' in req_headers:
         id_token = req_headers['Authorization']
   else:
      return ("No Authorization Header", 400, res_headers);
   PREFIX = 'Bearer '
   id_token = id_token[len(PREFIX):]
   try:
      decoded_token = auth.verify_id_token(id_token)
      uid = decoded_token['uid']
   except Exception as e:
      return ("Error: {}".format(e), 500, res_headers)

   request_args = request.args
   if request_args and 'site_id' in request_args:
      site_id = request_args['site_id']
   if request_args and 'device_id' in request_args:
      device_id = request_args['device_id']




   #connect to the site-user_management database
   db_user = "root"
   db_pass = "FbtNb8rkjArEwApg"
   db_name = "site-user_management"
   db_socket_dir = "/cloudsql"
   cloud_sql_connection_name = "silo-systems-292622:us-west1:test-instance"
   #connect to the site-user_management database
   pool = sqlalchemy.create_engine(
      # Equivalent URL:
      #mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=<socket_path>/<cloud_sql_instance_name>
      #        sqlalchemy.engine.url.URL(
      drivername="mysql+pymysql",
      username=db_user,  # e.g. "my-database-user"
      password=db_pass,  # e.g. "my-database-password"
      database=db_name,  # e.g. "my-database-name"
      query={
         "unix_socket": "{}/{}".format(
             db_socket_dir,  # e.g. "/cloudsql"
             cloud_sql_connection_name)  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
      }
   )
   connSiteUserManagement = pool.connect()
   #execute sql statements
   #get site's db name & make sure the user is listed as an owner
   result = connSiteUserManagement.execute(sqlalchemy.text("SELECT db_name FROM site INNER JOIN site_user_role ON site.site_id = site_user_role.site_id where site_user_role.uid = '{}' AND site_user_role.site_id = {} AND site_user_role.role_id = 0;".format(uid, site_id)))
   if int(result.rowcount) == 0:
      return('Error: Site does not exist or user does not have ownership permissions', 500, res_headers)
   r = result.fetchone()
   db_name = str(r[0])
   #connect to site's database
   db_user = "root"
   db_pass = "FbtNb8rkjArEwApg"
   db_name = "{}{}".format(db_name)
   db_socket_dir = "/cloudsql"
   cloud_sql_connection_name = "silo-systems-292622:us-west1:test-instance"

   #connect to the site database
   pool = sqlalchemy.create_engine(
      # Equivalent URL:
      #mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=<socket_path>/<cloud_sql_instance_name>
      sqlalchemy.engine.url.URL(
      drivername="mysql+pymysql",
      username=db_user,  # e.g. "my-database-user"
      password=db_pass,  # e.g. "my-database-password"
      database=db_name,  # e.g. "my-database-name"
      query={
         "unix_socket": "{}/{}".format(
             db_socket_dir,  # e.g. "/cloudsql"
             cloud_sql_connection_name)  # i.e "<PROJECT-NAME>:<INSTANCE-REGION>:<INSTANCE-NAME>"
      })
   )
   #delete device
   connSiteDB = pool.connect()
   #delete device data
   results = connSiteDB.execute(sqlalchemy.text("SELECT parameter_name FROM device_parameter INNER JOIN parameters ON device_parameter.parameter_id = parameters.parameter_id WHERE device_parameter.device_id = {};".format(device_id)))
   for r in results:
      connSiteDB.execute(sqlalchemy.text("delete from {} where device_id = {};".format(str(r[0]), device_id)))
   connSiteDB.execute(sqlalchemy.text("delete from devices where device_id = {};".format(device_id) ))
   connSiteDB.execute(sqlalchemy.text("delete from device_parameter where device_id = {};".format(device_id)))
   return ('', 200, res_headers)
    