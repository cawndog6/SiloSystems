import requests 
import os
import json
import firebase_admin
from firebase_admin import auth
default_app = firebase_admin.initialize_app()
def handleEmailTrigger(request):
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
    if request_args and 'device_name' in request_args:
        device_name = request_args['device_name']
    else:
        return ('', 400, res_headers)
    if request_args and 'current_reading' in request_args:
        current_reading = request_args['current_reading']
    else:
        return ('', 400, res_headers)
    trigger = request.json
    API_KEY = os.environ.get('SENDGRID_API_KEY')

    url = "https://api.sendgrid.com/v3/mail/send"
    reqHeader = {}
    reqHeader['Authorization'] = "Bearer {}".format(API_KEY)
    reqHeader['Content-Type'] = "application/json"
    emailData = {
        "personalizations": [
            {
                "to": [
                    {"email": "{}".format(trigger['action'])}
                ],
                "subject": "Lab Companion Trigger Event: {}".format(trigger['trigger_name']),
            }
        ],
        "from": {"email": "silosystemsuidaho@gmail.com", "name": "Lab Companion Trigger"},
        "mail_settings": {"sandbox_mode": {"enable": False}},
        "reply_to": {"email": "silosystemsuidaho@gmail.com", "name": "Lab Companion Trigger"},
        "subject": "Lab Companion Trigger Event: {}".format(trigger['trigger_name']),
        "tracking_settings": {
            "click_tracking": {"enable": True, "enable_text": True},
            "open_tracking": {"enable": True},
        },
        "content": [{"type": "text/plain", "value": "Trigger [{}] has occured on device [{}]. Current reading is {}.".format(trigger['trigger_name'], device_name, current_reading)}],
    }
    emailData = json.dumps(emailData)
    requests.post(url, data=emailData, headers=reqHeader)
    