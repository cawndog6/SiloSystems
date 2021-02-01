#Author(s): Connor Williams
#Date: 1/22/2021
#Purpose: Take in arguments from an HTTP request for delete_user_email, site_name, and requestor_uid and delete the user from the site. 
# This will revoke user privleges to view information about the site
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/addUserToSite?user_email=user@site.com&site_name=mySite&requestor_uid=abcdabcd
#input: site_name and uid
import pymysql
import sqlalchemy import pymysql


def removeUserFromSite(request):

   db_user = "root"
   db_pass = "FbtNb8rkjArEwApg"
   db_name = "site-user-management"
   db_socket_dir = "/cloudsql"
   cloud_sql_connection_name = "silo-systems-292622:us-west1:test-instance"

   #get arguments to http request
   request_args = request.args

   if request_args and 'delete_user_email' in request_args:
      delete_user_email = request_args['delete_user_email']
      delete_user_email.lower()
   else: 
      return ('', 400, {'Access-Control-Allow-Origin':'*'})
   if request_args and 'site_name' in request_args:
      site_id = request_args['site_id']
   else:
      return ('', 400, {'Access-Control-Allow-Origin':'*'})
   if request_args and 'requestor_uid' in request_args:
      requestor_uid = request_args['requestor_uid']
   else:
      return ('', 400, {'Access-Control-Allow_Origin':'*'})
      
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
      result = conn.execute(sqlalchemy.text("SELECT role_id from site_user_role where site_id = {} AND uid ='{}';".format(site_id, requestor_uid)))
      if int(result.rowcount) == 0 :
         return ("Error: Site does not exist for the requested user")
      r = result.fetchone()
      
      if int(r[0]) != 0:
         return ("Error: Requesting user is not the owner of this site")
      else:
         #get uid of user to be added
         result = conn.execute(sqlalchemy.text("SELECT uid FROM user WHERE email = '{}';".format(delete_user_email)))
         r = result.fetchone()
         delete_user_uid = str(r[0])
         #add new user to site
         conn.execute(sqlalchemy.text("DELETE FROM site_user_role WHERE site_id = {} AND delete_user_uid = {};".format(site_id, delete_user_uid)))
         return ('', 200, {'Access-Control-Allow-Origin':'*'})