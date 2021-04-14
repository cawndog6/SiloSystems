#Author(s): Connor Williams
#Date: 2/15/2021
#Purpose: Take in arguments from an HTTP request for uid, site_id, and device_name and delete the user account from the site-user_management database. 
# This function must be called from the user account that is to be deleted.
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/deleteUserAccount?<arguments>
#input: None other than the token_id in the Authorization header
#output: returns status code 400 if bad request, 500 if authorization failed, and 200 on success
import sqlalchemy
import pymysql
import json
import os
import firebase_admin
from firebase_admin import auth
default_app = firebase_admin.initialize_app()
def deleteUserAccount(request):
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
   connSiteUserManagement.execute(sqlalchemy.text("DELETE FROM site_user_role WHERE uid = '{}';".format(uid)))
   connSiteUserManagement.execute(sqlalchemy.text("DELETE FROM user WHERE uid = '{}';".format(uid)))
