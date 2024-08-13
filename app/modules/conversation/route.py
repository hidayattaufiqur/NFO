from flask import Blueprint
from app.utils import require_authorization

from .service import *

bp = Blueprint('conversations', __name__, url_prefix='/conversations')


@bp.route('', methods=['POST'])
@bp.route('/<conversation_id>', methods=['POST'])
@require_authorization
async def conversation(conversation_id=None):
    return await conversation_service(conversation_id)


@bp.route('/<conversation_id>', methods=['GET'])
@require_authorization
def get_detail_conversation(conversation_id):
    return get_detail_conversation_service(conversation_id)


@bp.route('/users/<user_id>', methods=['GET'])
@require_authorization
def get_all_conversations_by_user_id(user_id):
    return get_all_conversations_by_user_id_service(user_id)


@bp.route('/<conversation_id>', methods=['DELETE'])
@require_authorization
def delete_conversation(conversation_id):
    return delete_conversation_service(conversation_id)


@bp.route('/competency-questions/<conversation_id>', methods=['POST'])
@require_authorization
# will update instead if there's already a CQ with the same ID
def save_competency_questions(conversation_id):
    return save_competency_questions_service(conversation_id)


@bp.route('/competency-questions/<conversation_id>', methods=['GET'])
@require_authorization
def get_competency_questions(conversation_id):
    return get_competency_questions_service(conversation_id)


@bp.route('/competency_questions/validate/<cq_id>', methods=['GET'])
@require_authorization
def validating_competency_questions(cq_id):
    return validating_competency_questions_service(cq_id)
