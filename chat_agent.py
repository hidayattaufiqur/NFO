from flask import request, Blueprint, jsonify, session
from dotenv import load_dotenv
from langchain_core import output_parsers
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, BaseChatPromptTemplate, PromptTemplate
from langchain.schema import HumanMessage, BaseOutputParser
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

chat = Blueprint('chat', __name__)

llm = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0)

@chat.route('/2/<session_id>', methods=['DELETE'])
def delete_conversation(session_id): 
    try: 
        history = PostgresChatMessageHistory(
            connection_string=f"postgresql://{os.environ.get('DB_NAME')}:{os.environ.get('DB_PASSWORD')}@localhost/postgres",
            session_id=session_id,
        )
        history.clear()

    except Exception as e:
        return jsonify(helper.response_template({"message": f"Error: {e}", "status_code": 500}))

    return jsonify(helper.response_template({"message": "Deleting Has Been Successful", "status_code": 200, "data": None}))

@chat.route('/2', methods=['POST'])
def chat_post2():
# Define the initial system message
    system_message = """
    You are an ontology assistant. Your task is to generate competency questions for an ontology based on the user's input of domain and scope.

    User will provide an {input} that contains domain, scope, and the number of competency questions they want. You should extract those out of the paragraph and then generate n number of competency questions based on the provided information. 

    If it's the first prompt from the user (there is nothing yet in conversation history), your output must be formatted as follows:
    "input": input_text,
    "competency_questions": enumerated competency questions (e.g. 1. What is the efficiency of solar panel technology in generating renewable energy?, 2. How does the cost of solar panel technology compare to other renewable energy sources?, etc.),
    "domain": domain,
    "num_cqs": num_cqs,
    "scope": scope,

    If user gives follow up prompt(s) (there is at least one conversation history), you should answer using conversation history as your knowledge.
    
   Previous conversation history:
    {history}
    """

    try: 
        data = request.json

        user_id = session.get('user_id')

        db_response = db.create_conversation(user_id, "dummy domain", "dummy scope") 


        history = PostgresChatMessageHistory(
            connection_string=f"postgresql://{os.environ.get('DB_NAME')}:{os.environ.get('DB_PASSWORD')}@localhost/postgres",
            session_id=str(db_response["id"]),
        )

        while True: 
            x = LLMChain(
                llm=llm,
                prompt=PromptTemplate(
                    input_variables=["input", "history"], 
                    template=system_message
                ),
                verbose=True,
                memory = ConversationBufferWindowMemory(memory_key="history", return_messages=True, k=3, chat_memory=history)
            )

            response = x.invoke({"input": data["prompt"]})

            response_json = json.loads(response["text"])

    except Exception as e:
        return jsonify(helper.chat_agent_response_template({"message": f"Error: {e}", "status_code": 500, "prompt": data["prompt"], "map_competency_questions": None}))

    return jsonify(helper.chat_agent_response_template({"message": "Success", "status_code": 200, "prompt": data["prompt"], "map_competency_questions": response_json})) 


@chat.route('/', methods=['POST'])
def chat_post():
    try: 
        data = request.json
        print(data["prompt"])
        # prompt[-1]["content"] = data["prompt"]
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an ontology assistant. Based on the user's input, you will generate a list of competency questions for the ontology in the domain of {{domain}} with a focus on {{scope}} along with the parsed domain, scope, and numCQs. The ontology should be designed to capture the key concepts and relationships within the domain. Please generate {{numCQs}} competency questions that will help to define the scope and requirements of the ontology. The competency questions should be open-ended and designed to elicit information about the domain and scope. The competency questions should be suitable for use in interviews, surveys, or other data collection methods. The competency questions should be clear, concise, and relevant to the domain and scope. The competency questions should be designed to capture the key concepts and relationships within the domain."),
                ("user", "{input}")
            ]
        )

        chain = prompt | llm 
        competency_questions = chain.invoke({"input": data["prompt"]})

        print(f"copmetency_questions: {competency_questions.json}")
        print("=====================================" * 2)

        """ split and map content to extract domain and scope """ 
        split_competency_questions = json.loads(competency_questions.json())["content"].split("\n")
        print(f"splitted copmetency_questions: {split_competency_questions}")
        print("=====================================" * 2)

        # TODO: Add a check to ensure that the competency questions are not empty
        # TODO: Make the parsed contents dynamic through the use of a chat agent
        map_competency_questions = {
            "domain": split_competency_questions[0].split(": ")[1],
            "scope": split_competency_questions[1].split(": ")[1],
            "numCQs": split_competency_questions[2].split(": ")[1],
            "CQs": split_competency_questions[3:]
        }
        print(map_competency_questions)
    except Exception as e:
        return jsonify(helper.chat_agent_response_template({"message": f"Error: {e}", "status_code": 500, "prompt": data["prompt"], "map_competency_questions": None}))

    return jsonify(helper.chat_agent_response_template({"message": "Success", "status_code": 200, "prompt": data["prompt"], "map_competency_questions": map_competency_questions})) 

