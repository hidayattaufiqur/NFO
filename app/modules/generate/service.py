from flask import jsonify, request, session, send_file
from werkzeug.utils import secure_filename

from app.modules.conversation import get_conversation_detail_by_id
from app.database import *
from app.logger import get_logger
from app.cache import *
from app.utils import *
from app.utils.config import CLASSES_AND_PROPERTIES_GENERATION_SYSTEM_MESSAGE_BY_IMPORTANT_TERMS
from .model import *
from .utils import *
from owlready2 import *

import tempfile
import os
import json
import uuid
import time
import datetime

logger = get_logger(__name__)
cache = get_cache()

async def get_important_terms_service(conversation_id):
    try:
        cached_result = cache.get(f"important_terms_{conversation_id}")

        if cached_result:
            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": cached_result
            })), 200
        
        db_response = get_important_terms_by_conversation_id(conversation_id)

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no important terms in conversation with such ID",
                "status_code": 404,
                "data": None
            })), 404

        sanitized_terms_list = []

        if len(db_response) > 0:
            terms_str = db_response[0].get("terms").strip('{}')
            terms_list = terms_str.split(",")
            sanitized_terms_list = []

            for term in terms_list:
                sanitized_terms_list.append(term.replace('"', '').replace(' ', '').replace("'", "").replace("\\", "").replace("/", ""))

            db_response[0]["terms"] = sanitized_terms_list

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500
        
    cache.set(f"important_terms_{conversation_id}", db_response, timeout=300)
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def save_important_terms_service(conversation_id):
    try:
        data = request.json
        terms = data["terms"]
        terms = [term.replace(' ', '').replace("'", "").replace('"', "") for term in terms]

        user_id = session.get('user_id')

        db_response = get_important_terms_by_conversation_id(conversation_id)
        logger.info(f"db_response: {db_response}")

        if db_response is None or len(db_response) == 0:
            important_terms_id = uuid.uuid4()
            data = create_important_terms(
                important_terms_id, user_id, conversation_id, terms)
        else:
            important_terms_id = db_response[0].get("important_terms_id")
            data = update_important_terms(important_terms_id, terms)

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.delete(f"important_terms_{conversation_id}")
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None 
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

        if cache.get(f"conversation_detail_{conversation_id}"): db_response = cache.get(f"conversation_detail_{conversation_id}")
        else: db_response = get_conversation_detail_by_id(conversation_id)

        if db_response is None:
            # domain = data["domain"]
            # scope = data["scope"]
            raise ValueError("No conversation found with such id")
        else:
            domain = db_response["domain"]
            scope = db_response["scope"]

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
            if not os.path.exists(filepath):
                file.save(filepath)

        extracted_text = extract_text_from_pdf(filepath)
        if extracted_text is None:
            logger.error("error extracting text from pdf")
            return jsonify(response_template({
                "message": "Error extracting text from pdf",
                "status_code": 500,
                "data": None
            })), 500

        start_time = time.time()
        logger.info("invoking chatai llm")

        prompt = {
            "domain": domain,
            "scope": scope,
            "text": extracted_text,
            # "predicted_tags": predicted_tags,
        }

        # chatai_llm_response = await prompt_chatai(prompt=prompt, template=GENERATE_TERMS_BY_TAGGED_SENTENCES_PROMPT_SYSTEM_MESSAGE, model="llmmini")

        chatai_llm_response = await prompt_chatai(prompt=prompt, template=COMBINED_SYSTEM_MESSAGE, model="llmmini")
        chatai_llm_response_json = loads(chatai_llm_response.get("text"))
        terms = chatai_llm_response_json.get("important_terms")
        logger.info(f"terms have been generated in {time.time()-start_time:,.2f} ")

        important_terms_id = uuid.uuid4()
        # terms = awan_llm_response["choices"][0]["message"]["content"]

        start_time = time.time()
        logger.info("saving important terms to database")
        create_important_terms(
            important_terms_id, user_id, conversation_id, terms)
        logger.info(f"saving important terms has been completed in {time.time()-start_time:,.2f} ")

        # prompt = {
        #     "domain": domain,
        #     "scope": scope,
        #     "important_terms": terms
        # }

        # start_time = time.time()
        # llm_response = await prompt_chatai(prompt=prompt, model="llmmini")
        # logger.info(f"classes and props have been generated in {time.time()-start_time:,.2f} ")
        # llm_response_json = reformat_response(llm_response)

        llm_response_json = reformat_response(chatai_llm_response)
        logger.info(f"llm_response_json: {llm_response_json}")

        start_time = time.time()
        save_classes_and_properties_service(llm_response_json, conversation_id)
        logger.info(f"classes and props have been saved in {time.time()-start_time:,.2f} ")

        end_time = time.time()

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        }), 500

    logger.info("file uploaded successfully")
    logger.info("deleting file from server")
    os.remove(filepath)
    logger.info(f"Total time: {round(end_time - start_process_time, 2)}s")
    # print_time_for_each_process()

    # invalidate cache
    cache.delete(f"classes_and_properties_{conversation_id}") 
    cache.delete(f"important_terms_{conversation_id}") 

    return response_template({
        "message": "File uploaded successfully",
        "status_code": 200,
        "data": {
            "filename": filename,
            "llm_output": llm_response_json,
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

        if cache.get(f"conversation_detail_{conversation_id}"): db_response = cache.get(f"conversation_detail_{conversation_id}")
        else: db_response = get_conversation_detail_by_id(conversation_id)

        if db_response is None:
            # domain = data["domain"]
            # scope = data["scope"]
            raise ValueError("No conversation found with such id")
        else:
            domain = db_response["domain"]
            scope = db_response["scope"]

        logger.info(f"extracting texts from {url}")

        start_time = time.time()

        if cache.get(f"extracted_text_from_url_{url}"):
            extracted_text = cache.get(f"extracted_text_from_url_{url}")
            logger.info(f"texts have been extracted from cache in {time.time()-start_time:,.2f} ")
        else: 
            extracted_text = extract_text_from_url(url)
           
            if extracted_text is None:
                logger.error("error extracting text from url")
                raise ValueError("Error extracting text from url")

            cache.set(f"extracted_text_from_url_{url}", extracted_text, timeout=300)
            logger.info(f"texts have been extracted in {time.time()-start_time:,.2f} ")

        '''
        remove the use of manual NER extraction to improve the performance of the system
        # logger.info("predicting tags with spacy NER model")
        # predicted_tags = predict_with_flair(extracted_text)
        # predicted_tags = predict_with_spacy(extracted_text)
        # logger.info(f"predicted tags: {predicted_tags}")
        # logger.info(f"tags have been predicted in {time.time()-start_time:,.2f} ")
        ''' 

        start_time = time.time()
        logger.info("invoking chatai llm")

        prompt = {
            "domain": domain,
            "scope": scope,
            "text": extracted_text,
            # "predicted_tags": predicted_tags,
        }

        # chatai_llm_response = await prompt_chatai(prompt=prompt, template=GENERATE_TERMS_BY_TAGGED_SENTENCES_PROMPT_SYSTEM_MESSAGE, model="llmmini")

        chatai_llm_response = await prompt_chatai(prompt=prompt, template=COMBINED_SYSTEM_MESSAGE, model="llmmini")
        chatai_llm_response_json = loads(chatai_llm_response.get("text"))
        terms = chatai_llm_response_json.get("important_terms")
        logger.info(f"terms have been generated in {time.time()-start_time:,.2f} ")

        important_terms_id = uuid.uuid4()
        # terms = awan_llm_response["choices"][0]["message"]["content"]

        start_time = time.time()
        logger.info("saving important terms to database")
        create_important_terms(
            important_terms_id, user_id, conversation_id, terms)
        logger.info(f"saving important terms has been completed in {time.time()-start_time:,.2f} ")

        # prompt = {
        #     "domain": domain,
        #     "scope": scope,
        #     "important_terms": terms
        # }

        # start_time = time.time()
        # llm_response = await prompt_chatai(prompt=prompt, model="llmmini")
        # logger.info(f"classes and props have been generated in {time.time()-start_time:,.2f} ")
        # llm_response_json = reformat_response(llm_response)

        llm_response_json = reformat_response(chatai_llm_response)
        logger.info(f"llm_response_json: {llm_response_json}")

        start_time = time.time()
        save_classes_and_properties_service(llm_response_json, conversation_id)
        logger.info(f"classes and props have been saved in {time.time()-start_time:,.2f} ")

        end_time = time.time()

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error message: {e}")

        return response_template({
            "message": f"an error occurred at route {request.path} with error message: {e}",
            "status_code": 500,
            "data": None
        }), 500

    logger.info(f"Total time for processing the URL: {round(end_time - start_process_time, 2)}s")

    # invalidate cache
    cache.delete(f"classes_and_properties_{conversation_id}")
    cache.delete(f"important_terms_{conversation_id}") 

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
        cached_result = cache.get(f"classes_and_properties_{conversation_id}")
        if cached_result:
            logger.info("cache hit!")
            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": cached_result
            })), 200


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

            # for obj_prop in object_properties:
            #     object_property_id = obj_prop.get("object_property_id")
            #     ranges = get_all_ranges_by_object_property_id(
            #         object_property_id)
            #     if ranges is None:
            #         return jsonify(response_template({
            #             "message": "There is no ranges in conversation with such ID",
            #             "status_code": 404,
            #             "data": None
            #         })), 404

            response.append({
                "class_id": class_id,
                "class_name": cls.get("name"),
                "data_properties": data_properties,
                "object_properties": object_properties,
            })


    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500


    cache.set(f"classes_and_properties_{conversation_id}", response, timeout=300)
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": response
    })), 200


