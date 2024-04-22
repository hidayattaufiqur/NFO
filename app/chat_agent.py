from flask import request, Blueprint, jsonify, session
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import  LLMChain
from langchain_postgres import PostgresChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory

from . import database as db
from . import helper

import json
import logging
import uuid

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        db_conn = db.get_connection()

        table_name = "message_store"
        PostgresChatMessageHistory.create_tables(db_conn, table_name)

        if conversation_id is None: 
            conversation_id = uuid.uuid4()
            db_response = db.create_conversation(conversation_id, user_id, "domain", "scope") 
            logger.info(f"db_response: {db_response}")
        else: db_response = None

        if db_response is None: 
            return jsonify(helper.chat_agent_response_template({"message": "Conversation Not Found", "status_code": 404, "prompt": data["prompt"], "output": None})), 404 

        session_id = str(conversation_id)

        logger.info(f"accessing conversation history")
        history = PostgresChatMessageHistory(
            table_name, 
            session_id,
            sync_connection=db_conn,
        )

        logger.info("creating LLMChain")
        x = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["input", "history"], 
                template=system_message
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
            db.update_conversation(response_json["domain"], db_response["id"], response_json["domain"], response_json["scope"], True)

        logger.info("successfully invoked OpenAI prompt and updated the conversation history")

        db.close_connection(db_conn)

    except Exception as e:
        return jsonify(helper.chat_agent_response_template({"message": f"Error: {e}", "status_code": 500, "prompt": data["prompt"], "output": None})), 500

    return jsonify(helper.chat_agent_response_template({"message": "Success", "status_code": 200, "prompt": data["prompt"], "output": response_json})) 

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
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500})), 500

    return jsonify(helper.response_template({"message": "Deleting Has Been Successful", "status_code": 200, "data": None}))

@bp.route('/competency_questions/<conversation_id>', methods=['POST']) 
def save_competency_questions(conversation_id):
    try: 
        data = request.json
        cq_id = uuid.uuid4()
        user_id = session.get('user_id')

        if type(data["competency_question"]) != str: 
            print(len(data["competency_question"]))
            for i in range(len(data["competency_question"])):
                db.create_competency_question(cq_id, user_id, conversation_id, data["competency_question"][i])
        else: db.create_competency_question(cq_id, user_id, conversation_id, data["competency_question"])

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
