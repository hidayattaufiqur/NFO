from flask import jsonify, request, session
from werkzeug.utils import secure_filename

from app.modules.conversation import get_conversation_detail_by_id
from app.database import *
from app.utils import *
from app.utils.config import TERMS_CLASSES_PROPERTIES_GENERATION_SYSTEM_MESSAGE 
from .model import *
from .utils import *

import logging 
import os
import json
import uuid
import time

logger = logging.getLogger(__name__)

async def get_important_terms_service(conversation_id):
    try:
        db_response = get_important_terms_by_conversation_id(conversation_id)
        if db_response is None: 
            return jsonify(response_template({
                "message": "There is no important terms in conversation with such ID",
                "status_code": 404, 
                "data": None
            })), 404
    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200

async def save_important_terms_service(conversation_id):
    try:
        data = request.json
        terms = data["terms"]
        user_id = session.get('user_id')

        db_response = get_important_terms_by_conversation_id(conversation_id)

        if db_response is None:
            important_terms_id = uuid.uuid4()
            data = create_important_terms(important_terms_id, user_id, conversation_id, terms)
        else:
            important_terms_id = db_response[0].get("important_terms_id")
            data = update_important_terms(important_terms_id, terms)

    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": data
    })), 200


async def generate_important_terms_from_pdf_service():
    start_process_time = time.time()
    filename = ""
    filepath = ""

    try: 
        if "file" not in request.files:
            logger.error("no file is uploaded")
            return jsonify(response_template({
                "message": "no file uploaded",
                "status_code": 400,
                "data": None
            })), 400
        
        data = request.form

        user_id = session.get('user_id')
        conversation_id = data["conversation_id"]

        logger.info(f"conversation_id: {conversation_id}")
        # TODO: need to know whether domain and scope from a saved conversation is prioritized over body request or not
        db_response = get_conversation_detail_by_id(conversation_id)

        logger.info(f"db_response: {db_response}")

        if db_response is None: 
            # domain = data["domain"]
            # scope = data["scope"]
            raise ValueError("No conversation found with such id")
        else: 
            domain = db_response["domain"]
            scope = db_response["scope"]

        file = request.files['file']
        if file.filename == '':
            logger.error("no file selected")
            return jsonify(response_template({
                "message": "No file selected",
                "status_code": 400,
                "data": None
            })), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

        extracted_text = extract_text_from_pdf(filepath)
        if extracted_text is None: 
            logger.error("error extracting text from pdf")
            return jsonify(response_template({
                "message": "Error extracting text from pdf",
                "status_code": 500,
                "data": None
            })), 500
        logger.info(f"extracted text: {extracted_text}")

        logger.info("predicting tags with spacy NER model")
        # predicted_tags = predict_with_flair(extracted_text)
        predicted_tags = predict_with_spacy(extracted_text)
        logger.info(f"predicted tags: {predicted_tags}")

        logger.info("invoking awan llm")
        awan_llm_response = prompt_awan_llm_chunked(predicted_tags, domain, scope)

        if "statusCode" in awan_llm_response:
            logger.error(f"Error invoking awan llm with error: {awan_llm_response['message']}")
            return response_template({
                "message": f"Error invoking awan llm with error: {awan_llm_response['message']}",
                "status_code": awan_llm_response["statusCode"],
                "data": None
            }), 500

        important_terms_id = uuid.uuid4()
        terms = awan_llm_response["choices"][0]["message"]["content"]

        logger.info("saving important terms to database")
        create_important_terms(important_terms_id, user_id, conversation_id, terms)

        prompt = {
            "domain": domain,
            "scope": scope,
            "important_terms": terms
        }

        llm_response = await prompt_chatai(prompt)
        llm_response_json = reformat_response(llm_response)
        save_classes_and_properties_service(llm_response_json, conversation_id)
        end_time = time.time()

    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        }), 500

    logger.info("file uploaded successfully")
    logger.info("deleting file from server")
    os.remove(filepath)

    logger.info(f"Total time: {round(end_time - start_process_time, 2)}s")
    print_time_for_each_process()

    return response_template({
        "message": "File uploaded successfully",
        "status_code": 200,
        "data": {
            "filename": filename,
            "llm_output": llm_response_json
        }
    }), 200

