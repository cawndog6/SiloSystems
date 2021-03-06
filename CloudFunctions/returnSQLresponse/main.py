#Author(s): Connor Williams
#Date: 11/24/2020
#Purpose: Take in arguments from an HTTP request for sensor and deviceId and run a sql query to return information from that sensor + device in JSON format
#Trigger: https://us-west2-silo-systems-292622.cloudfunctions.net/returnSQLresponse?sensor=Temperatures&deviceID=12810
#input: sensor & deviceID
import pymysql
import sqlalchemy
import os
from flask import escape
import firebase_admin
from firebase_admin import auth
default_app = firebase_admin.initialize_app()
def returnSQLresponse(request):

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

    db_user = os.environ.get('db_user')
    db_pass = os.environ.get('db_pass')
    db_name = "site1"
    db_socket_dir = "/cloudsql"
    cloud_sql_connection_name = "silo-systems-292622:us-west1:test-instance"

    #get arguments to http request
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and 'deviceID' in request_json:
        deviceID = request_json['deviceID']
    elif request_args and 'deviceID' in request_args:
        deviceID = request_args['deviceID']
    else:
        deviceID = '-1'

    if request_json and 'sensor' in request_json:
        sensor = request_json['sensor']
    elif request_args and 'sensor' in request_args:
        sensor = request_args['sensor']
    else:
        sensor = -1
    print("deviceID = {}".format(deviceID))
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
        ),
        # ... Specify additional properties here.

    )
    
    #execute sql statement
    with pool.connect() as conn:
        
        results = conn.execute(sqlalchemy.text("SELECT * FROM {} WHERE deviceId = {};".format(sensor, deviceID)));

    #assemble JSON from results to be returned
    numRows = len(results._saved_cursor._result.rows)
    counter = 0
    headerProduced = 0
    if numRows > 0:

        for r in results:
            print("counter = {}".format(counter))
            if headerProduced == 0:
                JSONresults = '{"deviceId":' + str(r[0]) + ',"deviceName":"' + str(r[1]) + '","sensorId":' + str(r[2]) + \
                    ',"sensorName":"' + str(r[3]) + '","data":['
                headerProduced = 1
            if counter < (numRows - 1): 
                JSONresults += '{"date":"' + str(r[4]) + '","value":' + str(r[5]) + '},'
                counter = counter + 1
            else:
                JSONresults += '{"date":"' + str(r[4]) + '","value":' + str(r[5]) + '}'
                counter = counter + 1
        JSONresults += ']}'
        return (JSONresults, 200, res_headers)
    else: 
        return ('', 204, res_headers)
    #return JSONresults;