async def generate_classes_and_properties_service(conversation_id): # obselete
    start_process_time = time.time()
    prompt = ""
    try:
        data = request.get_json()
        terms_id = data["important_terms_id"]

        db_response = get_conversation_detail_by_id(conversation_id)
        if db_response is None:
            return response_template({
                "message": "There is no conversation with such ID",
                "status_code": 404,
                "data": None
            }), 404

        domain = db_response["domain"]
        scope = db_response["scope"]

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
                input_variables=[
                    "domain",
                    "scope",
                    "important_terms"],
                template=CLASSES_AND_PROPERTIES_GENERATION_SYSTEM_MESSAGE_BY_IMPORTANT_TERMS,
                template_format="jinja2"),
            verbose=True)

        logger.info(f"Invoking prompt to OpenAI")
        response = await x.ainvoke(prompt)
        logger.info(f"ChatOpenAI response {response}")
        response_json = json.loads(response["text"])

        after_prompt_time = time.time()

        # cache.delete(f"classes_and_properties_{conversation_id}") # invalidate cache
        # cache.delete(f"classes_{class_id}") # invalidate cached_result
        # cache.delete(f"owl_file_{conversation_id}") # invalidate cached_result
        # cache.delete(f"object_properties_{class_id}") # invalidate cached_result
        # cache.delete(f"object_property_range_{object_property_id}") # invalidate cached_result
        # cache.delete(f"object_property_domain_{object_property_id}") # invalidate cached_result
        # cache.delete(f"data_properties_{class_id}") # invalidate cached_result

    except Exception as e:
        logger.info(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(
            chat_agent_response_template(
                {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "prompt": prompt, "output": None})
        ), 500

    logger.info(
        f"Total time: {round(after_prompt_time - start_process_time, 2)}s")
    logger.info(
        f"DB fetch time: {round(after_db_fetch_time - start_process_time, 2)}s")
    print_time_for_each_process()

    return jsonify(chat_agent_response_template(
        {"message": "Success", "status_code": 200, "prompt": prompt, "output": response_json}))


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
        logger.info(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(
            chat_agent_response_template(
                {"message": f"an error occurred at route {request.path} with error: {e}", "status_code": 500, "prompt": "", "output": None})
        ), 500

    cache.delete(f"instances_{conversation_id}")
    return jsonify(chat_agent_response_template(
        {"message": "Success", "status_code": 200, "prompt": "", "output": llm_response_json}))


async def get_classes_service(conversation_id):
    try:
        cached_result = cache.get(f"classes_{conversation_id}")

        if cached_result:
            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": cached_result
            })), 200

        db_response = get_all_classes_by_conversation_id(conversation_id)
        if db_response is None:
            return jsonify(response_template({
                "message": "There is no classes in conversation with such ID",
                "status_code": 404,
                "data": None
            })), 404

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.set(f"classes_{conversation_id}", db_response, timeout=300)
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
            return jsonify(response_template({
                "message": "No conversation found with such id",
                "status_code": 404,
                "data": None
            })), 404
        # else:
        #     domain = db_response["domain"]
        #     scope = db_response["scope"]

        for cls in class_names:
            class_name = cls.get("class_name").replace(" ", "")
            logger.info("creating class")
            if cls.get("class_id"):
                class_id = cls.get("class_id")
                db_response = get_class_by_id(class_id)
                if db_response is None:
                    return jsonify(response_template({
                        "message": "There is no class with such ID",
                        "status_code": 404,
                        "data": None
                    })), 404

                update_class(class_id, class_name)
            else:
                class_id = uuid.uuid4()
                create_class(class_id, conversation_id,
                             class_name, "")

            response = {"class_id": class_id,
                        "class_name": cls.get("class_name")}
            responses.append(response)

        cache.delete(f"classes_{conversation_id}")

            # prompt = {
            #     "domain": domain,
            #     "scope": scope,
            #     "class_name": class_name,
            # }
            #
            # llm_response = await prompt_chatai(prompt=prompt, input_variables=["domain", "scope", "class_name"], template=PROPERTIES_GENERATION_SYSTEM_MESSAGE_BY_CLASS_NAME)
            # llm_response_json = reformat_response(llm_response)
            # responses.append(llm_response_json)

            # cls = llm_response_json

            # for data_prop in cls["data_properties"]:
            #     data_property_id = uuid.uuid4()
            #     data_property_name = data_prop["name"]
            #     data_property_type = data_prop["recommended_data_type"]
            #     created_data_property = create_data_property(data_property_id, class_id, data_property_name, data_property_type)
            #
            #     if created_data_property:
            #         # Create junction between class and data property
            #         create_classes_data_junction(class_id, data_property_id)
            #
            #     # Handle object properties
            #     for obj_prop in cls["object_properties"]:
            #         object_property_id = uuid.uuid4()
            #         object_property_name = obj_prop["name"]
            #         created_obj_property = create_object_property(object_property_id, class_id, object_property_name)
            #
            #         if created_obj_property:
            #             # Create junction between class and object property
            #             create_classes_object_junction(class_id, object_property_id)
            #
            #             # Handle domains and ranges
            #             for domain_name in obj_prop["recommended_domain"]:
            #                 domain_id = uuid.uuid4()
            #                 created_domain = create_domain(domain_id, object_property_id, domain_name)
            #
            #                 if created_domain:
            #                     for range_name in obj_prop["recommended_range"]:
            #                         range_id = uuid.uuid4()
            #                         created_range = create_range(range_id, object_property_id, range_name)
            #
            #                         if created_range:
            #                             # Create junction between domain and range
            #                             create_domains_ranges_junction(object_property_id, domain_id, range_id)

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.delete(f"classes_and_properties_{conversation_id}") # invalidate cache
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": responses
    })), 200


