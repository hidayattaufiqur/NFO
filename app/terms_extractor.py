from flask import Blueprint, jsonify, request 
from werkzeug.utils import secure_filename
from llmsherpa.readers import LayoutPDFReader
from flair.nn import Classifier 
from flair.data import Sentence
from segtok.segmenter import split_single

from . import helper

import logging 
import os
import json
import requests

logger = logging.getLogger(__name__)

bp = Blueprint('terms_extractor', __name__, url_prefix='/terms_extractor')

@bp.route('/pdf', methods=['POST'])
def extract_from_pdf():
    filename = ""
    filepath = ""

    try: 
        if "file" not in request.files:
            logger.error("no file is uploaded")
            return jsonify(helper.response_template({
                "message": "no file uploaded",
                "status_code": 400,
                "data": None
            })), 400

        file = request.files['file']

        if file.filename == '':
            logger.error("no file selected")
            return jsonify(helper.response_template({
                "message": "No file selected",
                "status_code": 400,
                "data": None
            })), 400

        if file and helper.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(helper.UPLOAD_FOLDER, filename)
            file.save(filepath)

        extracted_text = extract_text_from_pdf(filepath)
        if extracted_text is None: 
            logger.error("error extracting text from pdf")
            return jsonify(helper.response_template({
                "message": "Error extracting text from pdf",
                "status_code": 500,
                "data": None
            })), 500

        logger.info("predicting tags with flair NER model")
        predicted_tags = predict_with_flair(extracted_text)

        logger.info("invoking awan llm")
        awan_llm_response = prompt_awan_llm(predicted_tags)
        logger.info(f"awan llm response: {awan_llm_response}")

    except Exception as e: 
        logger.error(f"{e}")
        return helper.response_template({
            "message": "Error extracting text from pdf",
            "status_code": 500,
            "data": None
        }), 500

    logger.info("file uploaded successfully")
    return helper.response_template({
        "message": "File uploaded successfully",
        "status_code": 200,
        "data": {
            "filename": filename,
            "extracted_text": extracted_text, 
            "predicted_tags": predicted_tags,
            "important_terms": awan_llm_response
        }
    }), 200

def extract_text_from_pdf(pdf_file_path):
    try: 
        logger.info("offloading pdf reading to llmsherpa api")
        llmsherpa_api_url = "https://readers.llmsherpa.com/api/document/developer/parseDocument?renderFormat=all"
        pdf_reader = LayoutPDFReader(llmsherpa_api_url)

        logger.info("pdf file read successfully")
        doc = pdf_reader.read_pdf(pdf_file_path)
        doc_json = doc.json

        extracted_text = [] 
        for value in doc_json: 
            if "sentences" in value:
                extracted_text.append(value["sentences"][0])

        return extracted_text 

    except Exception as e: 
        logger.error(f"{e}")
        return None

def predict_with_flair(sentences): 
    tagged_sentences = []

    logger.info("loading flair NER model")
    tagger = Classifier.load("ner") # load flair NER model 

    logger.info("predicting NER tags")
    for sentence in sentences: 
        sentence = helper.clean_text(sentence)
        logger.info("split sentence into segments")
        splitted_sentence = [Sentence(sent) for sent in split_single(sentence)]
        logger.info("text splitted successfully")
        tagger.predict(splitted_sentence) # predict NER tags

        for sent in splitted_sentence:
            logger.info("extracting NER tags")
            for entity in sent.get_spans("ner"): 
                logger.info(f"entity-text {entity.text}")
                logger.info(f"entity-tag {entity.tag}")
                logger.info(f"entity-score {entity.score}")
                logger.info(f"entity-labels {entity.labels}")
                logger.info(f"entity-unlabeled_identifier {entity.unlabeled_identifier}")

                tagged_sentence = {}
                tagged_sentence.update({"text": entity.text})
                tagged_sentence.update({"tag": entity.tag})
                tagged_sentence.update({"score": entity.score})
                tagged_sentences.append(tagged_sentence)

    return tagged_sentences

def prompt_awan_llm(tagged_sentences, domain = "web protocol", scope = "http"):
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
        }
      ]
    })
    headers = {
      'Content-Type': 'application/json',
        'Authorization': f"Bearer {os.environ.get("AWAN_API_KEY")}"
    }

    logger.info("invoking prompt to awan llm")
    response = requests.request("POST", url, headers=headers, data=payload)
    logger.info("prompt result has been received")

    return response.json()
