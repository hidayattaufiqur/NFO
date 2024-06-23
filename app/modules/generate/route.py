from flask import Blueprint
from app.utils import require_authorization

from .service import *

bp = Blueprint('terms_extractor', __name__, url_prefix='/terms_extractor')

@bp.route('/pdf', methods=['POST'])
@require_authorization
async def get_important_terms_from_pdf():
    return await get_important_terms_from_pdf_service()
    

@bp.route("/url", methods=["POST"])
@require_authorization
async def get_important_terms_from_url(): 
    return await get_important_terms_from_url_service()
    

@bp.route('/generate', methods=['POST'])
@require_authorization
async def generate_classes_and_properties():
    return await generate_classes_and_properties_service()

