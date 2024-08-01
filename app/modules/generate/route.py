from flask import Blueprint
from app.utils import require_authorization

from .service import *

bp = Blueprint('generation', __name__, url_prefix='/generation')

@bp.route('/terms/pdf', methods=['POST'])
@require_authorization
async def generate_important_terms_from_pdf():
    return await generate_important_terms_from_pdf_service()

    
@bp.route('/terms/url', methods=["POST"])
@require_authorization
async def generate_important_terms_from_url(): 
    return await generate_important_terms_from_url_service()


@bp.route('/terms/<conversation_id>', methods=['GET'])
@require_authorization
async def get_important_terms(conversation_id):
    return await get_important_terms_service(conversation_id)

    
@bp.route('/terms/<conversation_id>', methods=['POST'])
@require_authorization
async def save_important_terms(conversation_id):
    return await save_important_terms_service(conversation_id)
    

@bp.route('/classes-and-properties', methods=['POST'])
@require_authorization
async def generate_classes_and_properties():
    return await generate_classes_and_properties_service()


@bp.route('/facets-of-propeties', methods=['POST'])
@require_authorization  
async def generate_facets_of_properties():
    return await generate_facets_of_properties_service()


@bp.route('/instances-of-classes', methods=['POST'])
@require_authorization 
async def generate_instances_of_classes():
    return await generate_instances_of_classes_service()
