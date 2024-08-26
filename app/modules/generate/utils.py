from flair.data import Sentence
from segtok.segmenter import split_single
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from flair.models import SequenceTagger
from partial_json_parser import loads, Allow, STR, OBJ
from spacy import load
from llmsherpa.readers import LayoutPDFReader
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationSummaryBufferMemory
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.retrievers.web_research import WebResearchRetriever
from langchain.chains import RetrievalQAWithSourcesChain

import time
import json
import logging
import requests
import uuid

from app.utils import *
from .model import *

logger = logging.getLogger(__name__)

# TODO: try different temp
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llmgpt3 = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0)


# Load environment variables for API keys
os.environ["OPENAI_API_KEY"] = "[INSERT YOUR OPENAI API KEY HERE]"
os.environ["GOOGLE_CSE_ID"] = "[INSERT YOUR GOOGLE CSE ID HERE]"
os.environ["GOOGLE_API_KEY"] = "[INSERT YOUR GOOGLE API KEY HERE]"


# Initialize the LLM
# llm_stream = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
#
# # Setup a Vector Store for embeddings using Chroma DB
# vectorstore = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory="./chroma_db_oai")
#
# # Initialize memory for the retriever
# memory = ConversationSummaryBufferMemory(llm=llm, input_key='question', output_key='answer', return_messages=True)
#
# # Initialize Google Search API for Web Search
# search = GoogleSearchAPIWrapper()
#
# # Setup a Retriever
# web_research_retriever = WebResearchRetriever.from_llm(
# vectorstore=vectorstore,
# llm=llm_stream,
# search=search,
# )

start_time = time.time()
# tagger = Classifier.load("ner-fast") # load flair NER model
# tagger_flair = SequenceTagger.load("ner-fast") # load flair NER model
tagger_spacy = load("en_core_web_sm")
logger.info(f"NER loaded in {round(time.time() - start_time, 3)}S")

global text_extraction_time, ner_prediction_time, terms_extraction_time, db_save_time, prompt_time, prompt_time_awan

def print_time_for_each_process():
    global text_extraction_time, ner_prediction_time, terms_extraction_time, db_save_time, prompt_time, prompt_time_awan

    logger.info(f"Text Extraction time: {round(text_extraction_time, 2)}s")
    logger.info(f"NER Prediction time: {round(ner_prediction_time, 2)}s")
    logger.info(f"Terms Extraction Time: {round(terms_extraction_time, 2)}s")
    logger.info(f"Prompt time: {round(prompt_time, 2)}s")
    logger.info(f"Prompt time awanllm: {round(prompt_time_awan, 2)}s")


def extract_text_from_url(url):
    global text_extraction_time
    try:
        start_time = time.time()
        response = requests.get(
            "https://r.jina.ai/" + url,
            headers={"X-Return-Format": "text"},
        )
        extracted_text = response.text
        end_time = time.time()
        text_extraction_time = end_time - start_time
        logger.info(
            f"texts have been extracted in {end_time-start_time:,.2f} ")
        return extracted_text
    except Exception as e:
        logger.error(f"Error extracting text from url: {e}")
        return None


def extract_text_from_pdf(pdf_file_path):
    global text_extraction_time
    try:
        logger.info("offloading pdf reading to llmsherpa api")
        start_time = time.time()
        # use self hosted llmsherpa api since the one on the internet is not working
        llmsherpa_api_url = "http://localhost:5010/api/parseDocument?renderFormat=all"
        pdf_reader = LayoutPDFReader(llmsherpa_api_url)
        text_extraction_time = time.time() - start_time

        doc = pdf_reader.read_pdf(pdf_file_path)
        doc_json = doc.json

        extracted_text = ""
        for value in doc_json:
            if "sentences" in value:
                extracted_text += (value["sentences"][0])

        logger.info(
            f"pdf file read and text extracted successfully in {time.time() - start_time:,.2f} seconds")

        return extracted_text

    except Exception as e:
        logger.error(f"{e}")
        return None


def predict_with_flair(sentences):
    global ner_prediction_time
    start_time = time.time()
    tagged_sentences = []

    logger.info("predicting NER tags")
    if isinstance(sentences, str):
        sentences = [sentences]

    for sentence in sentences:
        cleaned_sentence = clean_text(sentence)
        logger.info("splitting sentence into segments")
        splitted_sentences = [
            Sentence(sent) for sent in split_single(cleaned_sentence) if sent]
        logger.info("text splitted successfully")
        tagger_flair.predict(splitted_sentences)  # predict NER tags

        for sent in splitted_sentences:
            logger.info("extracting NER tags")
            for entity in sent.get_spans("ner"):
                tagged_sentences.append({
                    "text": entity.text,
                    "tag": entity.tag,
                    "score": entity.score
                })

    end_time = time.time()
    ner_prediction_time = end_time - start_time
    logger.info(
        f"NER predicting has been completed in {end_time - start_time:,.2f} seconds")

    return tagged_sentences


