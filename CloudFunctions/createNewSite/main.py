#Author(s): Connor Williams
#Date: 1/3/2021
#Purpose: Take in arguments from an HTTP request for site_name and uid and run sql queries to add the site to the user/site management database. Also adds the users uid to the site_user_role table as the site owner
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/createNewSite?site_name=myNewSite&uid=abcdabcdjj
#input: site_name and uid
#output: returns status code 500 if server cannot create new site or 201 on success
import pymysql
import sqlalchemy
import os
import firebase_admin
from firebase_admin import auth
default_app = firebase_admin.initialize_app()
def createNewSite(request):
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
      return ("No Authorization Header", 400, res_headers);
   PREFIX = 'Bearer '
   id_token = id_token[len(PREFIX):]
   try:
      decoded_token = auth.verify_id_token(id_token)
      uid = decoded_token['uid']
   except Exception as e:
      return ("Error: {}".format(e), 500, res_headers)
   db_user = os.environ.get('db_user')
   db_pass = os.environ.get('db_pass')
   db_name = "site-user_management"
   db_socket_dir = "/cloudsql"
   cloud_sql_connection_name = "silo-systems-292622:us-west1:test-instance"

   #get arguments to http request
   request_args = request.args
   if request_args and 'site_name' in request_args:
      site_name = request_args['site_name']
   else: 
      return ('', 400, res_headers)


   #connect to the database
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
    
   #execute sql statements
   with pool.connect() as conn:
      #Add new site in database
      #Check if site already exists for the uid (owner)
      result = conn.execute(sqlalchemy.text("SELECT * FROM site INNER JOIN site_user_role on site.site_id = site_user_role.site_id WHERE site.site_name = '{}' AND site_user_role.uid = '{}';".format(site_name, uid)))
      if int(result.rowcount):
         return('Error:Site already exists for this user.', 500, res_headers)
      else:
         #create new entry for site in site table 
         conn.execute(sqlalchemy.text("INSERT INTO site(site_name) VALUES ('{}');".format(site_name)))
         #get the new site's site_id
         result = conn.execute(sqlalchemy.text("SELECT site.site_id FROM site WHERE site.site_name = '{}';".format(site_name)))
         site_id = 0
         greatest_id = 0
         for r in result:
            if int(r[0]) > greatest_id:
               greatest_id = int(r[0])
               site_id = greatest_id
         #insert site's db name in site
         db_name = "{}".format(site_name) + "{}".format(site_id)
         conn.execute(sqlalchemy.text("UPDATE site SET db_name = '{}' where site.site_id = {};".format(db_name, site_id)))
         #add user to site_user_role as the site owner
         role_id = 0
         conn.execute(sqlalchemy.text("INSERT INTO site_user_role VALUES ({}, '{}', {});".format(int(site_id), uid, role_id)))
         conn.execute("CREATE DATABASE {};".format(db_name))
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
   print("about to connect")
   connSiteDB = pool.connect()
   connSiteDB.execute(sqlalchemy.text("CREATE TABLE `devices`(`device_id` INT NOT NULL AUTO_INCREMENT, `device_name` VARCHAR(25) NOT NULL, PRIMARY KEY(`device_id`, `device_name`)) AUTO_INCREMENT=1001;"))
   connSiteDB.execute(sqlalchemy.text("CREATE TABLE `parameters`(`parameter_id` INT NOT NULL AUTO_INCREMENT, `parameter_name` VARCHAR(25) NOT NULL, PRIMARY KEY(`parameter_id`, `parameter_name`)) AUTO_INCREMENT=1001;"))
   connSiteDB.execute(sqlalchemy.text("CREATE TABLE `device_parameter`(`device_id` INT NOT NULL, `device_name` VARCHAR(25) NOT NULL);"))
   connSiteDB.execute(sqlalchemy.text("CREATE TABLE `triggers` (`trigger_id` INT NOT NULL AUTO_INCREMENT,`trigger_name` VARCHAR(25) NOT NULL,`trigger_type` VARCHAR(25) NOT NULL,`action` VARCHAR(45) NULL,`parameter_id` INT NULL,`reading_value` INT NULL,`relation_to_reading` VARCHAR(15) NULL,PRIMARY KEY (`trigger_id`, `trigger_name`));"))
   connSiteDB.execute(sqlalchemy.text("CREATE TABLE `device_trigger`(`trigger_id` INT NOT NULL, `device_id` INT NOT NULL, PRIMARY KEY(`trigger_id`, `device_id`))"))
   return ('', 200, res_headers)
        
