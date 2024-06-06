from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from flask import Flask 
from flask_cors import CORS

from . import helper

import os
import logging
logger = logging.getLogger(__name__)

load_dotenv()

def create_app(): 
    logger.info("initializing flask app")
    app = Flask(__name__)

    logger.info("initializing CORS config")
    CORS(
        app,
        origins=os.environ.get('CORS_WHITELIST', '').split(','),
        supports_credentials=True
    )

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", default=False)
    app.config['UPLOAD_FOLDER'] = helper.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = helper.MAX_CONTENT_LENGTH
    app.config['PREFERRED_URL_SCHEME'] = 'https'

    from . import database as db

    db.init_db()

    @app.route('/')
    def index():
        return 'Hello, world!'

    from . import auth
    from . import chat_agent 
    from . import terms_extractor

    app.register_blueprint(auth.bp)
    app.register_blueprint(chat_agent.bp)
    app.register_blueprint(terms_extractor.bp)

    return app
