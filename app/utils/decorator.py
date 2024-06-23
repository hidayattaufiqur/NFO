from functools import wraps
from flask import jsonify

from .auth import is_authorized, refresh_session

def require_authorization(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_response = is_authorized()
        if auth_response:
            return jsonify(auth_response), 401
        refresh_session()
        return f(*args, **kwargs)
    return decorated_function
