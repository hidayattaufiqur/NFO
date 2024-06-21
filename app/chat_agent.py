from flask import request, Blueprint, jsonify, session
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_postgres import PostgresChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory

from . import database as db
from . import helper
from .auth import is_authorized, refresh_session

import json
import logging
import uuid

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

bp = Blueprint('conversation', __name__, url_prefix='/conversation')

llm = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0)

@bp.route('', methods=['POST'])
@bp.route('/<conversation_id>', methods=['POST'])
async def conversation(conversation_id=None):
    try: 
        auth_response = is_authorized()
        if auth_response: 
            return jsonify(auth_response), 401

        refresh_session()

        if request.is_json:
            data = request.get_json()
        else:
            return jsonify(helper.response_template({
                "message": "Invalid data type, expecting application/json.",
                "status_code": 400,
                "data": None
            })), 400

        data = request.get_json()
        user_id = session.get('user_id')
        db_conn = db.get_connection()

        if conversation_id is None: 
            conversation_id = uuid.uuid4()
            db_response = db.create_conversation(conversation_id, user_id, "domain", "scope") 
        else: 
            db_response = db.get_conversation_detail_by_id(conversation_id)

        if db_response is None: 
            return jsonify(helper.chat_agent_response_template({"message": "Conversation Not Found", "status_code": 404, "prompt": data["prompt"], "output": None})), 404 

        table_name = "message_store"
        session_id = str(conversation_id)

        logger.info(f"accessing conversation history")
        history = db.get_chat_message_history_connection(table_name, session_id)

        logger.info("creating LLMChain")
        x = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["input", "history"], 
                template=helper.SYSTEM_MESSAGE
            ),
            verbose=True,
            memory = ConversationBufferWindowMemory(memory_key="history", return_messages=True, k=10, chat_memory=history)
        )

        logger.info(f"invoking prompt to OpenAI")
        response = await x.ainvoke({"input": data["prompt"]})
        response_json = json.loads(response["text"])
        response_json.update({"conversation_id": conversation_id}) 

        # If the conversation is new, we need to update the domain and scope in the database 
        if db_response["domain"] != response_json["domain"] or db_response["scope"] != response_json["scope"]:
            db.update_conversation(response_json["scope"], conversation_id, response_json["domain"], response_json["scope"], True)

        logger.info("successfully invoked OpenAI prompt and updated the conversation history")
        logger.info("closing ChatMessageHistory db connection")

        db_conn.close()

    except Exception as e:
        logger.info(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(helper.chat_agent_response_template({"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "prompt": None, "output": None})), 500

    return jsonify(helper.chat_agent_response_template({"message": "Success", "status_code": 200, "prompt": data["prompt"], "output": response_json})) 


@bp.route('/<conversation_id>', methods=['GET'])
def get_detail_conversation(conversation_id): 
    try: 
        auth_response = is_authorized()
        if auth_response: 
            return jsonify(auth_response), 401

        refresh_session()

        db_response = db.get_conversation_detail_by_id(conversation_id)

        if db_response is None: 
            logger.info(f"an error occurred at route {request.path}")
            return jsonify(helper.response_template({"message": f"an error occurred at route {request.path}", "status_code": 500, "data": None})), 500

        conversation_id = db_response["conversation_id"]
        domain = db_response["domain"]
        scope = db_response["scope"]
        is_active = db_response["is_active"]

        if type(db_response["messages"][0]) != 'dict':
            prompt = json.loads(db_response["messages"][0])["data"]["content"]
            competency_questions = json.loads(db_response["messages"][1])["data"]["content"]
        else:
            prompt = db_response["messages"][0]["data"]["content"]
            competency_questions = db_response["messages"][1]["data"]["content"]

    except Exception as e:
        logger.info(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(helper.response_template({"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "data": None})), 500

    return jsonify(helper.response_template({
        "message": "Success",
        "status_code": 200,
        "data": {
            "conversation_id": conversation_id,
            "prompt": prompt,
            "domain": domain,
            "scope": scope,
            "is_active": is_active,
            "competency_questions": competency_questions
        }
    })), 200


@bp.route('/all/<user_id>', methods=['GET'])
def get_all_conversations_by_user_id(user_id): 
    try: 
        auth_response = is_authorized()
        if auth_response: 
            return jsonify(auth_response), 401

        refresh_session()

        db_response = db.get_all_conversations_from_a_user(user_id)

    except Exception as e:
        logger.info(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(helper.response_template({"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "data": None})), 500

    return jsonify(helper.response_template({"message": "Success", "status_code": 200, "data": db_response})), 200


@bp.route('/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id): 
    try: 
        auth_response = is_authorized()
        if auth_response: 
            return jsonify(auth_response), 401

        refresh_session()

        db_conn = db.get_connection()
        table_name = "message_store"
        session_id = conversation_id

        history = PostgresChatMessageHistory(
            table_name, 
            session_id,
            sync_connection=db_conn,
        )

        history.clear()
        db.delete_conversation(conversation_id)

    except Exception as e:
        logger.info(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(helper.response_template({"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500})), 500

    return jsonify(helper.response_template({"message": "Deleting Has Been Successful", "status_code": 200, "data": None}))


@bp.route('/competency_questions/<conversation_id>', methods=['POST']) 
def save_competency_questions(conversation_id):
    try:
        auth_response = is_authorized()
        if auth_response: 
            return jsonify(auth_response), 401

        refresh_session()

        data = request.json
        cq_id = uuid.uuid4()
        user_id = session.get('user_id')

        if type(data["competency_question"]) != str: 
            print(len(data["competency_question"]))
            for i in range(len(data["competency_question"])):
                db.create_competency_question(cq_id, user_id, conversation_id, data["competency_question"][i])
        else: db.create_competency_question(cq_id, user_id, conversation_id, data["competency_question"])

    except Exception as e:
        logger.info(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(helper.response_template({"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500})), 500

    return jsonify(helper.response_template({"message": "Saving Competency Question Has Been Successful", "status_code": 200, "data": None}))


@bp.route('/competency_questions/<conversation_id>', methods=['GET'])
def get_competency_questions(conversation_id):
    try: 
        auth_response = is_authorized()
        if auth_response: 
            return jsonify(auth_response), 401

        refresh_session()

        db_response = db.get_all_competency_questions_by_convo_id(conversation_id)

    except Exception as e:
        logger.info(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(helper.response_template({"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "data": None})), 500

    return jsonify(helper.response_template({"message": "Success", "status_code": 200, "data": db_response})), 200


@bp.route('/competency_questions/validate/<cq_id>', methods=['GET'])
def validating_competency_questions(cq_id):
    try: 
        auth_response = is_authorized()
        if auth_response: 
            return jsonify(auth_response), 401

        refresh_session()

        db.validating_competency_question(cq_id, True)

    except Exception as e:
        logger.info(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(helper.response_template({"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500})), 500

    return jsonify(helper.response_template({"message": "Updating Competency Question Has Been Successful", "status_code": 200, "data": None})), 200
