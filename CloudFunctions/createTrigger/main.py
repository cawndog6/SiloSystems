#Author(s): Connor Williams
#Date: 3/28/2021
#Purpose: Take in arguments from an HTTP request for site_id, trigger_name, trigger_type, action, parameter_id, reading_value, and relation_to_reading, and add the trigger to a site. Then call addTriggerToDevice to 
#attach the trigger to a Pi device.
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/createTrigger?<arguments>
#input: site_id, trigger_name, trigger_type, action, parameter_id, reading_value, relation_to_reading, add_to_device, device_id
#output: returns status code 500 if server cannot create new site or 201 on success
import sqlalchemy
import pymysql
from sqlalchemy import sql
import firebase_admin
from firebase_admin import auth
default_app = firebase_admin.initialize_app()
def createTrigger(request):
   res_headers = {
      'Access-Control-Allow-Origin': 'https://storage.googleapis.com',
      'Access-Control-Allow-Headers': 'Authorization'
   }
   if request.method =='OPTIONS':
      return ("", 204, res_headers)
   req_headers = request.headers
   if req_headers and 'Authorization' in req_headers:
         id_token = req_headers['Authorization']
   else:
      return ("No Authorization Header", 400, res_headers)
   PREFIX = 'Bearer '
   id_token = id_token[len(PREFIX):]
   try:
      decoded_token = auth.verify_id_token(id_token)
      uid = decoded_token['uid']
   except Exception as e:
      return ("Error: {}".format(e), 511, res_headers)

   #get arguments to http request
   request_args = request.args
   if request_args and 'site_id' in request_args:
       site_id = request_args['site_id']
   else: 
      return ('', 400, res_headers)
   if request_args and 'trigger_name' in request_args:
       trigger_name = request_args['trigger_name']
   else: 
      return ('', 400, res_headers)
   if request_args and 'trigger_type' in request_args:
      trigger_type = request_args['trigger_type']
   else:
      return ('', 400, res_headers)
   if request_args and 'action' in request_args:
      action = request_args['action']
   else:
      return ('', 400, res_headers) 
   if request_args and 'parameter_id' in request_args:
      parameter_id = request_args['parameter_id']
   else:
      return ('', 400, res_headers)
   if request_args and 'reading_value' in request_args:
      reading_value = request_args['reading_value']
   else:
      return ('', 400, res_headers)
   if request_args and 'relation_to_reading' in request_args:
      relation_to_reading = request_args['relation_to_reading']
   else:
      return ('', 400, res_headers)
   if request_args and 'add_to_device' in request_args:
      add_to_device = request_args['add_to_device']
      if 'device_id' in request_args:
         device_id = request_args
      else:
         return ('', 400, res_headers)
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
   db_name = "{}".format(db_name)
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
   if relation_to_reading == '>' or relation_to_reading == '<' or relation_to_reading == '==' or relation_to_reading == '>=' or relation_to_reading == '<=':
      pass #do nothing
   else:
      return ('Invalid relation to trigger reading', 400, res_headers)


   connSiteDB = pool.connect()
   result = connSiteDB.execute(sqlalchemy.text("INSERT INTO `triggers` (trigger_name, trigger_type, action, parameter_id, reading_value, relation_to_reading) VALUES ('{}', '{}', '{}', {}, {}, '{}');".format(trigger_name, trigger_type, action, int(parameter_id), int(reading_value), relation_to_reading)))
   add_to_device = add_to_device.lower()
   if add_to_device == "true":
      result = connSiteDB.execute(sqlalchemy.text("SELECT trigger_id FROM triggers where trigger_name = '{}'".format(trigger_name)))
      r = result.fetchone()
      trigger_id = r[0]
      connSiteDB.execute(sqlalchemy.text("INSERT INTO device_trigger(device_id, trigger_id) values ({}, {});".format(int(device_id), int(trigger_id))))
   return ('', 200, res_headers)
    