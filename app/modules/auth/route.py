from flask import Blueprint, jsonify, request

from .service import *

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    return login_service()


@bp.route('/login/callback')
def callback():
    return callback_service()


@bp.route('/profile')
def profile():
    return profile_service()