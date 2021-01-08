#Author(s): Connor Williams
#Date: 1/3/2021
#Purpose: Take in arguments from an HTTP request for site_name and uid and run sql queries to add the site to the user/site management database. Also adds the users uid to the site_user_role table as the site owner
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/returnSQLresponse?sensor=Temperatures&deviceID=12810
#input: site_name and uid
import pymysql
import sqlalchemy


def addUserToSite(request):

   db_user = "root"
   db_pass = "FbtNb8rkjArEwApg"
   db_name = "site-user-management"
   db_socket_dir = "/cloudsql"
   cloud_sql_connection_name = "silo-systems-292622:us-west1:test-instance"

   #get arguments to http request
   request_args = request.args

   if request_args and 'new_user_email' in request_args:
      user_email = request_args['new_user_email']
   else: 
      return ('', 400, {'Access-Control-Allow-Origin':'*'})
   if request_args and 'role_id' in request_args:
      role_id = request_args['role_id']
   else
      return ('', 400, {'Access-Control-Allow-Origin':'*'})
   if request_args and 'site_name' in request_args:
      site_name = request_args['site_id']
   else
      return ('', 400, {'Access-Control-Allow-Origin':'*'})
   if request_args and 'requestor_uid' in request_args:
      requestor_uid = request_args['requestor_uid']
   else:
      return ('', 400, {Access-Control-Allow_Origin':'*'})

      
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
      result = conn.execute(sqlalchemy.text("SELECT site_id FROM site INNER JOIN site_user_role ON site.site_id = site_user_role.site_id WHERE site_user_role.uid = {} AND site_user_role.role_id = 0 AND  site.site_name = '{}';".format(requestor_uid, site_name)))
      if numRows = len(results._saved_cursor._result.rows) == 0:
         return ('Site does not exist or requestor is not an authorized owner of the site', 403, {Access-Control-Allow_Origin':'*'}) 
      else:
         r = fetchone(result)






   return ('success', 200, {Access-Control-Allow-Origin':'*'})
