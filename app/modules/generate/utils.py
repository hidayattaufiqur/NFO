from flair.data import Sentence
from segtok.segmenter import split_single
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain.chains import  LLMChain
from flair.models import SequenceTagger
from partial_json_parser import loads, Allow, STR, OBJ

from spacy import load

from llmsherpa.readers import LayoutPDFReader

import time
import json
import logging
import requests

from app.utils import * 

logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-3.5-turbo-0613", temperature=0) # TODO: try different temp
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
        logger.info(f"texts have been extracted in {end_time-start_time:,.2f} ")
        return extracted_text
    except Exception as e:
        logger.error(f"Error extracting text from url: {e}")
        return None

def extract_text_from_pdf(pdf_file_path):
    global text_extraction_time
    try:
        logger.info("offloading pdf reading to llmsherpa api")
        start_time = time.time()
        llmsherpa_api_url = "http://localhost:5010/api/parseDocument?renderFormat=all" # use self hosted llmsherpa api since the one on the internet is not working
        pdf_reader = LayoutPDFReader(llmsherpa_api_url)
        text_extraction_time = time.time() - start_time

        doc = pdf_reader.read_pdf(pdf_file_path)
        doc_json = doc.json

        extracted_text = ""
        for value in doc_json:
            if "sentences" in value:
                extracted_text += (value["sentences"][0])

        logger.info(f"pdf file read and text extracted successfully in {time.time() - start_time:,.2f} seconds")

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
        splitted_sentences = [Sentence(sent) for sent in split_single(cleaned_sentence) if sent]
        logger.info("text splitted successfully")
        tagger_flair.predict(splitted_sentences) # predict NER tags

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
    logger.info(f"NER predicting has been completed in {end_time - start_time:,.2f} seconds")

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
    logger.info(f"NER predicting has been completed in {end_time - start_time:,.2f} seconds")

    return tagged_sentences

def chunk_list(lst, chunk_size=100):
    start_time = time.time()
    for i in range(0, len(lst), chunk_size):
        chunk = lst[i:i + chunk_size]
        yield [item['text'] for item in chunk]
    end_time = time.time()
    logger.info(f"List chunking completed in {end_time - start_time:,.2f} seconds")

def extract_terms(content):
    global terms_extraction_time
    start_time = time.time()
    terms = []
    for item in content.split(','):
        item = item.replace('"important_terms":', '').replace('[', '').replace(']', '').strip()
        if item:
            terms.append(item.strip('" '))

    end_time = time.time()
    terms_extraction_time = end_time - start_time
    logger.info(f"Term extraction completed in {end_time - start_time:,.2f} seconds")
    return terms

async def prompt_chatai(prompt, input_variables=["domain", "scope", "important_terms"], template=TERMS_CLASSES_PROPERTIES_GENERATION_SYSTEM_MESSAGE):
    global prompt_time
    start_time = time.time()
    x = LLMChain(
        llm=llm,
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
    logger.info(f"Prompting ChatOpenAI completed in {end_time - start_time:,.2f} seconds")
    return llm_response

def prompt_awan_llm(tagged_sentences, domain, scope):
    global prompt_time_awan
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
    prompt_time_awan = end_time - start_time
    logger.info(f"prompt result has been received in {end_time - start_time:,.2f} seconds")
    logger.info(f"prompt result {response}")

    try:
        return response.json()
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Response content: {response.text}")

        raise ValueError(f"Failed to parse JSON response. Status code: {response.status_code}, Response: {response.text}")

def prompt_awan_llm_chunked(tagged_sentences, domain, scope):
    start_time = time.time()
    max_tokens = 512
    chunk_size = max_tokens // 2
    chunks = chunk_list(tagged_sentences, chunk_size)
    combined_response = []

    for chunk in chunks:
        response = prompt_awan_llm(chunk, domain, scope)
        if "statusCode" in response:
            logger.error(f"Error invoking awan llm with error: {response['message']}")
            return response
        content = response["choices"][0]["message"]["content"]

        terms = extract_terms(content)
        combined_response.extend(terms)

    combined_response = list(set(combined_response))
    end_time = time.time()
    logger.info(f"prompt_awan_llm_chunked completed in {end_time - start_time:,.2f} seconds")
    return {"choices": [{"message": {"content": combined_response}}]}

def reformat_response(llm_response):
    try:
        if isinstance(llm_response, dict):
            try:
                raw_data = json.dumps(llm_response)
                parsed_data = loads(raw_data)
                parsed_data = parsed_data['text']

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

        return llm_response_json

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding failed: {e}")
        raise ValueError(f"Failed to decode JSON. Error: {e}")
