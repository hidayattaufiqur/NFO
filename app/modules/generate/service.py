from flask import jsonify, request, session, send_file
from werkzeug.utils import secure_filename

from app.modules.conversation import get_conversation_detail_by_id
from app.database import *
from app.utils import *
from app.utils.config import CLASSES_AND_PROPERTIES_GENERATION_SYSTEM_MESSAGE_BY_IMPORTANT_TERMS 
from .model import *
from .utils import *
from owlready2 import *

import tempfile
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

async def get_classes_and_properties_service(conversation_id):
    try:
        classes = get_all_classes_by_conversation_id(conversation_id)
        response = []

        if classes is None: 
            return jsonify(response_template({
                "message": "There is no conversation with such ID",
                "status_code": 404, 
                "data": None
            })), 404

        for cls in classes:
            class_id = cls.get("class_id")

            data_properties = get_all_data_properties_by_class_id(class_id)
            if data_properties is None:
                return jsonify(response_template({
                    "message": "There is no data properties in conversation with such ID",
                    "status_code": 404, 
                    "data": None
                })), 404

            object_properties = get_all_object_properties_by_class_id(class_id)
            if object_properties is None:
                return jsonify(response_template({
                    "message": "There is no object properties in conversation with such ID",
                    "status_code": 404, 
                    "data": None
                })), 404

            for obj_prop in object_properties:
                object_property_id = obj_prop.get("object_property_id")
                ranges = get_all_ranges_by_object_property_id(object_property_id)
                if ranges is None:
                    return jsonify(response_template({
                        "message": "There is no ranges in conversation with such ID",
                        "status_code": 404, 
                        "data": None
                    })), 404

            response.append({
                "class_id": class_id,
                "class_name": cls.get("name"),
                "data_properties": data_properties,
                "object_properties": object_properties,
            })


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
        "data":  response
    })), 200

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
                template=CLASSES_AND_PROPERTIES_GENERATION_SYSTEM_MESSAGE_BY_IMPORTANT_TERMS,
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


async def create_class_service(conversation_id):
    try:
        data = request.json
        class_names = data["classes"]
        responses = []

        db_response = get_conversation_detail_by_id(conversation_id)

        if db_response is None:
            raise ValueError("No conversation found with such id")
        else:
            domain = db_response["domain"]
            scope = db_response["scope"]

        for class_name in class_names:
            logger.info("creating class")   

            class_id = uuid.uuid4()
            create_class(class_id, conversation_id, class_name, "")

            prompt = {
                "domain": domain,
                "scope": scope,
                "class_name": class_name,
            }

            llm_response = await prompt_chatai(prompt=prompt, input_variables=["domain", "scope", "class_name"], template=PROPERTIES_GENERATION_SYSTEM_MESSAGE_BY_CLASS_NAME)
            llm_response_json = reformat_response(llm_response)
            responses.append(llm_response_json)

            cls = llm_response_json

            for data_prop in cls["data_properties"]:
                data_property_id = uuid.uuid4()
                data_property_name = data_prop["name"]
                data_property_type = data_prop["recommended_data_type"]
                created_data_property = create_data_property(data_property_id, class_id, data_property_name, data_property_type)
                
                if created_data_property:
                    # Create junction between class and data property
                    create_classes_data_junction(class_id, data_property_id)
                
                # Handle object properties
                for obj_prop in cls["object_properties"]:
                    object_property_id = uuid.uuid4()
                    object_property_name = obj_prop["name"]
                    created_obj_property = create_object_property(object_property_id, class_id, object_property_name)
                    
                    if created_obj_property:
                        # Create junction between class and object property
                        create_classes_object_junction(class_id, object_property_id)
                        
                        # Handle domains and ranges
                        for domain_name in obj_prop["recommended_domain"]:
                            domain_id = uuid.uuid4()
                            created_domain = create_domain(domain_id, object_property_id, domain_name)
                            
                            if created_domain:
                                for range_name in obj_prop["recommended_range"]:
                                    range_id = uuid.uuid4()
                                    created_range = create_range(range_id, object_property_id, range_name)
                                    
                                    if created_range:
                                        # Create junction between domain and range
                                        create_domains_ranges_junction(object_property_id, domain_id, range_id)

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
        "data": responses
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


