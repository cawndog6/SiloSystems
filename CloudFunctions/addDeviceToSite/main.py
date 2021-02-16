#Author(s): Connor Williams
#Date: 1/21/2021
#Purpose: Take in arguments from an HTTP request for uid, site_id, and device_name and run sql queries to add the the device to the site's database
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/addDeviceToSite?<arguments>
#input: site_id, device_name, uid
#output: returns status code 500 if server cannot create new site or 201 on success
import sqlalchemy
import pymysql
import firebase_admin
from firebase_admin import auth
default_app = firebase_admin.initialize_app()
def addDeviceToSite(request):
   res_headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Authorization',
   }
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

   #get arguments to http request
   request_args = request.args
   if request_args and 'site_id' in request_args:
       site_id = request_args['site_id']
   else: 
      return ('', 400, res_headers)
   if request_args and 'device_name' in request_args:
       device_name = request_args['device_name']
   else: 
      return ('', 400, res_headers)


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
   connSiteUserManagement = pool.connect()
   #execute sql statements
   #get site's db name & make sure the user is listed as an owner
   result = connSiteUserManagement.execute(sqlalchemy.text("SELECT db_name FROM site_user_role INNER JOIN site ON site_user_role.site_id = site.site_id where site_user_role.uid = '{}' AND site_user_role.site_id = {} AND site_user_role.role_id = 0;".format(uid, site_id)))
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
         }
      )
   )
   connSiteDB = pool.connect()
   connSiteDB.execute(sqlalchemy.text("INSERT INTO devices(device_name) VALUES ('{}');".format(device_name)))
   return ('', 200, res_headers)
    