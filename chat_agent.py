from flask import Flask, redirect, url_for, session, request, Blueprint
from flask_login import login_required, login_user, current_user, logout_user
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import ChatMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.agents import create_openai_functions_agent
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import tool
from langchain.pydantic_v1 import Field

import json
import os

load_dotenv()

chat = Blueprint('chat', __name__)

# client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

llm = ChatOpenAI(openai_api_key=os.environ.get("OPENAI_API_KEY"), model="gpt-3.5-turbo-0613", temperature=0)

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

        # input_variables=["name", "domain", "scope", "numCQs"],
        # template="Generate a list of competency questions for the ontology in the domain of {{domain}} with a focus on {{scope}}. The ontology should be designed to capture the key concepts and relationships within the domain. Please generate {{numCQs}} competency questions that will help to define the scope and requirements of the ontology. The competency questions should be open-ended and designed to elicit information about the domain and scope. The competency questions should be suitable for use in interviews, surveys, or other data collection methods. The competency questions should be clear, concise, and relevant to the domain and scope. The competency questions should be designed to capture the key concepts and relationships within the domain.",

    return json.dumps(query)

@chat.route('/', methods=['GET'])
def chat_index():
    # user can choose different model? 
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
    data = request.json
    print(data)
    messages[-1]["content"] = data["message"]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are an ontology assistant. Based on the user's input, you will generate a list of competency questions for the ontology in the domain of {{domain}} with a focus on {{scope}} along with the parsed domain, scope, and number of CQs. The ontology should be designed to capture the key concepts and relationships within the domain. Please generate {{numCQs}} competency questions that will help to define the scope and requirements of the ontology. The competency questions should be open-ended and designed to elicit information about the domain and scope. The competency questions should be suitable for use in interviews, surveys, or other data collection methods. The competency questions should be clear, concise, and relevant to the domain and scope. The competency questions should be designed to capture the key concepts and relationships within the domain."),
            ("user", "{input}")
        ]
    )

    chain = prompt | llm  

    competency_questions = chain.invoke({"input": data["message"]})
    # tools = [generate_competency_questions_input]
    # agent = create_openai_functions_agent(llm, tools, prompt)
    # agent_executor = AgentExecutor(agent=agent, verbose=True)
    #
    # competency_questions = agent_executor.invoke({message: data["message"]})

    # assistant = client.chat.completions.create(
    #     model="gpt-3.5-turbo-0613",
    #     messages=messages,
    #     tools=tools,
    #     tool_choice="auto")

    return_value = json.dumps({"input": data["message"], "output": competency_questions.dict()})

    return return_value or "No response from LLM."
    # response_message = assistant.choices[0].message
    # tool_calls = response_message.tool_calls
    # print(tool_calls)
    #
    # if tool_calls:
    #     available_functions = {
    #         "generate_competency_questions": generate_competency_questions
    #     }
    #
    #     messages.append(response_message)
    #     
    #     for tool_call in tool_calls:
    #         function_name = tool_call.function.name
    #         function_to_call = available_functions[function_name]
    #         function_args = json.loads(tool_call.function.arguments)
    #         function_response = function_to_call(**function_args)
    #         messages.append({"tool_call_id": tool_call.id, "role": "system", "name": function_name, "content": function_response})
    #
    #     second_response = client.chat.completions.create(
    #         model="gpt-3.5-turbo-0613",
    #         messages=messages,
    #     )
    #
    # print(second_response)
    # return second_response.choices[0].message.content or "No response from GPT-3" 