async def update_class_service(class_id): # obselete
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

        # cache.delete(f"classes_{conversation_id}")
        # cache.delete(f"classes_and_properties_{conversation_id}")

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
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


async def delete_class_service():
    try:
        data = request.json
        class_ids = data["class_ids"]
        conversation_id = get_class_by_id(class_ids[0])["conversation_id"]

        for class_id in class_ids:
            db_response = get_class_by_id(class_id)
            if db_response is None:  
                return jsonify(response_template({
                    "message": "There is no class with such ID",
                    "status_code": 404,
                    "data": None
                })), 404


            data_properties = get_all_data_properties_by_class_id(class_id)
            if data_properties is not None:
                for dp in data_properties:
                    delete_classes_data_junction(
                        class_id, dp.get("data_property_id"))
                    delete_data_property(dp.get("data_property_id"))

                    cache.delete(f"data_properties_{dp.get('data_property_id')}")

            object_properties = get_all_object_properties_by_class_id(class_id)
            if object_properties is not None:
                for op in object_properties:
                    delete_classes_object_junction(
                        class_id, op.get("object_property_id"))
                    delete_object_property(op.get("object_property_id"))

                    cache.delete(f"object_properties_{op.get('object_property_id')}")

            instances = get_all_instances_by_class_id(class_id)
            if instances is not None:
                for instance in instances:
                    delete_classes_instances_junction(
                        class_id, instance.get("instance_id"))
                    delete_instance(instance.get("instance_id"))

                    cache.delete(f"instances_{instance.get('instance_id')}")

            delete_class(class_id)
            cache.delete(f"classes_{conversation_id}") # invalidate cache

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.delete(f"classes_and_properties_{conversation_id}") # invalidate cache
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None
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
            data_property_type = "" if data.get(
                "data_property_type") is None else data.get("data_property_type")

            if data.get("data_property_id"):
                data_property_id = data.get("data_property_id")
                update_data_property(
                    data_property_id, data_property_name, data_property_type)
                # expected behavior when updating data, the junction is
                # already existing
                cache.delete(f"data_properties_{data_property_id}")
            else:
                data_property_id = uuid.uuid4()
                create_data_property(
                    data_property_id,
                    class_id,
                    data_property_name,
                    data_property_type)
                create_classes_data_junction(class_id, data_property_id)

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.delete(f"classes_and_properties_{db_response['conversation_id']}")
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None
    })), 200


