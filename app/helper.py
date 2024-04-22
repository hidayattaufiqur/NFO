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

