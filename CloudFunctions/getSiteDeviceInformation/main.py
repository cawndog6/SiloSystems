#Author(s): Connor Williams
#Date: 1/27/2021
#Purpose: Take in arguments from an HTTP request for uid, site_id, and device_name and return the available devices with their parameters in json format
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/getSiteDeviceInformation?<arguments>
#input: site_id
#output: returns status code 500 if the site cant be found or the user does not have authorization for the site. Returns 200 on success and the json data, which will look like:
# {
#  "devices": [
#  {
#     "device_id": 1, 
#     "device_name": "biolabPi", 
#     "parameters": [
#        {
#        "parameter_name": "temperature",
#        "parameter_id": 1
#         }
#      ]
#     "triggers": [
#     {
#        "trigger_name": "tempover90",
#        "trigger_id": 5,
#        "trigger_type": "function",
#        "action": "tempover90",
#        "parameter_id": 60,
#        "reading_value": 90,
#        "relation_to_reading": ">"
#     }]
# }]
#  "availableParameters": [
#    {
#     "parameter_id": 15,
#     "parameter_name": "temperature"
#    }]
#  "availableTriggers": [
#   {
#      "trigger_name": "tempover90",
#      "trigger_id": 5,
#      "trigger_type": "function",
#      "action": "tempover90",
#      "parameter_id": 60,
#      "reading_value": 90,
#      "relation_to_reading": ">"
#  }]
# }
import sqlalchemy
import pymysql
import json
import os
import firebase_admin
from firebase_admin import auth
default_app = firebase_admin.initialize_app()
def getSiteDeviceInformation(request):
   res_headers = {
      'Access-Control-Allow-Origin': 'https://storage.googleapis.com',
      'Access-Control-Allow-Headers': 'Authorization'
   }
   if request.method =='OPTIONS':
      return ("", 204, res_headers)
   #get arguments to http request
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

   request_args = request.args
   if request_args and 'site_id' in request_args:
       site_id = request_args['site_id']
   else: 
      return ('', 400, res_headers)


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
   #get site's db name & make sure the user is listed as an owner
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
   deviceResults = connSiteDB.execute(sqlalchemy.text("SELECT * FROM devices;"))
   #assemble json string
   devices = {'devices': []}
   for d in deviceResults:
      device = dict(d)
      device_id = device['device_id']
      #get available parameters for device
      paramResults = connSiteDB.execute(sqlalchemy.text("""SELECT parameters.parameter_name, parameters.parameter_id  FROM parameters INNER JOIN device_parameter 
      ON device_parameter.parameter_id = parameters.parameter_id WHERE device_parameter.device_id = {};""".format(device_id)))
      triggerResults = connSiteDB.execute(sqlalchemy.text("""SELECT triggers.trigger_name, triggers.trigger_id, triggers.trigger_type, action, parameter_id, reading_value, relation_to_reading FROM triggers INNER JOIN device_trigger ON triggers.trigger_id = device_trigger.trigger_id WHERE device_trigger.device_id = {};""".format(int(device_id))))
      device['parameters'] = [dict(p) for p in paramResults]
      device['triggers'] = [dict(t) for t in triggerResults]
      devices['devices'].append(device)
   availableParameters = connSiteDB.execute(sqlalchemy.text("SELECT parameter_id, parameter_name FROM parameters "))
   devices['availableParameters'] = [dict(p) for p in availableParameters]
   availableTriggers = connSiteDB.execute(sqlalchemy.text("SELECT trigger_name, trigger_id, trigger_type, action, parameter_id, reading_value, relation_to_reading FROM triggers "))
   devices['availableTriggers'] = [dict(t) for t in availableTriggers]
   jsonData = json.dumps(devices)

   return (jsonData, 200, res_headers)
    