async def get_data_properties_service(class_id):
    try:
        cached_result = cache.get(f"data_properties_{class_id}")

        if cached_result:
            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": cached_result
            })), 200

        db_response = get_all_data_properties_by_class_id(class_id)
        if db_response is None:
            return jsonify(response_template({
                "message": "There is no data properties in conversation with such ID",
                "status_code": 404,
                "data": None
            })), 404

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.set(f"data_properties_{class_id}", db_response, timeout=300)
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def update_data_property_service(data_property_id): # obselete
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
            data = update_data_property(
                data_property_id, data_property_name, data_property_type)

        # cache.delete(f"data_properties_{data_property_id}")
        # cache.delete(f"classes_and_properties_{conversation_id}")

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
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


async def delete_data_properties_service(class_id):
    try:
        data = request.json
        data_properties = data["data_properties_ids"]

        for data_property_id in data_properties:

            db_response = get_class_by_id(class_id)
            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no class with such ID",
                    "status_code": 404,
                    "data": None
                })), 404

            conversation_id = db_response["conversation_id"]

            db_response = get_data_property_by_id(data_property_id)
            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no data property with such ID",
                    "status_code": 404,
                    "data": None
                })), 404

            delete_classes_data_junction(class_id, data_property_id)
            delete_data_property(data_property_id)

            cache.delete(f"data_properties_{data_property_id}")


    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500


    cache.delete(f"classes_and_properties_{conversation_id}")
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None
    })), 200


