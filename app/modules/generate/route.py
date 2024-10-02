from flask import Blueprint
from app.utils import require_authorization

from .service import *

bp = Blueprint('generation', __name__, url_prefix='/generation')

"""important terms"""


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


"""classes and properties"""


@bp.route('/classes-and-properties/<conversation_id>', methods=['GET'])
@require_authorization
async def get_classes_and_properties(conversation_id):
    return await get_classes_and_properties_service(conversation_id)


@bp.route('/classes-and-properties/<conversation_id>', methods=['POST']) # obselete
@require_authorization
async def generate_classes_and_properties(conversation_id):
    return await generate_classes_and_properties_service(conversation_id)


@bp.route('/classes/<conversation_id>', methods=['GET'])
@require_authorization
async def get_classes(conversation_id):
    return await get_classes_service(conversation_id)


@bp.route('/classes/<conversation_id>', methods=['POST'])
@require_authorization
async def create_class(conversation_id):
    return await create_class_service(conversation_id)


@bp.route('/classes/<class_id>', methods=['PUT']) # obselete
@require_authorization
async def update_class(class_id):
    return await update_class_service(class_id)


@bp.route('/classes', methods=['DELETE'])
@require_authorization
async def delete_class():
    return await delete_class_service()


"""object properties"""


@bp.route('/object-properties/<class_id>', methods=['GET'])
@require_authorization
async def get_object_properties(class_id):
    return await get_object_properties_service(class_id)


@bp.route('/object-properties/<object_property_id>', methods=['PUT']) # obselete
@require_authorization
async def update_object_property(object_property_id):
    return await update_object_property_service(object_property_id)


@bp.route('/object-properties/<class_id>', methods=['POST'])
@require_authorization
async def create_object_property(class_id):
    return await create_object_property_service(class_id)


@bp.route('/object-properties/<class_id>', methods=['DELETE'])
@require_authorization
async def delete_object_properties(class_id):
    return await delete_object_properties_service(class_id)


@bp.route('/object-properties/<object_property_id>/domain-range',
          methods=['POST'])
@require_authorization
async def create_object_property_domain_range(object_property_id):
    return await create_object_property_domain_range_service(object_property_id)


"""ranges"""


@bp.route('/object-properties/<object_property_id>/range', methods=['GET'])
@require_authorization
async def get_object_property_range(object_property_id):
    return await get_object_property_range_service(object_property_id)


@bp.route('/object-properties/range/<range_id>', methods=['PUT'])
@require_authorization
async def update_object_property_range(range_id):
    return await update_object_property_range_service(range_id)


@bp.route('/object-properties/<object_property_id>/range', methods=['DELETE'])
@require_authorization
async def delete_object_property_range(object_property_id):
    return await delete_object_property_range_service(object_property_id)


"""domains"""


@bp.route('/object-properties/<object_property_id>/domain', methods=['GET'])
@require_authorization
async def get_object_property_domain(object_property_id):
    return await get_object_property_domain_service(object_property_id)


@bp.route('/object-properties/domain/<domain_id>', methods=['PUT'])
@require_authorization
async def update_object_property_domain(domain_id):
    return await update_object_property_domain_service(domain_id)


@bp.route('/object-properties/<object_property_id>/domain', methods=['DELETE'])
@require_authorization
async def delete_object_property_domain(object_property_id):
    return await delete_object_property_domain_service(object_property_id)


"""data properties"""


@bp.route('/data-properties/<class_id>', methods=['POST'])
@require_authorization
async def create_data_property(class_id):
    return await create_data_property_service(class_id)


@bp.route('/data-properties/<class_id>', methods=['GET'])
@require_authorization
async def get_data_properties(class_id):
    return await get_data_properties_service(class_id)


@bp.route('/data-properties/<data_property_id>', methods=['PUT']) # obselete
@require_authorization
async def update_data_property(data_property_id):
    return await update_data_property_service(data_property_id)


@bp.route('/data-properties/<class_id>', methods=['DELETE'])
@require_authorization
async def delete_data_properties(class_id):
    return await delete_data_properties_service(class_id)


"""instances"""


@bp.route('/instances-of-classes', methods=['POST'])
@require_authorization
async def generate_instances_of_classes():
    return await generate_instances_of_classes_service()


@bp.route('/classes/<conversation_id>/instance', methods=['GET'])
@require_authorization
async def get_instances(conversation_id):
    return await get_instances_service(conversation_id)


@bp.route('/classes/instance/<class_id>', methods=['POST'])
@require_authorization
async def update_instances(class_id):
    return await update_instances_service(class_id)


@bp.route('/classes/instance/<class_id>', methods=['DELETE'])
@require_authorization
async def delete_instances(class_id):
    return await delete_instances_service(class_id)


"""ontology"""


@bp.route('/ontology/<conversation_id>', methods=['GET'])
# @require_authorization
async def generate_owl_file(conversation_id):
    return await generate_owl_file_service(conversation_id)

# TODO: save the results to DB 
# FIX: fix potential error when parsing response from LLM 
@bp.route('/ontology/<conversation_id>/existing-ontologies', methods=['POST'])
# @require_authorization
async def get_existing_ontologies(conversation_id):
    return await get_existing_ontologies_service(conversation_id)