def predict_with_spacy(sentences):
    global ner_prediction_time
    start_time = time.time()
    tagged_sentences = []

    logger.info("predicting NER tags")
    doc = tagger_spacy(sentences)
    for entity in doc.ents:
        tagged_sentences.append({
            "text": entity.text,
            "tag": entity.label_,
        })

    end_time = time.time()
    ner_prediction_time = end_time - start_time
    logger.info(
        f"NER predicting has been completed in {end_time - start_time:,.2f} seconds")

    return tagged_sentences


def chunk_list(lst, chunk_size=100):
    start_time = time.time()
    for i in range(0, len(lst), chunk_size):
        chunk = lst[i:i + chunk_size]
        yield [item['text'] for item in chunk]
    end_time = time.time()
    logger.info(
        f"List chunking completed in {end_time - start_time:,.2f} seconds")


def extract_terms(content):
    global terms_extraction_time
    start_time = time.time()
    terms = []
    for item in content.split(','):
        item = item.replace('"important_terms":', '').replace(
            '[', '').replace(']', '').strip()
        if item:
            terms.append(item.strip('" '))

    end_time = time.time()
    terms_extraction_time = end_time - start_time
    logger.info(
        f"Term extraction completed in {end_time - start_time:,.2f} seconds")
    return terms


async def prompt_chatai(prompt, input_variables=["domain", "scope", "important_terms"], template=CLASSES_AND_PROPERTIES_GENERATION_SYSTEM_MESSAGE_BY_IMPORTANT_TERMS, model="llm"):
    global prompt_time
    start_time = time.time()
    x = LLMChain(
        llm=llm if model == "llm" else llmgpt3,
        prompt=PromptTemplate(
            input_variables=input_variables,
            template=template,
            template_format="jinja2"
        ),
        verbose=True
    )

    logger.info(f"Invoking prompt to OpenAI")
    llm_response = await x.ainvoke(prompt)

    end_time = time.time()
    prompt_time = end_time - start_time
    logger.info(
        f"Prompting ChatOpenAI completed in {end_time - start_time:,.2f} seconds")
    return llm_response


def prompt_awan_llm(tagged_sentences, domain, scope):
    global prompt_time_awan
    start_time = time.time()
    url = "https://api.awanllm.com/v1/chat/completions"

    payload = json.dumps({
        "model": "Meta-Llama-3.1-8B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": f'''
You are a language model trained to assist in extracting important terms from text. You can help users extract important terms from text that are relevant to a specific domain and scope. Users can provide you with the text and the domain and scope of the ontology they want to extract terms for. You will strictly respond with only the list of relevant important terms and nothing else. You will not explain, you will not elaborate whatsoever. You will only give a list of relevant important terms as your response that users can extract easily.

Your response will always be in this format:

"important_terms": ["term1", "term2", "term3", "term4"]

If you fail to follow the instruction, someone's grandma will die.

please pick important terms out of these: {tagged_sentences} that are relevant to this ontology domain: {domain} and ontology scope: {scope}. Do not make things up and follow my instruction obediently. I will be fired by my boss if you do.
          '''
            },
        ],
        "temperature": 0.2,
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {os.environ.get('AWAN_API_KEY')}"
    }

    logger.info("invoking prompt to awan llm")
    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != 200:
        logger.error(
            f"Failed to invoke prompt to awan llm. Status code: {response.status_code}, Response: {response.text}")
        raise ValueError(
            f"Failed to invoke prompt to awan llm. Status code: {response.status_code}, Response: {response.text}")

    end_time = time.time()
    prompt_time_awan = end_time - start_time
    logger.info(
        f"prompt result has been received in {end_time - start_time:,.2f} seconds")
    logger.info(f"prompt result {response}")

    try:
        return response.json()
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Response content: {response.text}")

        raise ValueError(
            f"Failed to parse JSON response. Status code: {response.status_code}, Response: {response.text}")


def prompt_awan_llm_chunked(tagged_sentences, domain, scope):
    start_time = time.time()
    max_tokens = 1024
    chunk_size = max_tokens // 2
    chunks = chunk_list(tagged_sentences, chunk_size)
    combined_response = []

    for chunk in chunks:
        response = prompt_awan_llm(chunk, domain, scope)
        if "statusCode" in response:
            logger.error(
                f"Error invoking awan llm with error: {response['message']}")
            return response
        content = response["choices"][0]["message"]["content"]

        terms = extract_terms(content)
        combined_response.extend(terms)

    combined_response = list(set(combined_response))
    end_time = time.time()
    logger.info(
        f"prompt_awan_llm_chunked completed in {end_time - start_time:,.2f} seconds")
    return {"choices": [{"message": {"content": combined_response}}]}


