from app.database import close_pool_connection, get_pool_connection, logger


def create_conversation(conversation_id, user_id, domain, scope):
    conn = get_pool_connection()
    try:
        logger.info(f"creating conversation with id: {conversation_id}")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO conversations (conversation_id, user_id, domain, scope)
                VALUES (%s, %s, %s, %s)
                RETURNING *;
            ''', (conversation_id, user_id, domain, scope))
            convo = cur.fetchone()
            conn.commit()
            return convo
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_conversation_detail_by_id(convo_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching conversation detail by id")
        with conn.cursor() as cur:
            cur.execute('''
                SELECT 
                    c.domain, 
                    c.scope, 
                    c.user_id, 
                    c.is_active,
                    c.conversation_id,
                    JSON_AGG(message_store.message) AS messages
                FROM conversations c
                LEFT JOIN message_store ON c.conversation_id = CAST(message_store.session_id AS UUID)
                WHERE c.conversation_id = %s AND c.deleted_at IS NULL
                GROUP BY c.domain, c.scope, c.user_id, c.is_active, c.id;
            ''', (convo_id,))
            convo = cur.fetchone()
            return convo
    except Exception as e:
        logger.error(f"Error fetching conversation detail by id: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_all_conversations_from_a_user(user_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching conversations from a user")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT conversation_id, title, domain, scope, is_active, created_at FROM conversations WHERE user_id = %s AND deleted_at IS NULL', (user_id,))
            convos = cur.fetchall()
            return convos
    except Exception as e:
        logger.error(f"Error fetching conversations from a user: {e}")
        return None
    finally:
        close_pool_connection(conn)


def update_conversation(title, convo_id, domain, scope, is_active):
    conn = get_pool_connection()
    try:
        logger.info("updating a conversation")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE conversations
                SET title = %s, domain = %s, scope = %s, is_active = %s, updated_at = CURRENT_TIMESTAMP
                WHERE conversation_id = %s
                RETURNING *;
            ''', (title, domain, scope, is_active, convo_id))
            convo = cur.fetchone()
            conn.commit()
            return convo
    except Exception as e:
        logger.error(f"Error updating conversation: {e}")
        return None
    finally:
        close_pool_connection(conn)


def delete_conversation(conversation_id):
    conn = get_pool_connection()
    try:
        logger.info("deleting a conversation")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE conversations 
                SET deleted_at = CURRENT_TIMESTAMP
                SET is_active = FALSE
                WHERE conversation_id = %s; 
            ''', (conversation_id,))
            conn.commit()
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        return None
    finally:
        close_pool_connection(conn)
