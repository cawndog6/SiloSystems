#Author(s): Connor Williams
#Date: 1/3/2021
#Purpose: Take in arguments from an HTTP request for site_name and uid and run sql queries to add the site to the user/site management database. Also adds the users uid to the site_user_role table as the site owner
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/returnSQLresponse?sensor=Temperatures&deviceID=12810
#input: site_name and uid
import pymysql
import sqlalchemy

from flask import escape

def createNewSite(request):

    db_user = "root"
    db_pass = "FbtNb8rkjArEwApg"
    db_name = "site-user-management"
    db_socket_dir = "/cloudsql"
    cloud_sql_connection_name = "silo-systems-292622:us-west1:test-instance"

    #get arguments to http request
    request_args = request.args

    if request_args and 'site_name' in request_args:
        site_name = request_args['site_name']
    else: 
        return ('', 400, {'Access-Control-Allow-Origin':'*'})
    if request_args and 'uid' in request_args:
        uid = request_args['uid']
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
        #Add new site in database
        conn.execute(sqlalchemy.text("INSERT INTO site(site_name) VALUES ('{}');".format(site_name)))
        r = conn.execute(sqlalchemy.text("SELECT site_id FROM site WHERE site_name = {}".format(site_name)))
        site_id = str(r[0])
        
        #add user to site_user_role as the site owner
        role_id = 0
        conn.execute(sqlalchemy.text("INSERT INTO site_user_role VALUES ({}, {}, {});".format(site_id, uid, role_id)))
    return ('success', 200, {Access-Control-Allow-Origin':'*'})