async def create_data_property_service(class_id):
    try:
        data = request.json 

        db_response = get_class_by_id(class_id)
        if db_response is None:
            return jsonify(response_template({
                "message": "There is no class with such ID",
                "status_code": 404, 
                "data": None
            })), 404

        for data in data.get("data_properties"):
            data_property_name = data.get("data_property_name")
            data_property_type = data.get("data_property_type")

            if data.get("data_property_id"): 
                data_property_id = data.get("data_property_id")
                update_data_property(data_property_id, data_property_name, data_property_type) 
                # expected behavior when updating data, the junctions is already existing
            else:
                data_property_id = uuid.uuid4()
                create_data_property(data_property_id, class_id, data_property_name, data_property_type)
                create_classes_data_junction(class_id, data_property_id)

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
        "data": None
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


async def create_object_property_service(class_id):
    try:
        data = request.json

        for data in data.get("object_properties"):
            object_property_name = data.get("object_property_name")

            db_response = get_class_by_id(class_id)
            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no class with such ID",
                    "status_code": 404, 
                    "data": None
                })), 404

            if data.get("object_property_id"): 
                object_property_id = data.get("object_property_id")
                update_object_property(object_property_id, object_property_name)
                # expected behavior when updating object property, the class-object_prop junction is already existing
            else:
                object_property_id = uuid.uuid4()
                create_object_property(object_property_id, class_id, object_property_name)
                create_classes_object_junction(class_id, object_property_id)

            domains = data.get("domains")

            for domain in domains: 
                domain_id = domain.get("domain_id")
                logger.debug(f"domain_id: {domain_id}")
                if domain_id is None:
                    domain_id = uuid.uuid4()
                    create_domain(domain_id, object_property_id, domain.get("domain_name"))
                else:
                    res = get_domain_by_id(domain_id)
                    if res: update_domain(domain_id, domain.get("domain_name"))
                    else: return jsonify(response_template({
                        "message": "There is no domain with such ID",
                        "status_code": 404, 
                        "data": None
                    })), 404

                ranges = domain.get("ranges")

                for rg in ranges: 
                    range_id = rg.get("range_id")

                    if range_id is None:
                        range_id = uuid.uuid4()
                        create_range(range_id, object_property_id, rg.get("range_name"))
                        create_domains_ranges_junction(object_property_id, domain_id, range_id)
                    else:
                        res = get_range_by_id(range_id)
                        # expected behavior when updating range, the domain-range junction is already existing
                        if res: update_range(range_id, rg.get("range_name"))
                        else: return jsonify(response_template({
                            "message": "There is no range with such ID",
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
        "data": None 
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


async def delete_object_property_range_service(object_property_id):
    try:
        data = request.json
        range_ids = data.get("range_ids")

        for rg_id in range_ids:
            db_response = get_range_by_id(rg_id)

            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no range with such ID",
                    "status_code": 404, 
                    "data": None
                })), 404
            else:
                delete_domains_ranges_junction(object_property_id, rg_id)
                delete_range(rg_id)

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
        "data": None 
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


async def create_object_property_domain_range_service(object_property_id):
    try:
        data = request.json

        # expect an array of objects containing domain and array of range objects
        db_response = get_object_property_by_id(object_property_id)

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no object property with such ID",
                "status_code": 404, 
                "data": None
            })), 404

        domains = data.get("domains")

        for domain in domains: 
            new_domain, new_range = False, False # used to check whether to create new junction or update existing one

            domain_id = domain.get("domain_id")
            logger.debug(f"domain_id: {domain_id}")
            if domain_id is None:
                domain_id = uuid.uuid4()
                create_domain(domain_id, object_property_id, domain.get("domain_name"))
                new_domain = True
            else:
                res = get_domain_by_id(domain_id)
                if res: update_domain(domain_id, domain.get("domain_name"))
                else: return jsonify(response_template({
                    "message": "There is no domain with such ID",
                    "status_code": 404, 
                    "data": None
                })), 404

            ranges = domain.get("ranges")

            for rg in ranges: 
                range_id = rg.get("range_id")

                if range_id is None:
                    range_id = uuid.uuid4()
                    create_range(range_id, object_property_id, rg.get("range_name"))
                    new_range = True
                else:
                    res = get_range_by_id(range_id)
                    if res: update_range(range_id, rg.get("range_name"))
                    else: return jsonify(response_template({
                        "message": "There is no range with such ID",
                        "status_code": 404, 
                        "data": None
                    })), 404

                # create junction only if there's a new domain and/or range 
                if new_domain or new_range:
                    create_domains_ranges_junction(object_property_id, domain_id, range_id)


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
        "data": None
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


