from flask import request, Blueprint, jsonify, session
from dotenv import load_dotenv
from langchain_core import output_parsers
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, BaseChatPromptTemplate, PromptTemplate
from langchain.schema import AIMessage, HumanMessage, BaseOutputParser
from langchain.chains import ConversationChain, LLMChain
from langchain_community.chat_message_histories import PostgresChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory
from langchain.agents import Tool, AgentExecutor, LLMSingleActionAgent, AgentOutputParser, agent
from typing import Dict

import database as db
import helper
import json
import os
import logging

logging.basicConfig(level=logging.DEBUG)

load_dotenv()

chat = Blueprint('conversation', __name__)

llm = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0)

# Define initial system message
system_message = """
You are an ontology assistant. Your task is to generate competency questions for an ontology based on the user's input of domain and scope.

User will provide an {input} that contains domain, scope, and the number of competency questions they want. You should extract those out of the paragraph and then generate n number of competency questions based on the provided information. 

If it's the first prompt from the user (there is nothing yet in conversation history), your output must be formatted in a key-pair (dictionary or hashmap) values as follows:
"competency_questions": enumerated competency questions (e.g. 1. What is the efficiency of solar panel technology in generating renewable energy?, 2. How does the cost of solar panel technology compare to other renewable energy sources?, etc.),
"domain": domain,
"num_cqs": num_cqs,
"scope": scope,

If user gives follow up prompt(s) (there is at least one conversation history), you should answer using conversation history as your knowledge, but still strictly follow above's format. 
Remember, competency_questions must be enumerated!

Previous conversation history:
{history}
"""

@chat.route('/', methods=['POST'])
@chat.route('/<conversation_id>', methods=['POST'])
def conversation(conversation_id=None):
    try: 
        data = request.json
        user_id = session.get('user_id')

        if conversation_id is None: 
            db_response = db.create_conversation(user_id, "domain", "scope") 
        else: 
            db_response = db.get_conversation_by_id(conversation_id) 

        if db_response is None: 
            return jsonify(helper.chat_agent_response_template({"message": "Conversation Not Found", "status_code": 404, "prompt": data["prompt"], "output": None})), 404 

        history = PostgresChatMessageHistory(
            connection_string=f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@localhost/postgres", # TODO: Add the connection string to the .env file 
            session_id=str(db_response["id"]), 
        )

        x = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["input", "history"], 
                template=system_message
            ),
            verbose=True,
            memory = ConversationBufferWindowMemory(memory_key="history", return_messages=True, k=20, chat_memory=history)
        )

        response = x.invoke({"input": data["prompt"]})
        response_json = json.loads(response["text"])
        response_json.update({"conversation_id": db_response["id"]}) 

        # If the conversation is new, we need to update the domain and scope in the database 
        if db_response["domain"] != response_json["domain"] or db_response["scope"] != response_json["scope"]:
            db.update_conversation(db_response["id"], response_json["domain"], response_json["scope"], True) 

    except Exception as e:
        return jsonify(helper.chat_agent_response_template({"message": f"Error: {e}", "status_code": 500, "prompt": data["prompt"], "output": None})), 500

    return jsonify(helper.chat_agent_response_template({"message": "Success", "status_code": 200, "prompt": data["prompt"], "output": response_json})) 

@chat.route('/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id): 
    try: 
        db_response = db.get_conversation_by_id(conversation_id)

        print(f"history =======>> {db_response}")
        # print(f"history type =======>> {type(history)}")

        # db_response.update({"history": history})

    except Exception as e:
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500, "data": None})), 500

    return jsonify(helper.response_template({"message": "Success", "status_code": 200, "data": db_response}))

@chat.route('/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id): 
    try: 
        history = PostgresChatMessageHistory(
            connection_string=f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@localhost/postgres", # TODO: Add the connection string to the .env file 
            session_id=conversation_id,
        )
        history.clear()
    except Exception as e:
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500})), 500

    return jsonify(helper.response_template({"message": "Deleting Has Been Successful", "status_code": 200, "data": None}))

@chat.route('/competency_questions/<conversation_id>', methods=['POST']) 
def save_competency_questions(conversation_id):
    try: 
        data = request.json
        user_id = session.get('user_id')

        if type(data["competency_question"]) != str: 
            for i in range(len(data["competency_question"])):
                db.create_competency_question(user_id, conversation_id, data["competency_question"][i])
        else: db.create_competency_question(user_id, conversation_id, data["competency_question"])

    except Exception as e:
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500})), 500

    return jsonify(helper.response_template({"message": "Saving Competency Question Has Been Successful", "status_code": 200, "data": None}))
