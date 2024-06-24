from flair.data import Sentence
from segtok.segmenter import split_single
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import  LLMChain

from spacy import load

from llmsherpa.readers import LayoutPDFReader

import re
import time
import json
import logging
import requests
from torch import parse_type_comment

from app.utils import * 

logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0) # TODO: try different temp

logger.info("loading flair NER model")
start_time = time.time()
# tagger = Classifier.load("ner-fast") # load flair NER model 
# tagger = SequenceTagger.load("ner-fast") # load flair NER model 
tagger = load("en_core_web_sm")
logger.info(f"NER loaded in {round(time.time() - start_time, 3)}S")


def extract_text_from_pdf(pdf_file_path):
    try:
        logger.info("offloading pdf reading to llmsherpa api")
        start_time = time.time()
        llmsherpa_api_url = "https://readers.llmsherpa.com/api/document/developer/parseDocument?renderFormat=all"
        pdf_reader = LayoutPDFReader(llmsherpa_api_url)

        doc = pdf_reader.read_pdf(pdf_file_path)
        doc_json = doc.json

        extracted_text = []
        for value in doc_json:
            if "sentences" in value:
                extracted_text.append(value["sentences"][0])

        end_time = time.time()
        logger.info(f"pdf file read and text extracted successfully in {end_time - start_time:,.2f} seconds")

        return extracted_text

    except Exception as e:
        logger.error(f"{e}")
        return None

def predict_with_flair(sentences):
    start_time = time.time()
    tagged_sentences = []

    logger.info("predicting NER tags")
    if isinstance(sentences, str):
        sentences = [sentences]

    for sentence in sentences:
        cleaned_sentence = clean_text(sentence)
        logger.info("splitting sentence into segments")
        splitted_sentences = [Sentence(sent) for sent in split_single(cleaned_sentence) if sent]
        logger.info("text splitted successfully")
        tagger.predict(splitted_sentences) # predict NER tags

        for sent in splitted_sentences:
            logger.info("extracting NER tags")
            for entity in sent.get_spans("ner"):
                logger.debug(f"entity: {entity.to_dict()}")
                tagged_sentences.append({
                    "text": entity.text,
                    "tag": entity.tag,
                    "score": entity.score
                })

    end_time = time.time()
    logger.info(f"NER predicting has been completed in {end_time - start_time:,.2f} seconds")

    return tagged_sentences

def predict_with_spacy(sentences):
    start_time = time.time()
    tagged_sentences = []

    logger.info("predicting NER tags")
    doc = tagger(sentences)
    for entity in doc.ents:
        logger.debug(f"entity: {entity}")
        tagged_sentences.append({
            "text": entity.text,
            "tag": entity.label_,
        })

    end_time = time.time()
    logger.info(f"NER predicting has been completed in {end_time - start_time:,.2f} seconds")

    return tagged_sentences

def chunk_list(lst, chunk_size=100):
    """Splits a list into chunks of maximum length."""
    start_time = time.time()
    logger.info(f"tagged_sentences length: {len(lst)}")
    for i in range(0, len(lst), chunk_size):
        chunk = lst[i:i + chunk_size]
        logger.info(f"Processing chunk: {chunk}")
        yield [item['text'] for item in chunk]
    end_time = time.time()
    logger.info(f"List chunking completed in {end_time - start_time:,.2f} seconds")

def extract_terms(content):
    """Extracts and cleans up terms from the response content."""
    start_time = time.time()
    terms = []
    # Split the content by commas and process each item
    # for item in content.split(','):
    #     item = item.replace('"important_terms":', '').replace('[', '').replace(']', '').strip()
    #     if item:
    #         terms.append(item.strip('" '))

    # Use regex to find both quoted and unquoted terms
    matches = re.findall(r'"([^"]+)"|\b\w+\b', content)
    
    # Filter out empty matches and standardize terms
    terms = [match if match else term for match, term in zip(matches, content.split(','))]
    terms = [f'"{term.strip()}"' for term in terms]

    end_time = time.time()
    logger.info(f"Term extraction completed in {end_time - start_time:,.2f} seconds")
    return terms

