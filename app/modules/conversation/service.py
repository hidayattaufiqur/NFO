from langchain_postgres import PostgresChatMessageHistory

from flask import request, jsonify, session
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_postgres import PostgresChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory

from app.utils import response_template, chat_agent_response_template
from app.database import get_connection, get_chat_message_history_connection
from app.cache import get_cache
from app.utils import *
from .model import *

import json
import logging
import uuid

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
cache = get_cache()

load_dotenv()

llm = ChatOpenAI(model="gpt-4o", temperature=0)


async def conversation_service(conversation_id):
    try:
        if request.is_json:
            data = request.get_json()
        else:
            return jsonify(response_template({
                "message": "Invalid data type, expecting application/json.",
                "status_code": 415,
                "data": None
            })), 415

        user_id = session.get('user_id')
        db_conn = get_connection()

        if conversation_id is None:
            conversation_id = uuid.uuid4()
            db_response = create_conversation(
                conversation_id, user_id, "domain", "scope")
        else:
            db_response = get_conversation_detail_by_id(conversation_id)

        if db_response is None:
            return jsonify(chat_agent_response_template(
                {"message": "Conversation Not Found", "status_code": 404, "prompt": data["prompt"], "output": None})), 404

        table_name = "message_store"
        session_id = str(conversation_id)

        logger.info(f"accessing conversation history")
        history = get_chat_message_history_connection(
            table_name, session_id)

        logger.info("creating LLMChain")
        x = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=[
                    "input",
                    "history"],
                template=SYSTEM_MESSAGE),
            verbose=True,
            memory=ConversationBufferWindowMemory(
                memory_key="history",
                return_messages=True,
                k=10,
                chat_memory=history))

        logger.info(f"invoking prompt to OpenAI")
        response = await x.ainvoke({"input": data["prompt"]})
        logger.info(f"response: {response['text']}")
        response_json = json.loads(response["text"])
        response_json.update({"conversation_id": conversation_id})

        # If the conversation is new, we need to update the domain and scope in
        # the database
        if db_response["domain"] != response_json["domain"] or db_response["scope"] != response_json["scope"]:
            update_conversation(
                "" if response_json["scope"] is None else response_json["scope"],
                conversation_id,
                response_json["domain"],
                response_json["scope"],
                True)

        logger.info(
            "successfully invoked OpenAI prompt and updated the conversation history")
        logger.info("closing ChatMessageHistory db connection")

        db_conn.close()

    except Exception as e:
        logger.info(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(chat_agent_response_template(
            {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "prompt": None, "output": None})), 500

    cache.delete(f"conversation_detail_{conversation_id}")
    cache.delete(f"conversations_by_user_{user_id}")

    return jsonify(
        chat_agent_response_template(
            {
                "message": "Success",
                "status_code": 200,
                "prompt": data["prompt"],
                "output": response_json}))


def get_detail_conversation_service(conversation_id):
    try:
        cached_result = cache.get(f"conversation_detail_{conversation_id}")
        if cached_result:
            db_response = cached_result

            conversation_id = db_response["conversation_id"]
            domain = db_response["domain"]
            scope = db_response["scope"]
            is_active = db_response["is_active"]

            if not isinstance(db_response["messages"][0], dict):
                prompt = json.loads(db_response["messages"][0])["data"]["content"]
                competency_questions = json.loads(db_response["messages"][1])[
                    "data"]["content"]
            else:
                prompt = db_response["messages"][0]["data"]["content"]
                competency_questions = db_response["messages"][1]["data"]["content"]


            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": {
                    "conversation_id": conversation_id,
                    "prompt": prompt,
                    "domain": "" if domain is None else domain,
                    "scope": "" if scope is None else scope,
                    "is_active": is_active,
                    "competency_questions": competency_questions
                }
            })), 200

        db_response = get_conversation_detail_by_id(conversation_id)

        if db_response is None:
            logger.info(
                f"an error occurred at route {request.path}: conversation not found")
            return jsonify(response_template(
                {"message": f"an error occurred at route {request.path}: conversation not found", "status_code": 404, "data": None})), 404

        conversation_id = db_response["conversation_id"]
        domain = db_response["domain"]
        scope = db_response["scope"]
        is_active = db_response["is_active"]

        if not isinstance(db_response["messages"][0], dict):
            prompt = json.loads(db_response["messages"][0])["data"]["content"]
            competency_questions = json.loads(db_response["messages"][1])[
                "data"]["content"]
        else:
            prompt = db_response["messages"][0]["data"]["content"]
            competency_questions = db_response["messages"][1]["data"]["content"]

    except Exception as e:
        logger.info(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template(
            {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "data": None})), 500

    cache.set(f"conversation_detail_{conversation_id}", db_response, timeout=300)

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": {
            "conversation_id": conversation_id,
            "prompt": prompt,
            "domain": "" if domain is None else domain,
            "scope": "" if scope is None else scope,
            "is_active": is_active,
            "competency_questions": competency_questions
        }
    })), 200