async def get_object_properties_service(class_id):
    try:
        cached_result = cache.get(f"object_properties_{class_id}")

        if cached_result:
            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": cached_result
            })), 200

        db_response = get_all_object_properties_by_class_id(class_id)
        if db_response is None:
            return jsonify(response_template({
                "message": "There is no object properties in conversation with such ID",
                "status_code": 404,
                "data": None
            })), 404


    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500


    cache.set(f"object_properties_{class_id}", db_response, timeout=300)
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def create_object_property_service(class_id):
    try:
        data = request.json
        conversation_id = ""

        for data in data.get("object_properties"):
            object_property_name = data.get("object_property_name")

            db_response = get_class_by_id(class_id)
            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no class with such ID",
                    "status_code": 404,
                    "data": None
                })), 404

            if conversation_id == "": conversation_id = db_response["conversation_id"]

            if data.get("object_property_id"):
                object_property_id = data.get("object_property_id")
                update_object_property(
                    object_property_id, object_property_name)
                # expected behavior when updating object property, the
                # class-object_prop junction is already existing
                cache.delete(f"object_properties_{object_property_id}")
            else:
                object_property_id = uuid.uuid4()
                create_object_property(
                    object_property_id, class_id, object_property_name)
                create_classes_object_junction(class_id, object_property_id)

            domains = data.get("domains")

            if domains:
                for domain in domains:
                    domain_id = domain.get("domain_id")
                    if domain_id is None:
                        domain_id = uuid.uuid4()
                        create_domain(domain_id, object_property_id,
                                      domain.get("domain_name"))
                    else:
                        res = get_domain_by_id(domain_id)
                        if res:
                            update_domain(domain_id, domain.get("domain_name"))
                        else:
                            return jsonify(response_template({
                                "message": "There is no domain with such ID",
                                "status_code": 404,
                                "data": None
                            })), 404

                        cache.delete(f"object_property_domain_{domain_id}")

                    ranges = domain.get("ranges")

                    if ranges:
                        for rg in ranges:
                            range_id = rg.get("range_id")

                            if range_id is None:
                                range_id = uuid.uuid4()
                                create_range(
                                    range_id, object_property_id, rg.get("range_name"))
                                create_domains_ranges_junction(
                                    object_property_id, domain_id, range_id)
                            else:
                                res = get_range_by_id(range_id)
                                # expected behavior when updating range, the
                                # domain-range junction is already existing
                                if res:
                                    update_range(
                                        range_id, rg.get("range_name"))
                                else:
                                    return jsonify(response_template({
                                        "message": "There is no range with such ID",
                                        "status_code": 404,
                                        "data": None
                                    })), 404

                                cache.delete(f"object_property_range_{range_id}")
                    else:
                        return jsonify(response_template({
                            "message": "Domain should have at least one range",
                            "status_code": 400,
                            "data": None
                        })), 400


    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500


    cache.delete(f"classes_and_properties_{conversation_id}")
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None
    })), 200


async def delete_object_properties_service(class_id):
    try:
        data = request.json
        object_properties = data["object_properties_ids"]
        conversation_id = ""

        for object_property_id in object_properties:
            db_response = get_class_by_id(class_id)
            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no class with such ID",
                    "status_code": 404,
                    "data": None
                })), 404

            if conversation_id == "": conversation_id = db_response["conversation_id"]

            db_response = get_object_property_by_id(object_property_id)
            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no object property with such ID",
                    "status_code": 404,
                    "data": None
                })), 404

            delete_classes_object_junction(class_id, object_property_id)
            delete_object_domains_ranges_junction(object_property_id)
            delete_object_property(object_property_id)

            cache.delete(f"object_properties_{object_property_id}")

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.delete(f"classes_and_properties_{conversation_id}")
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None
    })), 200