async def prompt_chatai(prompt):
    start_time = time.time()
    x = LLMChain(
        llm=llm,
        prompt=PromptTemplate(
            input_variables=["domain", "scope", "important_terms"],
            template=CLASSES_PROPERTIES_GENERATION_SYSTEM_MESSAGE,
            template_format="jinja2"
        ),
        verbose=True
    )

    logger.info(f"Invoking prompt to OpenAI")
    llm_response = await x.ainvoke(prompt)
    logger.info(f"type: ({type(llm_response)}, ChatOpenAI response {llm_response})")

    end_time = time.time()
    logger.info(f"Prompting ChatOpenAI completed in {end_time - start_time:,.2f} seconds")
    return llm_response

def prompt_awan_llm(tagged_sentences, domain, scope):
    start_time = time.time()
    url = "https://api.awanllm.com/v1/chat/completions"

    payload = json.dumps({
      "model": "Meta-Llama-3-8B-Instruct",
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
     "temperature": 0.7,
    })
    headers = {
      'Content-Type': 'application/json',
        'Authorization': f"Bearer {os.environ.get('AWAN_API_KEY')}"
    }

    logger.info("invoking prompt to awan llm")
    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code != 200:
        logger.error(f"Failed to invoke prompt to awan llm. Status code: {response.status_code}, Response: {response.text}")
        raise ValueError(f"Failed to invoke prompt to awan llm. Status code: {response.status_code}, Response: {response.text}")

    end_time = time.time()
    logger.info(f"prompt result has been received in {end_time - start_time:,.2f} seconds")
    logger.info(f"prompt result {response}")

    try:
        return response.json()
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Response content: {response.text}")

        raise ValueError(f"Failed to parse JSON response. Status code: {response.status_code}, Response: {response.text}")

def prompt_awan_llm_chunked(tagged_sentences, domain, scope):
    """Handles large tagged sentences by chunking."""
    start_time = time.time()
    max_tokens = 512
    chunk_size = max_tokens // 2
    chunks = chunk_list(tagged_sentences, chunk_size)
    combined_response = []

    for chunk in chunks:
        response = prompt_awan_llm(chunk, domain, scope)
        logger.info(f"response in chunk {response}")
        if "statusCode" in response:
            logger.error(f"Error invoking awan llm with error: {response['message']}")
            return response
        # Process the response content
        content = response["choices"][0]["message"]["content"]
        logger.info(f"Raw response content: {content}")

        # Extract and clean up terms
        terms = extract_terms(content)
        combined_response.extend(terms)

    # Remove duplicates and ensure clean terms
    combined_response = list(set(combined_response))
    end_time = time.time()
    logger.info(f"prompt_awan_llm_chunked completed in {end_time - start_time:,.2f} seconds")
    logger.info(f"combined_response {combined_response}")
    return {"choices": [{"message": {"content": combined_response}}]}

def reformat_response(llm_response):
    """Reformats the raw response text into the desired JSON structure."""
    start_time = time.time()
    try:
        logger.info(f"type of llm_response {type(llm_response)}")
        if isinstance(llm_response, dict):
            try:
                raw_data = json.dumps(llm_response['text'])
                logger.info(f"type of raw data {type(raw_data)}")
                logger.info(f"raw data {raw_data}")

                parsed_data = json.loads(raw_data)
                logger.info(f"type of parsed_data {type(parsed_data)}")
                logger.info(f"parsed data {parsed_data}")

                parsed_data = json.loads(parsed_data)
                logger.info(f"type of parsed_data {type(parsed_data)}")
                logger.info(f"parsed data {parsed_data}")

                if isinstance(parsed_data, str):
                    return parsed_data
                
                llm_response_json = {
                    "llm_output": {
                        "domain": parsed_data.get("domain"),
                        "scope": parsed_data.get("scope"),
                        "important_terms": parsed_data.get("important_terms"),
                        "classes": parsed_data.get("classes"),
                        "ambiguous_terms": parsed_data.get("ambiguous_terms"),
                    },
                }

            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding failed: {e}")
                raise ValueError(f"Failed to decode JSON. Error: {e}")
        else:
            try:
                llm_response_json = json.loads(llm_response['text'])
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding failed: {e}")
                raise ValueError(f"Failed to decode JSON. Error: {e}")

        end_time = time.time()
        logger.info(f"Response reformatting completed in {end_time - start_time:,.2f} seconds")
        return llm_response_json

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding failed: {e}")
        raise ValueError(f"Failed to decode JSON. Error: {e}")

