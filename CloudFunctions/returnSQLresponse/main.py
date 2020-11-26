import pymysql
import sqlalchemy

from flask import escape

def returnSQLresponse(request):

    # Remember - Might want to come up with a better solution than storing this password in plain text
    db_user = "root"
    db_pass = "FbtNb8rkjArEwApg"
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
       # results = "hello world";
        results = conn.execute(sqlalchemy.text("SELECT * FROM Temperatures;"));
    numRows = results.rowcount
    res= results.fetchone();
    JSONresults = '{"deviceId":"' + str(res[0].items()) + '","deviceName":"' + str(res[1].items()) + '","sensorId":"' + str(res[2].items()) + \
        '","sensorName":"' + str(res[3]) + '","data":[';
    for r in results:
        JSONresults += '{"date":"' + str(r[4]) + '","value":"' + str(r[5]) + '"},';
    JSONresults += ']}';
    return JSONresults;
    #return numRows;