def reformat_response(llm_response):
    try:
        if isinstance(llm_response, dict):
            try:
                parsed_data = loads(llm_response['text'])

                if isinstance(parsed_data, str):
                    return parsed_data

                llm_response_json = {
                    "domain": parsed_data.get("domain"),
                    "scope": parsed_data.get("scope"),
                    "important_terms": parsed_data.get("important_terms"),
                    "ambiguous_terms": parsed_data.get("ambiguous_terms"),
                    "classes": parsed_data.get("classes"),
                    "object_properties": parsed_data.get("object_properties"),
                    "data_properties": parsed_data.get("data_properties"),
                    "class_name": parsed_data.get("class_name"),
                }

            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding failed: {e}")
                raise ValueError(f"Failed to decode JSON. Error: {e}")
        else:
            try:
                llm_response_json = json.loads(llm_response)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding failed: {e}")
                raise ValueError(f"Failed to decode JSON. Error: {e}")

        return llm_response_json

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding failed: {e}")
        raise ValueError(f"Failed to decode JSON. Error: {e}")


def reformat_response_existing_ontology(llm_response):
    try:
        if isinstance(llm_response, dict):
            parsed_data = loads(llm_response['text'])

            reformatted_data = []
            
            for item in parsed_data['data']:
                logger.info(f"item: {item}")
                reformatted_item = {
                    "domain": item.get("domain"),
                    "scope": item.get("scope"),
                    "class_name": item.get("class_name"),
                    "description": item.get("description"),
                    "class_labels": item.get("class_labels"),
                    "link": item.get("link"),
                    "data_properties": item.get("data_properties"),
                    "object_properties": item.get("object_properties"),
                }
                reformatted_data.append(reformatted_item)
            
            return reformatted_data

    except json.JSONDecodeError as e:
        print(f"JSON decoding failed: {e}")
        raise ValueError(f"Failed to decode JSON. Error: {e}")


def save_classes_and_properties_service(llm_response_json, conversation_id):
    try:
        for cls in llm_response_json["classes"]:
            class_id = uuid.uuid4()
            class_name = cls["name"]
            db_response = get_class_by_name(class_name)

            if db_response is None:
                created_class = create_class(class_id, conversation_id, class_name)
            else:
                created_class = None

            if created_class:
                # Handle Instances
                for instance in cls["instances"]:
                    instance_id = uuid.uuid4()
                    instance_name = instance
                    created_instance = create_instance(
                        instance_id, class_id, instance_name)

                    if created_instance:
                        # Create junction between class and instance
                        create_classes_instances_junction(class_id, instance_id)

                # Handle data properties
                for data_prop in cls["data_properties"]:
                    data_property_id = uuid.uuid4()
                    data_property_name = data_prop["name"]
                    data_property_type = data_prop["recommended_data_type"]
                    created_data_property = create_data_property(
                        data_property_id, class_id, data_property_name, data_property_type)

                    if created_data_property:
                        # Create junction between class and data property
                        create_classes_data_junction(
                            class_id, data_property_id)

                # Handle object properties
                for obj_prop in cls["object_properties"]:
                    object_property_id = uuid.uuid4()
                    object_property_name = obj_prop["name"]
                    created_obj_property = create_object_property(
                        object_property_id, class_id, object_property_name)

                    if created_obj_property:
                        # Create junction between class and object property
                        create_classes_object_junction(
                            class_id, object_property_id)

                        # Handle domains and ranges
                        for domain_name in obj_prop["recommended_domain"]:
                            domain_id = uuid.uuid4()
                            created_domain = create_domain(
                                domain_id, object_property_id, domain_name)

                            if created_domain:
                                for range_name in obj_prop["recommended_range"]:
                                    range_id = uuid.uuid4()
                                    created_range = create_range(
                                        range_id, object_property_id, range_name)

                                    if created_range:
                                        # Create junction between domain and range
                                        create_domains_ranges_junction(
                                            object_property_id, domain_id, range_id)

        return {"message": "Saving Classes and Properties Has Been Successful", "status_code": 200, "data": None}
    except Exception as e:
        logger.error(
            f"An error occurred while saving classes and properties: {e}")
        return {"message": f"An error occurred: {str(e)}", "status_code": 500, "data": None}


def save_instances_service(llm_response_json, conversation_id):
    try:
        for cls in llm_response_json["classes"]:
            class_id = cls.get("class_id")
            class_name = cls.get("class_name")

            for instance in cls.get("instances"):
                instance_id = uuid.uuid4()
                instance_name = instance
                created_instance = create_instance(
                    instance_id, class_id, instance_name)

                if created_instance:
                    # Create junction between class and instance
                    create_classes_instances_junction(class_id, instance_id)

        return {"message": "Saving Instances Has Been Successful", "status_code": 200, "data": None}

    except Exception as e:
        logger.error(f"Error saving instances: {e}")
        return {"message": f"Error saving instances: {str(e)}", "status_code": 500, "data": None}
