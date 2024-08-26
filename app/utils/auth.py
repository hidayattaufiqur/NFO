import datetime

from flask import session
from flask_login import current_user, user_needs_refresh

from app.utils import *


def is_authorized():
    if not current_user.is_authenticated:
        return response_template(
            {"message": f"User is Unauthorized. Please Login", "status_code": 401, "data": None})
    return None


def refresh_session():
    if user_needs_refresh.send(current_user._get_current_object()):
        session.permanent = True
        session.modified = True
        session['_fresh'] = True
        session['_permanent'] = datetime.datetime.now(
            datetime.UTC) + datetime.timedelta(minutes=29)
