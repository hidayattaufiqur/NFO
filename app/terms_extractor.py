from flask import Blueprint, request 
from werkzeug.utils import secure_filename
from . import helper

import logging 
import os

logger = logging.getLogger(__name__)

bp = Blueprint('terms_extractor', __name__, url_prefix='/terms_extractor')

@bp.route('/pdf', methods=['POST'])
def upload_pdf():
    if request.method == 'POST':
        if 'file' not in request.files:
            logger.error("no file is uploaded")
            return helper.response_template({
                "message": "No file uploaded",
                "status_code": 400,
                "data": None
            }), 400

        file = request.files['file']

        if file.filename == '':
            logger.error("no file selected")
            return helper.response_template({
                "message": "No file selected",
                "status_code": 400,
                "data": None
            }), 400

        if file and helper.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(helper.UPLOAD_FOLDER, filename))

    logger.info("file uploaded successfully")

    return helper.response_template({
        "message": "File uploaded successfully",
        "status_code": 200,
        "data": {
            "filename": filename
        }
    }), 200
