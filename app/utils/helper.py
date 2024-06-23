from .config import ALLOWED_EXTENSIONS

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