def get_all_conversations_by_user_id_service(user_id):
    try:
        cached_result = cache.get(f"conversations_by_user_{user_id}")
        if cached_result:
            return jsonify(response_template(
                {"message": "Success", "status_code": 200, "data": cached_result})), 200

        db_response = get_all_conversations_from_a_user(user_id)

    except Exception as e:
        logger.info(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template(
            {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "data": None})), 500

    cache.set(f"conversations_by_user_{user_id}", db_response, timeout=300)

    return jsonify(response_template(
        {"message": "Success", "status_code": 200, "data": db_response})), 200


def delete_conversation_service(conversation_id):
    try:
        db_conn = get_connection()
        table_name = "message_store"
        session_id = conversation_id

        history = PostgresChatMessageHistory(
            table_name,
            session_id,
            sync_connection=db_conn,
        )

        history.clear()
        delete_conversation(conversation_id)
        user_id = session.get('user_id')

    except Exception as e:
        logger.info(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template(
            {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500})), 500

    cache.delete(f"conversation_detail_{conversation_id}")
    cache.delete(f"conversations_by_user_{user_id}")

    return jsonify(response_template(
        {"message": "Deleting Has Been Successful", "status_code": 200, "data": None}))


def save_competency_questions_service(conversation_id):
    try:
        cq_id = uuid.uuid4()
        data = request.json
        user_id = session.get('user_id')
        competency_questions_list = []

        competency_questions_in_db = get_all_competency_questions_by_convo_id(
            conversation_id)

        if competency_questions_in_db is None:
            return jsonify(response_template({
                "message": "There is no competency questions in conversation with such ID",
                "status_code": 404,
                "data": None
            })), 404

        if not isinstance(data["competency_question"], str):
            for i in range(len(data["competency_question"])):
                competency_questions_list.append(
                    data["competency_question"][i])
        else:
            competency_questions_list.append(data["competency_question"])

        if len(competency_questions_in_db) > 0:
            cq_id = competency_questions_in_db[0]["cq_id"]
            update_competency_question(
                cq_id, data["competency_question"])
        else:
            create_competency_question(
                cq_id, user_id, conversation_id, competency_questions_list)


    except Exception as e:
        logger.info(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template(
            {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "data": None})), 500

    cache.delete(f"competency_questions_{conversation_id}")
    return jsonify(
        response_template(
            {
                "message": "Saving Competency Question Has Been Successful",
                "status_code": 200,
                "data": None}))


def get_competency_questions_service(conversation_id):
    try:
        cached_result = cache.get(f"competency_questions_{conversation_id}")

        if cached_result:
            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": cached_result
            })), 200

        db_response = get_all_competency_questions_by_convo_id(
            conversation_id)

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no competency questions in conversation with such ID",
                "status_code": 404,
                "data": None
            })), 404

        if len(db_response) > 0:
            # strip '{}\/' to remove the quotes and forward slashes
            cq_str = db_response[0].get("question").strip("{}")
            cq_str = cq_str.replace('"', '').replace("/", "").replace("\\", "")
            cq_list = cq_str.split(',')

            db_response[0]["question"] = cq_list
        

    except Exception as e:
        logger.info(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template(
            {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "data": None})), 500

    cache.set(f"competency_questions_{conversation_id}", db_response, timeout=300)
    return jsonify(response_template(
        {"message": "Success", "status_code": 200, "data": db_response})), 200


def validating_competency_questions_service(cq_id):
    try:
        validating_competency_question(cq_id, True)

    except Exception as e:
        logger.info(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template(
            {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500})), 500

    cache.delete(f"competency_questions_{cq_id}")
    return jsonify(response_template(
        {"message": "Updating Competency Question Has Been Successful", "status_code": 200, "data": None})), 200
