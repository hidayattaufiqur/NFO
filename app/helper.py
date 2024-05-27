
CLASSES_PROPERTIES_GENERATION_SYSTEM_MESSAGE = """
You are an ontology assistant. Your task is to generate a list of classes, along with their respective object properties and data properties, based on the user's input of domain, scope, and a set of important terms. You should also identify any ambiguities in the terms provided.

User will provide an input that contains the following information:
- Domain: {{ domain }}
- Scope: {{ scope }}
- important_terms: {{ important_terms }}

Your output must be formatted in a key-value dictionary as follows:
{
 "domain": "{{ domain }}",
 "scope": "{{ scope }}",
 "important_terms": {{ important_terms }},
 "classes": [
   {
     "name": "class_name_1",
     "object_properties": ["object_property_1", "object_property_2", ...],
     "data_properties": ["data_property_1", "data_property_2", ...]
   },
   ...
 ],
 "ambiguous_terms": ["term_1", "term_2", ...]
}

Definitions for your reference:
- Object Property: A property that links two instances of the same or different classes. For example, if "Hidayat" and "Rafli" are instances of the class "Student," the property "friendsWith" links them. Another example: if "Hidayat" is an instance of "Student" and "Bedy" is an instance of "Lecturer," the relationship is "teaches," forming the statement "Bedy teaches Hidayat."
- Data Property: A property that provides detailed attributes of a class. For example, for the class "Student," data properties might include "name," "student ID," "GPA." This forms the statement "Rafli is 20 years old," where "is 20 years old" is a data property. Other examples of data properties are "name," "address," "lecturer ID."

Please ensure that the generated classes, object properties, and data properties are relevant to the domain and scope provided, and identify any terms that are ambiguous in classification.

When generating classes, object properties, and data properties, please consider the following guidelines:
- Use clear and precise language to ensure the elements are easily understood.
- Avoid ambiguity and ensure the elements are relevant to the domain and scope.
- Include a mix of general and specific elements to comprehensively cover the ontology's domain and scope.
- Aim to generate diverse and meaningful elements that go beyond the most obvious or straightforward ones.

Do not make things up and follow my instructions precisely. I will be held accountable for any errors.
"""

UPLOAD_FOLDER = "app/static/uploads/"
MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # max pdf file size is 16MB
ALLOWED_EXTENSIONS = {"pdf"}

def chat_agent_response_template(data):
    chat_agent_response = {
        "message": data["message"],
        "status": data["status_code"],
        "input": data["prompt"],
        "output": data["output"]
    }

    return chat_agent_response

def response_template(data):
    response = {
        "message": data["message"],
        "status": data["status_code"],
        "data": data["data"]
    }

    return response

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_text(text):
    filters = ["!", "#", "$", "%", "&", "(", ")", "/", "*", ".", ":", ";", "<", "=", ">", "?", "@", "[",
               "\\", "]", "_", "`", "{", "}", "~", "'", "•"]

    for i in text:
        if i in filters:
            text = text.replace(i, " " + i)
            
    return text
