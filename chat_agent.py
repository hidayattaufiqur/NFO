from flask import Flask, redirect, url_for, session, request, Blueprint
from flask_login import login_required, login_user, current_user, logout_user
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

chat = Blueprint('chat', __name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@chat.route('/', methods=['GET'])
def chat_index():
    completion = client.chat.completions.create(model="gpt-3.5-turbo-0613",
    messages=[
        {
            "role": "user",
            "content": "When's the next flight from Amsterdam to New York?",
        },
    ])

    output = completion.choices[0].message.content

    return output