async def update_object_property_service(object_property_id): # obselete
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

        # cache.delete(f"object_properties_{object_property_id}")
        # cache.delete(f"classes_and_properties_{conversation_id}")
        # cache.delete(f"owl_file_{conversation_id}")

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
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
        cached_result = cache.get(f"object_property_range_{object_property_id}")

        if cached_result:
            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": cached_result
            })), 200

        db_response = get_all_ranges_by_object_property_id(object_property_id)
        if db_response is None:
            return jsonify(response_template({
                "message": "There is no object property range with such ID",
                "status_code": 404,
                "data": None
            })), 404

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.set(f"object_property_range_{object_property_id}", db_response, timeout=300)
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def update_object_property_range_service(range_id): # obselete
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

        # cache.delete(f"object_property_range_{range_id}")
        # cache.delete(f"classes_and_properties_{conversation_id}")

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
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

        db_response = get_object_property_by_id(object_property_id)
        conversation_id = get_class_by_id(db_response["class_id"])["conversation_id"]

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no object property with such ID",
                "status_code": 404,
                "data": None
            })), 404

        for rg_id in range_ids:
            db_response = get_range_by_id(rg_id)

            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no range with such ID",
                    "status_code": 404,
                    "data": None
                })), 404
            else:
                delete_domains_ranges_junction(
                    range_id=rg_id, object_property_id=object_property_id)
                delete_range(rg_id)

            cache.delete(f"object_property_range_{rg_id}")

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.delete(f"object_property_range_{object_property_id}")
    cache.delete(f"classes_and_properties_{conversation_id}")
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None
    })), 200


async def get_object_property_domain_service(object_property_id):
    try:
        cached_result = cache.get(f"object_property_domain_{object_property_id}")

        if cached_result:
            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": cached_result
            })), 200

        db_response = get_all_domains_by_object_property_id(object_property_id)
        if db_response is None:
            return jsonify(response_template({
                "message": "There is no object property domain with such ID",
                "status_code": 404,
                "data": None
            })), 404

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.set(f"object_property_domain_{object_property_id}", db_response, timeout=300)
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": db_response
    })), 200


async def create_object_property_domain_range_service(object_property_id):
    try:
        data = request.json

        # expect an array of objects containing domain and array of range
        # objects
        db_response = get_object_property_by_id(object_property_id)
        conversation_id = get_class_by_id(db_response["class_id"])["conversation_id"]

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no object property with such ID",
                "status_code": 404,
                "data": None
            })), 404

        domains = data.get("domains")

        for domain in domains:
            # used to check whether to create new junction or update existing
            # one
            new_domain, new_range = False, False

            domain_id = domain.get("domain_id")
            logger.debug(f"domain_id: {domain_id}")
            if domain_id is None:
                domain_id = uuid.uuid4()
                create_domain(domain_id, object_property_id,
                              domain.get("domain_name"))
                new_domain = True
            else:
                res = get_domain_by_id(domain_id)
                if res:
                    update_domain(domain_id, domain.get("domain_name"))
                else:
                    return jsonify(response_template({
                        "message": "There is no domain with such ID",
                        "status_code": 404,
                        "data": None
                    })), 404
                cache.delete(f"object_property_domain_{domain_id}")

            ranges = domain.get("ranges")

            for rg in ranges:
                range_id = rg.get("range_id")

                if range_id is None:
                    range_id = uuid.uuid4()
                    create_range(range_id, object_property_id,
                                 rg.get("range_name"))
                    new_range = True
                else:
                    res = get_range_by_id(range_id)
                    if res:
                        update_range(range_id, rg.get("range_name"))
                    else:
                        return jsonify(response_template({
                            "message": "There is no range with such ID",
                            "status_code": 404,
                            "data": None
                        })), 404

                    cache.delete(f"object_property_range_{range_id}")

                # create junction only if there's a new domain and/or range
                if new_domain or new_range:
                    create_domains_ranges_junction(
                        object_property_id, domain_id, range_id)


    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.delete(f"object_property_domain_{object_property_id}")
    cache.delete(f"classes_and_properties_{conversation_id}")

    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None
    })), 200


async def update_object_property_domain_service(domain_id): # obselete
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

        # cache.delete(f"object_property_domain_{domain_id}")
        # cache.delete(f"classes_and_properties_{conversation_id}")

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
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


async def delete_object_property_domain_service(object_property_id):
    try:
        data = request.json
        domain_ids = data.get("domain_ids")

        db_response = get_object_property_by_id(object_property_id)
        conversation_id = get_class_by_id(db_response["class_id"])["conversation_id"]

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no object property with such ID",
                "status_code": 404,
                "data": None
            })), 404

        for dm_id in domain_ids:
            db_response = get_domain_by_id(dm_id)

            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no domain with such ID",
                    "status_code": 404,
                    "data": None
                })), 404
            else:
                delete_domains_ranges_junction(
                    domain_id=dm_id, object_property_id=object_property_id)
                delete_domain(dm_id)

                cache.delete(f"object_property_domain_{dm_id}")


    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.delete(f"classes_and_properties_{conversation_id}")
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None
    })), 200


