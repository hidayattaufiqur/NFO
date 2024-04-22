from flask import Blueprint, jsonify, request 
from werkzeug.utils import secure_filename
from llmsherpa.readers import LayoutPDFReader
from flair.nn import Classifier 
from flair.data import Sentence

from . import helper

import logging 
import os

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
            "predicted_tags": predicted_tags
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
                extracted_text.append(value["sentences"])

        return extracted_text 

    except Exception as e: 
        logger.error(f"{e}")
        return None

def predict_with_flair(sentences): 
    tagged_sentences = []

    logger.info("loading flair NER model")
    tagger = Classifier.load("ner") # load flair NER model 

    logger.info("predicting NER tags")
    i = 1
    for sentence in sentences: 
        helper.clean_text(sentence)
        sentence = Sentence(sentence)
        tagger.predict(sentence) # predict NER tags
        logger.info("============================================")
        logger.info(f"predicted tags for sentence {i}")
        logger.info(f"sentence: {sentence}")
        logger.info("============================================")
        i+=1

        for entity in sentence.get_spans("ner"): 
            logger.info(f"entity {entity.text}")
            logger.info(f"entity type {type(entity)}")
            tagged_sentences.append(entity)

    return tagged_sentences
