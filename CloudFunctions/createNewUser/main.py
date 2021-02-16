#Author(s): Connor Williams
#Date: 2/15/2021
#Purpose: Take in arguments from an HTTP request for site_name and uid and run sql queries to create new user in site-user_management database
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/createNewUser?email=user@xxx.com
#input: email
#output: returns status code 400 if bad request, 500 if user is not authorized or 200 on success
import pymysql
import sqlalchemy
import firebase_admin
from firebase_admin import auth

def createNewUser(request):
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

   db_user = "root"
   db_pass = "FbtNb8rkjArEwApg"
   db_name = "site-user_management"
   db_socket_dir = "/cloudsql"
   cloud_sql_connection_name = "silo-systems-292622:us-west1:test-instance"

   #get arguments to http request
   request_args = request.args
   if request_args and 'email' in request_args:
      email = request_args['email']
   else: 
      return ('', 400, res_headers)
   db_user = "root"
   db_pass = "FbtNb8rkjArEwApg"
   db_name = "site-user_management"
   db_socket_dir = "/cloudsql"
   cloud_sql_connection_name = "silo-systems-292622:us-west1:test-instance"

   #get arguments to http request
   request_args = request.args

   if request_args and 'uid' in request_args:
      uid = request_args['uid']
   else: 
      return ('', 400, res_headers)


      
   #connect to the database
   pool = sqlalchemy.create_engine(
      # Equivalent URL:
      # mysql+pymysql://<db_user>:<db_pass>@/<db_name>?unix_socket=<socket_path>/<cloud_sql_instance_name>
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
    
   #execute sql statements
   with pool.connect() as conn:
       conn.execute(sqlalchemy.text("INSERT INTO user(uid, email) VALUES('{}', '{}');".format(uid, email)))

   return ("", 200, res_headers)