async def get_instances_service(conversation_id):
    try:
        cached_result = cache.get(f"instances_{conversation_id}")

        if cached_result:
            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": cached_result
            })), 200

        # db_response = get_all_instances_by_class_id(class_id)
        db_response = get_all_instances_by_conversation_id(conversation_id)
        if db_response is None:
            return jsonify(response_template({
                "message": "There is no instances in conversation with such ID",
                "status_code": 404,
                "data": None
            })), 404

        sanitized_instances = []

        for data in db_response:
            for instance in data.get("instances"):
                if instance.get("instance_name") is None: continue
                else: instance["instance_name"] = instance["instance_name"].replace(" ", "")

            sanitized_instances.append(data)

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.set(f"instances_{conversation_id}", sanitized_instances, timeout=300)
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": sanitized_instances
    })), 200


async def update_instances_service(class_id):
    try:
        data = request.json
        instances = data["instances"]
        conversation_id = get_class_by_id(instances[0].get("class_id"))["conversation_id"]

        for instance in instances:
            instance_name = instance.get("instance_name")
            instance_id = instance.get("instance_id")

            if instance_id is None:
                instance_id = uuid.uuid4()
                create_instance(instance_id, class_id, instance_name)
                create_classes_instances_junction(class_id, instance_id)
            else:
                db_response = get_instance_by_id(instance_id)

                if db_response is None:
                    return jsonify(response_template({
                        "message": "There is no instance with such ID",
                        "status_code": 404,
                        "data": None
                    })), 404

                data = update_instance(instance_id, instance_name)


    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.delete(f"instances_{conversation_id}")
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None
    })), 200


async def delete_instances_service(class_id):
    try:
        data = request.json
        instances = data["instances_ids"]
        class_id = get_instance_by_id(instances[0])["class_id"]
        conversation_id = get_class_by_id(class_id)["conversation_id"]

        for instance_id in instances:
            db_response = get_class_by_id(class_id)
            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no class with such ID",
                    "status_code": 404,
                    "data": None
                })), 404

            db_response = get_instance_by_id(instance_id)
            if db_response is None:
                return jsonify(response_template({
                    "message": "There is no instance with such ID",
                    "status_code": 404,
                    "data": None
                })), 404

            delete_classes_instances_junction(class_id, instance_id)
            delete_instance(instance_id)

    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")
        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.delete(f"instances_{conversation_id}")
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": None
    })), 200


