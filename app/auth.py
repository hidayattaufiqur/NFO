import google.oauth2.id_token
import requests
import os
import logging
import uuid
import re

from flask import jsonify, redirect, url_for, session, request, Blueprint
# from flask_login import LoginManager, current_user
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from . import helper
from . import database as db

# TODO: add login manager user_loader function
# TODO: use this to check authenticated user instead

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)

# login_manager = LoginManager(app) 

# os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # !!! Only for testing, remove for production !!!
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", default=False)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", default=False)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

def create_flow():
    logger.info("initializing flow")
    flow = Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=[
            'https://www.googleapis.com/auth/userinfo.profile',
            'openid',
            'https://www.googleapis.com/auth/userinfo.email'
            ],
        redirect_uri=url_for('auth.callback', _external=True)
    )
    return flow

@bp.route('/login')
def login():
    flow = create_flow()
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    logging.info("redirecting to authorization url")
    return redirect(authorization_url)

@bp.route('/login/callback')
def callback():
    try: 
        user_id = uuid.uuid4()
        flow = create_flow()

        # hacky way to replace http to https on redirect
        authorization_response = request.url
        new_authorization_response = re.sub(
            "http:",
            "https:",
            authorization_response
        )
        flow.fetch_token(authorization_response=new_authorization_response)

        if not session['state'] == request.args['state']: abort(500)  

        credentials = flow.credentials
        request_session = requests.session()
        token_request = Request(session=request_session)
        id_info = google.oauth2.id_token.verify_oauth2_token(
            credentials.id_token, token_request, GOOGLE_CLIENT_ID, clock_skew_in_seconds=8
        )

        res = db.create_user(user_id, id_info['name'], id_info['email'], id_info['picture'])
        session['user_info'] = id_info
        session['user_id'] = res['user_id']
        logger.info(f"user: {id_info['name']} logged in successfully")
        return jsonify(helper.response_template({"message": "User logged in successfully", "status_code": 200, "data": { "name": id_info['name'], "profile_pic_url": id_info['picture']}}))
    
    except Exception as e:
        logger.error(f"an error occurred at route {request.path} {e}")
        return jsonify(helper.response_template({"message": f"an error occurred at route {request.path} {e}", "status_code": 500, "data": None}))

    
@bp.route('/profile')
def profile():
    try: 
        user_info = session.get('user_info')
        # if current_user.is_authenticated: # check if user is authenticated 
        if user_info:
            user_id = db.get_user_by_email(user_info['email'])
        else: 
            logger.error("no session id is found")
            return jsonify(helper.response_template(({"message": "no session id is found", "status_code": 400, "data": None})))

        logger.info("user fetched successfully")
        return jsonify(helper.response_template(({"message": "user profile", "status_code": 200, "data": {"user_id": user_id}})))

    except Exception as e: 
        logger.error(f"{e}")
        return jsonify(helper.response_template({"message": "error in retrieving user id", "status_code": 500, "data": None}))
