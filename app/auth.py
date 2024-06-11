import google.oauth2.id_token
import requests
import os
import logging
import uuid
import re
import datetime

from flask import jsonify, redirect, url_for, session, request, Blueprint
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user, user_needs_refresh
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from . import helper
from . import database as db

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
bp = Blueprint('auth', __name__)
login_manager = LoginManager() 

# os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # !!! Only for testing, remove for production !!!
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", default=False)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", default=False)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

class User(UserMixin):
    def __init__(self, user_id, name, email, profile_pic):
        self.id = user_id
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        user_info = db.get_user_by_id(user_id)
        if user_info:
            return User(user_id=user_info['user_id'], name=user_info['name'], email=user_info['email'], profile_pic=user_info['profile_pic_url'])
        return None

@login_manager.user_loader
def load_user(user_id):
    logger.info("loading user from email")
    user_info = User.get(user_id) 
    if user_info:
        return user_info
    return None

def is_authorized():
    if not current_user.is_authenticated:
        return helper.response_template({"message": f"User is Unauthorized. Please Login", "status_code": 401, "data": None})
    return None

def refresh_session():
    if user_needs_refresh.send(current_user._get_current_object()):
        session.permanent = True
        session.modified = True
        session['_fresh'] = True
        session['_permanent'] = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=30)

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
    try: 
        logger.info("parsing request body")
        data = request.get_json()
        client_id = data.get('client_id')
        access_token = data.get('access_token')

        id_info = google.oauth2.id_token.verify_oauth2_token(
            access_token, requests.Request(), client_id, clock_skew_in_seconds=8
        )

        logger.info("looking up user by email")
        user_info = db.get_user_by_email(id_info['email'])
        if user_info: 
            user_id = user_info['user_id']
        else:
            logger.info("creating a new user in database")
            user_id = uuid.uuid4()
            user_info = db.create_user(user_id, id_info['name'], id_info['email'], id_info['picture']) 

        session['user_info'] = id_info
        session['user_id'] = user_id
        session.permanent = True

        user = User(user_id=user_id, name=id_info['name'], email=id_info['email'], profile_pic=id_info['picture'])
        _ = login_user(user)

        logger.info(f"user: {id_info['name']} logged in successfully")
        # flow = create_flow()
        # authorization_url, state = flow.authorization_url()
        # session['state'] = state 
        # logging.info("redirecting to authorization_url")
        # return redirect(authorization_url)


        return jsonify(helper.response_template({"message": "User logged in successfully", "status_code": 200, "data": { "name": id_info['name'], "profile_pic_url": id_info['picture']}}))

    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} {e}")
        return jsonify(helper.response_template({"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "data": None}))


@bp.route('/login/callback')
def callback():
    try: 
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

        logger.info("looking up user by email")
        user_info = db.get_user_by_email(id_info['email'])
        if user_info: 
            user_id = user_info['user_id']
        else:
            logger.info("creating user in database")
            user_id = uuid.uuid4()
            user_info = db.create_user(user_id, id_info['name'], id_info['email'], id_info['picture']) 

        session['user_info'] = id_info
        session['user_id'] = user_id
        session.permanent = True

        user = User(user_id=user_id, name=id_info['name'], email=id_info['email'], profile_pic=id_info['picture'])
        _ = login_user(user)

        logger.info(f"user: {id_info['name']} logged in successfully")

        return jsonify(helper.response_template({"message": "User logged in successfully", "status_code": 200, "data": { "name": id_info['name'], "profile_pic_url": id_info['picture']}}))
    
    except Exception as e:
        logger.error(f"an error occurred at route {request.path} {e}")
        return jsonify(helper.response_template({"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "data": None}))

    
@bp.route('/profile')
def profile():
    try: 
        auth_response = is_authorized()

        if auth_response: 
            return jsonify(auth_response), 401

        refresh_session()

        user_info = {
            'name': current_user.name,
            'email': current_user.email,
            'profile_pic': current_user.profile_pic
        }

        logger.info("user fetched successfully")
        return jsonify(helper.response_template(({"message": "user profile", "status_code": 200, "data": user_info})))

    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} {e}")
        return jsonify(helper.response_template({"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "data": None}))
