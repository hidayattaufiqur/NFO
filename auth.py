from flask import Flask, redirect, url_for, session, request
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import google.oauth2.id_token
import requests
import os

load_dotenv()

app = Flask(__name__)
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
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    user_info = session.get('user_info')
    if user_info:
        return f"Hello {user_info['name']}, {user_info['email']}!"
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

