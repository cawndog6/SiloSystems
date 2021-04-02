#Author(s): Connor Williams
#Date: 1/21/2021
#Purpose: Take in arguments from an HTTP request for uid, site_id, and device_name and run sql queries to add the the device to the site's database
#Trigger: dearguments>
#input: site_id, device_id, parameter_name, data_type(optional), parameter_exists(optional)
#input description: data_type is the MySQL datatype that is being recorded. This may be an Integer, varchar(n), etc. This function needs the arguments site_id, device_id, and parameter_name. 
#If the parameter already exists and you're just adding it to another device, set parameter_exists to "true". You can see what parameters already exist by looking at "availableParameters" in the JSON returned from getSiteDeviceInformation.
#if parameter_exists is set to false or the argument isn't present, it will assumed to be false. In that case, the data_type argument is required.
#output: returns status code 500 if server cannot create new site or 200 on success
import sqlalchemy
import pymysql
import firebase_admin
from firebase_admin import auth
default_app = firebase_admin.initialize_app()
def addParameterToDevice(request):
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
      return ('', 400, res_headers)
   if request_args and 'parameter_name' in request_args:
      parameter_name = request_args['parameter_name']
   if request_args and 'parameter_exists' in request_args:
      parameter_exists = request_args['parameter_exists']
      parameter_exists = parameter_exists.lower()
   else:
      parameter_exists = "false"
   if parameter_exists == "false":
      if request_args and 'data_type' in request_args:
         data_type = request_args['data_type']
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
   result = connSiteUserManagement.execute(sqlalchemy.text("""SELECT db_name FROM site_user_role INNER JOIN site ON 
      site_user_role.site_id = site.site_id where site_user_role.uid = '{}' AND site_user_role.site_id = {} 
      AND site_user_role.role_id = 0;""".format(uid, site_id)))
   if int(result.rowcount) == 0:
      print("Error: Site does not exist or user does not have ownership permissions")
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
   connSiteDB = pool.connect()
   #check if parameter already exists for the device its being added to
   results = connSiteDB.execute(sqlalchemy.text("""SELECT * from parameters INNER JOIN device_parameter ON 
      parameters.parameter_id = device_parameter.parameter_id where parameters.parameter_name = '{}' AND 
      device_parameter.device_id = {};""".format(parameter_name, device_id)))
   if int(results.rowcount) != 0:
      return('Error: Parameter already exists for this device', 500, res_headers)
   # Create new table for paramter if it does not already exist
   if parameter_exists == "false":
      results = connSiteDB.execute(sqlalchemy.text("""SELECT * from parameters WHERE parameter_name = '{}' = {};""".format(parameter_name)))
      if int(results.rowcount) == 0:
         connSiteDB.execute(sqlalchemy.text("""CREATE TABLE {}(date_time DATETIME NOT NULL, device_id INT NOT NULL, 
            reading {}, PRIMARY KEY(date_time));""".format(parameter_name, data_type)))
         connSiteDB.execute(sqlalchemy.text("INSERT INTO parameters(parameter_name) VALUES ('{}');".format(parameter_name)))
   results = connSiteDB.execute(sqlalchemy.text("SELECT parameter_id from parameters where parameter_name = '{}';".format(parameter_name)))
   if int(results.rowcount) != 0:
      #add parameter to the device
      r = results.fetchone()
      parameter_id = r[0]
      connSiteDB.execute(sqlalchemy.text("INSERT INTO device_parameter(device_id, parameter_id) VALUES ({},{});".format(device_id, parameter_id)))
   else:
      return ('Could not get parameter_id', 500, res_headers)
   return ('', 200, res_headers)