from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from datetime import timedelta
from flask_caching import Cache

from .utils import *

import os
import logging

logger = logging.getLogger(__name__)
login_manager = LoginManager()
_ = load_dotenv()


def create_app():
    logger.info("initializing flask app")
    app = Flask(__name__)

    logger.info("initializing CORS config")
    _ = CORS(
        app,
        origins=os.environ.get('CORS_WHITELIST', '').split(','),
        supports_credentials=True
    )

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1,
                            x_proto=1, x_host=1, x_prefix=1)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", default=False)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=3)
    app.config['SESSION_COOKIE_SAMESITE'] = "None"
    app.config['SESSION_COOKIE_SECURE'] = True  # disabled for testing

    # caching 
    app.config['CACHE_TYPE'] = 'RedisCache'
    app.config['CACHE_REDIS_HOST'] = os.environ.get('REDIS_HOST')
    app.config['CACHE_REDIS_PORT'] = os.environ.get('REDIS_PORT')
    app.config['CACHE_REDIS_DB'] = 0              
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300     
        
    from . import database as db
    with app.app_context():
        db.init_db(app)
        
    from . import cache as c
    _ = c.init_cache(app)

    @app.route('/')
    def index():
        return 'Hello, world!'

    from .modules.auth import load_user, bp as auth_bp
    from .modules.conversation import bp as conversation_bp
    from .modules.generate import bp as generate_bp

    login_manager.init_app(app)
    login_manager.user_loader(load_user)

    app.register_blueprint(auth_bp)
    app.register_blueprint(conversation_bp)
    app.register_blueprint(generate_bp)

    return app