async def generate_owl_file_service(conversation_id):
    try:
        time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        def sanitize_name(name):
            name = name.replace(" ", "_")
            name = ''.join(c for c in name if c.isalnum() or c == '_')
            if not name[0].isalpha() and name[0] != '_':
                name = '_' + name
            return name

        onto = get_ontology(f"https://llm-nfo-frontend.vercel.app/ontology_{conversation_id}.owl#") # creating a new IRI for the ontology

        with onto:
            classes = get_all_classes_by_conversation_id(conversation_id)

            class_dict = {} 
            for cls in classes:
                class_name = cls["name"]
                if class_name is None or class_name == "":
                    continue

                class_name = sanitize_name(cls["name"])
                class_dict[class_name] = types.new_class(class_name, (Thing,)) # for a more complex implementation, a class might be a subclass of another class
                logger.info(f"Created new class '{class_name}'.")

            for cls in classes:
                class_name = cls["name"]
                if class_name is None or class_name == "":
                    continue
                class_name = sanitize_name(cls["name"])
                if class_name in class_dict:
                    CurrentClass = onto[class_name]

                # Data properties
                data_properties = get_all_data_properties_by_class_id(cls["class_id"])
                for dp in data_properties:
                    dp_name = dp["data_property_name"]
                    if dp_name is None or dp_name == "": 
                        continue
                    dp_name = sanitize_name(dp["data_property_name"])

                    new_data_property = types.new_class(dp_name, (DataProperty,))
                    logger.info(f"Created new data property '{dp_name}'.")
                    new_data_property.domain.append(CurrentClass)

                    data_property_type = dp["data_property_type"].lower()
                    if data_property_type == "string":
                        new_data_property.range.append(str)
                    elif data_property_type in ["integer", "int"]:
                        new_data_property.range.append(int)
                    elif data_property_type == "float":
                        new_data_property.range.append(float)
                    elif data_property_type == "boolean":
                        new_data_property.range.append(bool)
                    elif data_property_type == "date":
                        new_data_property.range.append(datetime.date)
                    else:
                        new_data_property.range.append(str)
                        logger.warning(f"Unknown data property type '{data_property_type}' for '{dp_name}'. Defaulting to 'str'.")

                # Object properties
                object_properties = get_all_object_properties_by_class_id(cls["class_id"])
                for op in object_properties:
                    op_name = op["object_property_name"]
                    if op_name is None or op_name == "":
                        continue
                    op_name = sanitize_name(op["object_property_name"])

                    new_object_property = types.new_class(op_name, (ObjectProperty,))
                    logger.info(f"Created new object property '{op_name}'.")
                    new_object_property.domain.append(CurrentClass)

                    # Handle domains
                    domains = get_all_domains_by_object_property_id(op["object_property_id"])
                    logger.info(f"Processing domains for '{op_name}': {domains}")
                    for d in domains:
                        domain_name = d["domains"][0]["domain_name"]
                        if domain_name is None or domain_name == "":
                            continue
                        domain_name = sanitize_name(d["domains"][0]["domain_name"]) 

                        """domain class type supposed to correspond to the type of the domain according to [https://owlready2.readthedocs.io/en/latest/properties.html#creating-a-new-class-of-property]"""
                        domain_class = types.new_class(domain_name, (Thing,)) # for now, we'll use Thing as the domain class type to make it dynamic
                        logger.info(f"Created new domain class '{domain_name}'.")
                        new_object_property.domain = [domain_class]

                    # Handle ranges
                    ranges = get_all_ranges_by_object_property_id(op["object_property_id"])
                    logger.info(f"Processing ranges for '{op_name}': {ranges}")
                    for r in ranges:
                        range_name = r["ranges"][0]["range_name"]
                        if range_name is None or range_name == "":
                            continue
                        range_name = sanitize_name(r["ranges"][0]["range_name"])

                        """range class type supposed to correspond to the type of the range according to [https://owlready2.readthedocs.io/en/latest/properties.html#creating-a-new-class-of-property]"""
                        range_class = types.new_class(range_name, (Thing,))
                        logger.info(f"Created new range class '{range_name}'.")
                        new_object_property.range = [range_class]

                # Instances
                instances = get_all_instances_by_class_id(cls["class_id"])
                for instance in instances:
                    try:
                        instance_name = instance['instance_name']
                        if instance_name is None or instance_name == "":
                            continue 
                        instance_name = sanitize_name(instance['instance_name'])

                        logger.info(f"Creating instance '{instance_name}' for class '{class_name}'.")
                        _ = CurrentClass(instance_name)
                        logger.info(f"Created new instance '{instance_name}'.")
                    except Exception as e:
                        logger.error(f"Failed to create instance '{instance_name}' for class '{class_name}': {str(e)}")

        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".owl") as temp_file:
                onto.save(file=temp_file.name, format="rdfxml")
                temp_file_path = temp_file.name

            return send_file(
                temp_file_path,
                as_attachment=True,
                download_name=f"ontology_{conversation_id}_{time}.owl",
                mimetype="application/rdf+xml"
            )

        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            onto.destroy()

    except Exception as e:
        logger.error(f"An error occurred while generating OWL file: {str(e)}", exc_info=True)
        return jsonify(response_template({
            "message": f"An error occurred while generating OWL file: {str(e)}",
            "status_code": 500,
            "data": None
        })), 500


async def get_existing_ontologies_service(conversation_id):
    try:
        cached_result = cache.get(f"existing_ontologies_{conversation_id}")

        if cached_result:
            return jsonify(response_template({
                "message": "Success",
                "status_code": 200,
                "data": cached_result
            })), 200

        data = request.get_json()
        prompt = data.get("prompt")
        db_response = get_conversation_detail_by_id(conversation_id)

        if db_response is None:
            return jsonify(response_template({
                "message": "There is no conversation with such ID",
                "status_code": 404,
                "data": None
            })), 404

        # prompt = {
        #     "domain": db_response["domain"],
        #     "scope": db_response["scope"],
        #     "prompt": prompt,
        # }

        # llm_response = await prompt_chatai(prompt, input_variables=["domain",
        # "scope", "prompt"],
        # template=EXISTING_ONTOLOGIES_GENERATION_SYSTEM_MESSAGE)

        search_result = await llm_search_google(
            prompt, db_response["domain"], db_response["scope"])
        llm_response_json = reformat_response_existing_ontology(search_result.content)


    except Exception as e:
        logger.error(
            f"an error occurred at route {request.path} with error: {e}")

        return jsonify(response_template({
            "message": f"an error occurred at route {request.path} with error: {e}",
            "status_code": 500,
            "data": None
        })), 500

    cache.set(f"existing_ontologies_{conversation_id}", llm_response_json, timeout=300)
    return jsonify(response_template({
        "message": "Success",
        "status_code": 200,
        "data": llm_response_json
    })), 200
