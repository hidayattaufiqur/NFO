from flask import Blueprint

from .service import *

bp = Blueprint('conversation', __name__, url_prefix='/conversation')

@bp.route('', methods=['POST'])
@bp.route('/<conversation_id>', methods=['POST'])
async def conversation(conversation_id=None):
    return await conversation_service(conversation_id)


@bp.route('/<conversation_id>', methods=['GET'])
def get_detail_conversation(conversation_id):
    return get_detail_conversation_service(conversation_id)


@bp.route('/all/<user_id>', methods=['GET'])
def get_all_conversations_by_user_id(user_id):
    return get_all_conversations_by_user_id_service(user_id)


@bp.route('/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    return delete_conversation_service(conversation_id)


@bp.route('/competency_questions/<conversation_id>', methods=['POST'])
def save_competency_questions(conversation_id):
    return save_competency_questions_service(conversation_id)


@bp.route('/competency_questions/<conversation_id>', methods=['GET'])
def get_competency_questions(conversation_id):
    return get_competency_questions_service(conversation_id)


@bp.route('/competency_questions/validate/<cq_id>', methods=['GET'])
def validating_competency_questions(cq_id):
    return validating_competency_questions_service(cq_id)