async def get_instances_service(conversation_id):
    try:
        # db_response = get_all_instances_by_class_id(class_id)
        db_response = get_all_instances_by_conversation_id(conversation_id)
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


async def generate_owl_file_service(conversation_id):
    try:
        # Create a new ontology
        onto = get_ontology(f"https://llm-nfo-frontend.vercel.app/ontology_{conversation_id}.owl")
        with onto:
            classes = get_all_classes_by_conversation_id(conversation_id)
            
            for cls in classes:
                types.new_class(cls["name"], (Thing,))
            
            for cls in classes:
                CurrentClass = onto[cls["name"]]
                
                data_properties = get_all_data_properties_by_class_id(cls["class_id"])
                for dp in data_properties:
                    new_data_property = types.new_class(dp["data_property_name"], (DataProperty,))
                    new_data_property.domain.append(CurrentClass)
                    # TODO: this mapping might need expanding
                    if dp["data_property_type"].lower() == "string":
                        new_data_property.range.append(str)
                    elif dp["data_property_type"].lower() in ["integer", "int"]:
                        new_data_property.range.append(int)

                object_properties = get_all_object_properties_by_class_id(cls["class_id"])
                for op in object_properties:
                    new_object_property = types.new_class(op["object_property_name"], (ObjectProperty,))
                    new_object_property.domain.append(CurrentClass)
                    
                    domains = get_all_domains_by_object_property_id(op["object_property_id"])
                    logger.info(f"domains: {domains}")
                    for d in domains:
                        domain_class = onto[d["domains"][0]["domain_name"]]
                        if domain_class:
                            new_object_property.domain.append(domain_class)
                    
                    ranges = get_all_ranges_by_object_property_id(op["object_property_id"])
                    logger.info(f"ranges: {ranges}")
                    for r in ranges:
                        range_class = onto[r["ranges"][0]["range_name"]]
                        if range_class:
                            new_object_property.range.append(range_class)

                instances = get_all_instances_by_class_id(cls["class_id"])
                for instance in instances:
                    CurrentClass(instance["instance_name"])

        logger.debug(f"Ontology: {onto}")
        # Save the ontology to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".owl") as temp_file:
            onto.save(file=temp_file.name, format="rdfxml")
            temp_file_path = temp_file.name

        # Return the file as an attachment
        return send_file(temp_file_path, as_attachment=True, 
                         download_name=f"ontology_{conversation_id}.owl", 
                         mimetype="application/rdf+xml")

    except Exception as e:
        logger.error(f"An error occurred while generating OWL file: {str(e)}", exc_info=True)
        return jsonify(response_template({
            "message": f"An error occurred while generating OWL file: {str(e)}",
            "status_code": 500,
            "data": None
        })), 500

    finally: 
        os.remove(temp_file_path)


async def get_existing_ontologies_service(conversation_id):
    try:
        data = request.get_json()
        prompt = data.get("prompt")
        db_response = get_conversation_detail_by_id(conversation_id)
        if db_response is None: 
            return jsonify(response_template({
                "message": "There is no conversation with such ID",
                "status_code": 404, 
                "data": None
            })), 404

        prompt = {
            "domain": db_response["domain"],
            "scope": db_response["scope"],
            "prompt": prompt,
        }

        llm_response = await prompt_chatai(prompt, input_variables=["domain", "scope", "prompt"], template=EXISTING_ONTOLOGIES_GENERATION_SYSTEM_MESSAGE)
        llm_response_json = reformat_response_existing_ontology(llm_response)

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
        "data": llm_response_json
    })), 200
