from functools import wraps
from flask import jsonify
from inspect import iscoroutinefunction

from .auth import is_authorized, refresh_session


def require_authorization(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        auth_response = is_authorized()
        if auth_response:
            return jsonify(auth_response), 401
        refresh_session()

        if iscoroutinefunction(f):
            return await f(*args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated_function
