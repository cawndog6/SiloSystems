#Author(s): Connor Williams
#Date: 1/7/2021
#Purpose: Take in arguments from an HTTP request for uid and run sql query to return sites that the user is a member of and allowed to access
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/returnSQLresponse?sensor=Temperatures&deviceID=12810
#input: site_name and uid
import pymysql
import sqlalchemy
from flask import jsonify

def getAvailableSites(request):

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
      return ('', 400, {'Access-Control-Allow-Origin':'*'})


      
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
      #check requestor_uid is authenticated as site owner to add new user
      results = conn.execute(sqlalchemy.text("SELECT site_id, role_id FROM site_user_role WHERE site_user_role.uid = {};".format(uid)))
      #numRows = len(results._saved_cursor._result.rows)
      #if numRows < 1:
         #return ('', 404, {'Access-Control-Allow_Origin':'*'})
      #else:
         #JSONresults = jsonify({'result': [dict(row) for row in result]})
      return ("hello", 200, {'Access-Control-Allow-Origin':'*'})


