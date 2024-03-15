from flask import Flask, redirect, url_for, session, request, Blueprint, jsonify
from flask_login import login_required, login_user, current_user, logout_user
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import ChatMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.agents import create_openai_functions_agent
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import tool
from langchain.pydantic_v1 import Field

import helper
import json

load_dotenv()

chat = Blueprint('chat', __name__)

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

llm = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0)

tools = [{
    "type": "function",
    "function": {
        "name": "generate_competency_questions",
        "description": "Generate a list of competency questions for ontology development",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "The domain for the ontology, e.g., 'Renewable Energy'"},
                "scope": {"type": "string", "description": "The specific focus within the domain, e.g., 'Impact of Solar Panels on Local Ecosystems'"},
                "numCQs": {"type": "integer", "description": "The number of competency questions to generate"}
            },
        "required": ["domain", "scope", "numCQs"]        
        },
    }
}]

messages = [
    { "role": "system", "content": "You are an ontology assistant. Use the provided functions to generate competency questions (CQs) based on the user's input domain and scope." },
    { "role": "user", "content": 'message'},
]

class generate_competency_questions_input(BaseModel):
    domain: str = Field(description="The domain for the ontology, e.g., 'Renewable Energy'")
    scope: str = Field(description="The specific focus within the domain, e.g., 'Impact of Solar Panels on Local Ecosystems'")
    numCQs: int = Field(description="The number of competency questions to generate")

@tool(args_schema=generate_competency_questions_input)
def generate_competency_questions(query: str): 
    """
    Generate a list of competency questions for ontology development.

    Parameters:
    - domain: The domain for the ontology, e.g., 'Renewable Energy'
    - scope: The specific focus within the domain, e.g., 'Impact of Solar Panels on Local Ecosystems'
    - numCQs: The number of competency questions to generate

    Returns:
    - competency_questions: A list of competency questions for ontology development
    """

    return json.dumps(query)

@chat.route('/', methods=['GET'])
def chat_index():
    # TODO: user can choose different model? 
    assistant = client.chat.completions.create(model="gpt-3.5-turbo-0613",
    messages=[
        {
            "role": "user",
            "content": "When's the next flight from Amsterdam to New York?",
        },
    ])

    output = assistant.choices[0].message.content

    return output

@chat.route('/', methods=['POST'])
def chat_post():
    try: 
        data = request.json
        print(data)
        messages[-1]["content"] = data["prompt"]
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an ontology assistant. Based on the user's input, you will generate a list of competency questions for the ontology in the domain of {{domain}} with a focus on {{scope}} along with the parsed domain, scope, and numCQs. The ontology should be designed to capture the key concepts and relationships within the domain. Please generate {{numCQs}} competency questions that will help to define the scope and requirements of the ontology. The competency questions should be open-ended and designed to elicit information about the domain and scope. The competency questions should be suitable for use in interviews, surveys, or other data collection methods. The competency questions should be clear, concise, and relevant to the domain and scope. The competency questions should be designed to capture the key concepts and relationships within the domain."),
                ("user", "{input}")
            ]
        )

        chain = prompt | llm 
        competency_questions = chain.invoke({"input": data["prompt"]})

        """ split and map content to extract domain and scope """ 
        split_competency_questions = json.loads(competency_questions.json())["content"].split("\n")
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
