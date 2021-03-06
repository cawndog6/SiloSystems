#Author(s): Connor Williams
#Date: 2/16/2021
#Purpose: Take in arguments from an HTTP request for site_id, device_id(optional), parameter_id, and from_date(optional) and returns available data for that sensor.
# if device_id is set, only data that came from the specified device will be returned. If from_date is set, only data recorded from that date->now is returned.
# from_date isn't supported yet.
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/getSensorData?<arguments>
#input: site_id, device_id(optional), parameter_id, from_date(optional)
#output: returns status code 500 if error (and an error message). Returns 200 on success and the json data, which will look like:
# {
#  "device_id":1,
#  "device_name":"Biolab Pi",
#  "parameter_id":1,
#  "parameter_name":"temperature",
#  "data":[
#  {
#     "date_time": "2020-10-10 13:24:04", 
#     "device_id": 1, 
#     "reading": 60
#  }, 
#  {
#     "date_time": "2020-10-10 13:24:05", 
#     "device_id": 1, 
#     "reading": 61
#  }]
# }
import sqlalchemy
import pymysql
import json
import os
import firebase_admin
from firebase_admin import auth
default_app = firebase_admin.initialize_app()
def getSensorData(request):
   res_headers = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Authorization',
   }
   if request.method =='OPTIONS':
      return ("", 204, res_headers)
   #Authenticate user calling the function
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
      return ("Error: {}".format(e), 500, res_headers)
   #get arguments to http request
   request_args = request.args
   if request_args and 'site_id' in request_args:
      site_id = request_args['site_id']
   else: 
      return ('', 400, res_headers)
   if request_args and 'device_id' in request_args:
      device_id = request_args['device_id']
   else: 
      device_id = None
   if request_args and 'parameter_id' in request_args:
      parameter_id = request_args['parameter_id']
   else: 
      return ('', 400, res_headers)
   if request_args and 'from_date' in request_args:
      from_date = request_args['from_date']

   #connect to the site-user_management database
   db_user = os.environ.get('db_user')
   db_pass = os.environ.get('db_pass')
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
   #get site's db name & make sure the user is a member of the site
   result = connSiteUserManagement.execute(sqlalchemy.text("SELECT db_name FROM site_user_role INNER JOIN site ON site_user_role.site_id = site.site_id where site_user_role.uid = '{}' AND site_user_role.site_id = {};".format(uid, site_id)))
   if int(result.rowcount) == 0:
      return('Error: Site does not exist or user does not have permission to view', 500, res_headers)
   r = result.fetchone()
   db_name = str(r[0])
   print("db_name: '{}'".format(db_name))
   #connect to site's database
   db_user = os.environ.get('db_user')
   db_pass = os.environ.get('db_pass')
   db_name = db_name
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
   results = connSiteDB.execute(sqlalchemy.text("SELECT parameter_name FROM parameters where parameter_id = {};".format(parameter_id)))
   if int(result.rowcount) == 0:
      return ('Error: Parameter does not exist.', 500, res_headers)
   r = results.fetchone()
   parameter_name = str(r[0])
   if device_id is not None:
      results = connSiteDB.execute(sqlalchemy.text("SELECT device_name FROM devices where device_id = {};".format(device_id)))
      if int(result.rowcount) == 0:
         return ('Error: Device does not exist.', 500, res_headers)
      r = results.fetchone()
      device_name = str(r[0])
      results = connSiteDB.execute(sqlalchemy.text("SELECT * FROM {} where device_id = {};".format(parameter_name, device_id)))
      JSONresults = {}
      JSONresults['device_id'] = int(device_id)
      JSONresults['device_name'] = device_name
      JSONresults['parameter_id'] = int(parameter_id)
      JSONresults['parameter_name'] = parameter_name
      JSONresults['data'] = [dict(r) for r in results]
      JSONresults = json.dumps(JSONresults, default = str)
      return (JSONresults, 200, res_headers)
   else:
      results = connSiteDB.execute(sqlalchemy.text("SELECT * FROM {} ;".format(parameter_name)))
      JSONresults = {}
      JSONresults['parameter_id'] = int(parameter_id)
      JSONresults['parameter_name'] = parameter_name
      JSONresults['data'] = [dict(r) for r in results]
      JSONresults = json.dumps(JSONresults, default = str)
      return (JSONresults, 200, res_headers)