async def generate_important_terms_from_url_service(): 
    start_process_time = time.time()

    try:
        logger.info("extracting url from request body")
        data = request.get_json()

        user_id = session.get('user_id')
        conversation_id = data["conversation_id"]
        url = data["url"]

        # TODO: need to know whether domain and scope from a saved conversation is prioritized over body request or not
        db_response = get_conversation_detail_by_id(conversation_id)

        if db_response is None: 
            # domain = data["domain"]
            # scope = data["scope"]
            raise ValueError("No conversation found with such id")
        else: 
            domain = db_response["domain"]
            scope = db_response["scope"]

        logger.info(f"extracting texts from {url}")

        start_time = time.time()

        logger.info(f"texts have been extracted in {time.time()-start_time:,.2f} ")
        extracted_text = extract_text_from_url(url)

        if extracted_text is None: 
            logger.error("error extracting text from url")
            raise ValueError("Error extracting text from url")
            
        logger.info("predicting tags with spacy NER model")
        # predicted_tags = predict_with_flair(extracted_text)
        predicted_tags = predict_with_spacy(extracted_text)
        logger.info(f"predicted tags: {predicted_tags}")

        logger.info("invoking awan llm")
        awan_llm_response = prompt_awan_llm_chunked(predicted_tags, domain, scope)

        if "statusCode" in awan_llm_response:
            logger.error(f"Error invoking awan llm with error: {awan_llm_response['message']}")
            return response_template({
                "message": f"Error invoking awan llm with error: {awan_llm_response['message']}",
                "status_code": awan_llm_response["statusCode"],
                "data": None
            }), 500

        important_terms_id = uuid.uuid4()
        terms = awan_llm_response["choices"][0]["message"]["content"]

        logger.info("saving important terms to database")
        create_important_terms(important_terms_id, user_id, conversation_id, terms)

        prompt = {
            "domain": domain,
            "scope": scope,
            "important_terms": terms
        }

        llm_response = await prompt_chatai(prompt)
        llm_response_json = reformat_response(llm_response)
        save_classes_and_properties_service(llm_response_json, conversation_id)
        logger.info(f"texts have been extracted in {time.time()-start_time:,.2f} ")

        end_time = time.time()
    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error message: {e}")
        return response_template({
            "message": f"an error occurred at route {request.path} with error message: {e}",
            "status_code": 500,
            "data": None
        }), 500
    
    logger.info(f"Total time: {round(end_time - start_process_time, 2)}s")
    print_time_for_each_process()

    return response_template({
        "message": "Url fetched successfully",
        "status_code": 200,
        "data": {
            "url": url,
            "llm_output": llm_response_json
        }
    }), 200

async def generate_classes_and_properties_service():
    start_process_time = time.time()
    prompt = ""
    try:
        data = request.get_json()
        terms_id = data["important_terms_id"]
        domain = data["domain"]
        scope = data["scope"]
        
        db_response = get_important_terms_by_id(terms_id)
        after_db_fetch_time = time.time()
        if db_response is None: 
            return response_template({
                "message": "There is no important terms with such ID",
                "status_code": 404, 
                "data": None
            }), 404
        prompt = {
            "domain": domain,
            "scope": scope,
            "important_terms": db_response["terms"] 
        }

        x = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["domain", "scope", "important_terms"],
                template=TERMS_CLASSES_PROPERTIES_GENERATION_SYSTEM_MESSAGE,
                template_format="jinja2"
            ),
            verbose=True
        )

        logger.info(f"Invoking prompt to OpenAI")
        response = await x.ainvoke(prompt)
        logger.info(f"ChatOpenAI response {response}")
        response_json = json.loads(response["text"])

        after_prompt_time = time.time()
        
    except Exception as e:
        logger.info(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(
            chat_agent_response_template(
                {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "prompt": prompt, "output": None})
        ), 500

    logger.info(f"Total time: {round(after_prompt_time - start_process_time, 2)}s")
    logger.info(f"DB fetch time: {round(after_db_fetch_time - start_process_time, 2)}s")
    print_time_for_each_process()

    return jsonify(chat_agent_response_template({"message": "Success", "status_code": 200, "prompt": prompt, "output": response_json})) 


async def generate_facets_of_properties_service():
    start_process_time = time.time()
    prompt = ""
    try:
        # Development only, not final implementation. 
        data = request.get_json() 
        properties = data["properties"]
        user_id = session.get('user_id')
        conversation_id = data["conversation_id"]

        # TODO: need to know whether domain and scope from a saved conversation is prioritized over body request or not
        db_response = get_conversation_detail_by_id(conversation_id)

        if db_response is None: 
            # domain = data["domain"]
            # scope = data["scope"]
            raise ValueError("No conversation found with such id")
        else: 
            domain = db_response["domain"]
            scope = db_response["scope"]

        prompt = {
            "domain": domain, 
            "scope": scope,
            "properties": properties,
        }

        llm_response = await prompt_chatai(prompt, input_variables=["domain", "scope", "properties"], template=FACETS_DEFINITION_SYSTEM_MESSAGE)
        llm_response_json = reformat_response(llm_response)
        end_time = time.time()

        # TODO: add global time counter for this function 
        logger.info(f"Total time: {round(end_time - start_process_time, 2)}s")

    except Exception as e:
        logger.info(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(
            chat_agent_response_template(
                {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "prompt": prompt, "output": None})
        ), 500

    return jsonify(chat_agent_response_template({"message": "Success", "status_code": 200, "prompt": prompt, "output": llm_response_json}))


async def generate_instances_of_classes_service():
    start_process_time = time.time()
    prompt = ""
    try:
        data = request.get_json()
        conversation_id = data["conversation_id"]

        db_response = get_conversation_detail_by_id(conversation_id)
        classes = get_all_classes_by_conversation_id(conversation_id)

        if db_response is None: 
            raise ValueError("No conversation found with such id")
        else: 
            domain = db_response["domain"]
            scope = db_response["scope"]

        prompt = {
            "domain": domain, 
            "scope": scope,
            "classes": classes,
        }

        llm_response = await prompt_chatai(prompt, input_variables=["domain", "scope", "classes"], template=INSTANCES_CREATION_SYSTEM_MESSAGE)
        llm_response_json = reformat_response(llm_response)
        save_instances_service(llm_response_json, conversation_id)
        end_time = time.time()

        logger.info(f"Total time: {round(end_time - start_process_time, 2)}s")

    except Exception as e:
        logger.info(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(
            chat_agent_response_template(
                {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "prompt": "", "output": None})
        ), 500

    return jsonify(chat_agent_response_template({"message": "Success", "status_code": 200, "prompt": "", "output": llm_response_json}))


async def get_classes_service(conversation_id):
    try:
        db_response = get_all_classes_by_conversation_id(conversation_id)
        if db_response is None: 
            return jsonify(response_template({
                "message": "There is no classes in conversation with such ID",
                "status_code": 404, 
                "data": None
            })), 404
    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def update_class_service(class_id):
    try:
        data = request.json
        class_name = data["class"]

        logger.info("updating class")   
        db_response = get_class_by_id(class_id)

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no class with such ID",
                "status_code": 404, 
                "data": None
            })), 404
        else:
            class_id = db_response.get("class_id")
            data = update_class(class_id, class_name)

    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": data
    })), 200


