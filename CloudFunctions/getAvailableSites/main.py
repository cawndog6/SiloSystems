#Author(s): Connor Williams
#Date: 1/7/2021
#Purpose: Take in arguments from an HTTP request for uid and run sql query to return sites that the user is a member of and allowed to access
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/getAvailableSites?uid=hdsfjgkhlsdkhfg
#input: nothing except the authentication header that contains the token_id
#output: Returned string will look something like {"result":[{"role_id":0, "site_name": "theSiteName", "site_id":2}]}
import sqlalchemy
import pymysql
import json
import firebase_admin
from firebase_admin import auth
def getAvailableSites(request):
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
      results = conn.execute(sqlalchemy.text("SELECT site.site_id, site.site_name, site_user_role.role_id  FROM site_user_role INNER JOIN site ON site_user_role.site_id = site.site_id WHERE site_user_role.uid = '{}';".format(uid)))
      numRows = int(results.rowcount)
      if numRows < 1:
         return ('No sites are available for this user', 500, {'Access-Control-Allow_Origin':'*'})
      else:
         JSONresults = json.dumps({'result': [dict(row) for row in results]})
         return (JSONresults, 200, res_headers)


