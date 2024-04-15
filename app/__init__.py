import os
from dotenv import load_dotenv

from flask import Flask 

load_dotenv()

def create_app(): 
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", default=False)

    from . import database as db

    db.init_db()
    db_conn = db.get_connection()

    @app.route('/')
    def index():
        return 'Hello, world!'

    from . import auth
    from . import chat_agent 

    app.register_blueprint(auth.bp)
    app.register_blueprint(chat_agent.bp)

    return app


