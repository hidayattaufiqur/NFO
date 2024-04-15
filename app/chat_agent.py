from flask import request, Blueprint, jsonify, session
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import  LLMChain
from langchain_community.chat_message_histories import PostgresChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory

from . import database as db
from . import helper

import json
import os
import logging

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

bp = Blueprint('conversation', __name__, url_prefix='/conversation')

llm = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0)

# Define initial system message
system_message = """
You are an ontology assistant. Your task is to generate competency questions for an ontology based on the user's input of domain, scope, and the number of competency questions they want. Your other task is to revise or replace one or more competency questions whenever user prompts it.

User will provide an {input} that contains the following information:
- Domain: The domain of the ontology (e.g., "Renewable Energy")
- Scope: The scope or focus of the ontology (e.g., "Solar Panel Technology")
- num_cqs: The number of competency questions the user wants you to generate (e.g., 5)

Your output must be formatted in a key-pair (dictionary or hashmap) values as follows:
 "competency_questions": enumerated competency questions (e.g. 1. What is the efficiency of solar panel technology in generating renewable energy?, 2. How does the cost of solar panel technology compare to other renewable energy sources?, etc.),
 "domain": domain,
 "num_cqs": num_cqs,
 "scope": scope,

If it's the first prompt from the user (there is nothing yet in conversation history), your output must follow the above format exactly.

If the user provides follow-up prompts (there is at least one conversation history), you should use the {history} as your base knowledge, while still following the above format.

If the user prompts for one or more competency questions to be revised, do not alter the rest of the competency questions, only alter the one(s) that user prompts about.

When generating competency questions, please consider the following guidelines:
- Use clear and concise language to ensure the questions are easily understood.
- Avoid ambiguity and ensure the questions are testable.
- Include a mix of conceptual, application-based, and evaluative questions to assess different aspects of the ontology.
- Aim to generate diverse and creative questions that go beyond the most obvious or straightforward ones.

Do not make things up and follow my instruction obediently. I will be fired by my boss if you do.

Previous conversation history:
{history}
"""

@bp.route('/', methods=['POST'])
@bp.route('/<conversation_id>', methods=['POST'])
async def conversation(conversation_id=None):
    try: 
        data = request.json
        user_id = session.get('user_id')

        # IMPROVE (1): this can and should be reduced to one call to database if conversation_id is being generated as a custom UUID, not automatically by DB. 
        if conversation_id is None: 
            db_response = db.create_conversation(user_id, "domain", "scope") 
            conversation_id = db_response["id"]
        else: 
            db_response = db.get_conversation_detail_by_id(conversation_id) 
            conversation_id = conversation_id

        if db_response is None: 
            return jsonify(helper.bp_agent_response_template({"message": "Conversation Not Found", "status_code": 404, "prompt": data["prompt"], "output": None})), 404 

        history = PostgresChatMessageHistory(
            connection_string=f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@localhost/postgres", # TODO: Add the connection string to the .env file 
            # IMPROVE (1)
            session_id=str(conversation_id), 
        )

        x = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["input", "history"], 
                template=system_message
            ),
            verbose=True,
            memory = ConversationBufferWindowMemory(memory_key="history", return_messages=True, k=10, bp_memory=history)
        )

        response = await x.ainvoke({"input": data["prompt"]})
        response_json = json.loads(response["text"])
        response_json.update({"conversation_id": conversation_id}) 

        # IMPROVE (1)
        # If the conversation is new, we need to update the domain and scope in the database 
        if db_response["domain"] != response_json["domain"] or db_response["scope"] != response_json["scope"]:
            db.update_conversation(db_response["id"], response_json["domain"], response_json["scope"], True)

        history.__del__ # make sure to close the connection to the database

    except Exception as e:
        return jsonify(helper.bp_agent_response_template({"message": f"Error: {e}", "status_code": 500, "prompt": data["prompt"], "output": None})), 500

    return jsonify(helper.bp_agent_response_template({"message": "Success", "status_code": 200, "prompt": data["prompt"], "output": response_json})) 

@bp.route('/<conversation_id>', methods=['GET'])
def get_detail_conversation(conversation_id): 
    try: 
        db_response = db.get_conversation_detail_by_id(conversation_id)

    except Exception as e:
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500, "data": None})), 500

    return jsonify(helper.response_template({"message": "Success", "status_code": 200, "data": db_response}))

@bp.route('/all/<user_id>', methods=['GET'])
def get_all_conversations_by_user_id(user_id): 
    try: 
        db_response = db.get_all_conversations_from_a_user(user_id)

    except Exception as e:
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500, "data": None})), 500

    return jsonify(helper.response_template({"message": "Success", "status_code": 200, "data": db_response}))

@bp.route('/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id): 
    try: 
        history = PostgresbpMessageHistory(
            connection_string=f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@localhost/postgres", # TODO: Add the connection string to the .env file 
            session_id=conversation_id,
        )
        history.clear()
    except Exception as e:
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500})), 500

    return jsonify(helper.response_template({"message": "Deleting Has Been Successful", "status_code": 200, "data": None}))

@bp.route('/competency_questions/<conversation_id>', methods=['POST']) 
def save_competency_questions(conversation_id):
    try: 
        data = request.json
        user_id = session.get('user_id')

        if type(data["competency_question"]) != str: 
            print(len(data["competency_question"]))
            for i in range(len(data["competency_question"])):
                db.create_competency_question(user_id, conversation_id, data["competency_question"][i])
        else: db.create_competency_question(user_id, conversation_id, data["competency_question"])

    except Exception as e:
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500})), 500

    return jsonify(helper.response_template({"message": "Saving Competency Question Has Been Successful", "status_code": 200, "data": None}))

@bp.route('/competency_questions/<conversation_id>', methods=['GET'])
def get_competency_questions(conversation_id):
    try: 
        db_response = db.get_all_competency_questions_by_convo_id(conversation_id)

    except Exception as e:
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500, "data": None})), 500

    return jsonify(helper.response_template({"message": "Success", "status_code": 200, "data": db_response}))

@bp.route('/competency_questions/validate/<cq_id>', methods=['GET'])
def validating_competency_questions(cq_id):
    try: 
       db.validating_competency_question(cq_id, True)

    except Exception as e:
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500})), 500

    return jsonify(helper.response_template({"message": "Updating Competency Question Has Been Successful", "status_code": 200, "data": None}))
