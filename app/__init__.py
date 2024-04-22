from dotenv import load_dotenv
from flask import Flask 

import os
import helper

load_dotenv()

def create_app(): 
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", default=False)
    app.config['UPLOAD_FOLDER'] = helper.UPLOAD_FOLDER

    from . import database as db

    db.init_db()

    @app.route('/')
    def index():
        return 'Hello, world!'

    from . import auth
    from . import chat_agent 

    app.register_blueprint(auth.bp)
    app.register_blueprint(chat_agent.bp)

    return app
