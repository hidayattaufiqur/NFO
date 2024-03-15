from flask import Flask, jsonify, redirect, url_for, session, request
# from flask_login import LoginManager, current_user
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from chat_agent import chat

import google.oauth2.id_token
import requests
import helper
import database as db
import os
import logging
# TODO: add logging 
# implement logging for debugging and monitoring in python
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger('werkzeug').setLevel(logging.DEBUG)

load_dotenv()

app = Flask(__name__)
app.register_blueprint(chat, url_prefix='/chat')

db.init_db()
db_conn = db.get_connection()

# login_manager = LoginManager(app) # TODO: add login manager user_loader function

app.secret_key = os.environ.get("FLASK_SECRET_KEY", default=False)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # !!! Only for testing, remove for production !!!
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", default=False)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", default=False)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

def create_flow():
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=[
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'openid'
        ],
        redirect_uri=url_for('callback', _external=True)
    )
    return flow

@app.route('/')
def index():
    return 'Hello, world!'

@app.route('/login')
def login():
    flow = create_flow()
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@app.route('/login/callback')
def callback():
    try: 
        flow = create_flow()
        flow.fetch_token(authorization_response=request.url)

        if not session['state'] == request.args['state']:
            abort(500)  

        credentials = flow.credentials
        request_session = requests.session()
        token_request = Request(session=request_session)
        id_info = google.oauth2.id_token.verify_oauth2_token(
            credentials.id_token, token_request, GOOGLE_CLIENT_ID
        )

        session['user_info'] = id_info

        db.create_user(id_info['name'], id_info['email'], id_info['picture'])
    except Exception as e:
        return jsonify(helper.response_template({"message": f"{e}", "status_code": 500, "data": None}))

    return jsonify(helper.response_template({"message": "User logged in successfully", "status_code": 200, "data": { "name": id_info['name'], "profile_pic_url": id_info['picture']}}))
    

@app.route('/profile')
def profile():
    user_info = session.get('user_info')
    # if current_user.is_authenticated: # check if user is authenticated # TODO: use this to check authenticated user instead
    if user_info:
        print(user_info)
        return f"Hello {user_info['name']}, {user_info['email']}, {user_info['picture']}!"
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