async def get_data_properties_service(class_id):
    try:
        db_response = get_all_data_properties_by_class_id(class_id)
        if db_response is None: 
            return jsonify(response_template({
                "message": "There is no data properties in conversation with such ID",
                "status_code": 404, 
                "data": None
            })), 404
    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def update_data_property_service(data_property_id):
    try:
        data = request.json
        data_property_name = data["name"]
        data_property_type = data["data_type"]

        db_response = get_data_property_by_id(data_property_id)

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no data property with such ID",
                "status_code": 404, 
                "data": None
            })), 404
        else:
            data_property_id = db_response.get("data_property_id")
            data = update_data_property(data_property_id, data_property_name, data_property_type)

    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": data
    })), 200


async def get_object_properties_service(class_id):
    try:
        db_response = get_all_object_properties_by_class_id(class_id)
        if db_response is None: 
            return jsonify(response_template({
                "message": "There is no object properties in conversation with such ID",
                "status_code": 404, 
                "data": None
            })), 404
    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def update_object_property_service(object_property_id):
    try:
        data = request.json
        object_property = data["object_property"]

        db_response = get_object_property_by_id(object_property_id)

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no object property with such ID",
                "status_code": 404, 
                "data": None
            })), 404
        else:
            object_property_id = db_response.get("object_property_id")
            data = update_object_property(object_property_id, object_property)

    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": data
    })), 200

async def get_object_property_range_service(object_property_id):
    try:
        db_response = get_all_ranges_by_object_property_id(object_property_id)
        if db_response is None: 
            return jsonify(response_template({
                "message": "There is no object property range with such ID",
                "status_code": 404, 
                "data": None
            })), 404
    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def update_object_property_range_service(range_id):
    try:
        data = request.json
        range_name = data["name"]

        db_response = get_range_by_id(range_id)

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no range with such ID",
                "status_code": 404, 
                "data": None
            })), 404
        else:
            data = update_object_property_range(range_id, range_name)

    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": data
    })), 200


async def get_object_property_domain_service(object_property_id):
    try:
        db_response = get_all_domains_by_object_property_id(object_property_id)
        if db_response is None: 
            return jsonify(response_template({
                "message": "There is no object property domain with such ID",
                "status_code": 404, 
                "data": None
            })), 404
    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def update_object_property_domain_service(domain_id):
    try:
        data = request.json
        domain_name = data["name"]

        db_response = get_domain_by_id(domain_id)

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no domain with such ID",
                "status_code": 404, 
                "data": None
            })), 404
        else:
            data = update_domain(domain_id, domain_name)

    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500, 
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": data
    })), 200


async def get_instances_service(class_id):
    try:
        db_response = get_all_instances_by_class_id(class_id)
        if db_response is None: 
            return jsonify(response_template({
                "message": "There is no instances in conversation with such ID",
                "status_code": 404, 
                "data": None
            })), 404
    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def update_instances_service(instance_id):
    try:
        data = request.json
        instance_name = data["name"]

        db_response = get_instance_by_id(instance_id)

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no instance with such ID",
                "status_code": 404, 
                "data": None
            })), 404
        else:
            instance_id = db_response.get("instance_id")
            data = update_instance(instance_id, instance_name)

    except Exception as e: 
        logger.error(f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": data
    })), 200
