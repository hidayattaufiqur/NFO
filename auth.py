from flask import Flask, redirect, url_for, session
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # You should use a secure, random secret key.

# Google OAuth 2.0 Configuration
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # !!! Only for testing, remove for production !!!
GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your-client-secret"
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Initialize the OAuth flow
flow = Flow.from_client_secrets_file(
    'client_secrets.json',
    scopes=['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email'],
    redirect_uri=url_for('callback', _external=True)
)

@app.route('/')
def index():
    return 'Hello, world!'

@app.route('/login')
def login():
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@app.route('/login/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session['state'] == request.args['state']:
        abort(500)  # State does not match!

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
        return f"Hello {user_info['name']}!"
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

