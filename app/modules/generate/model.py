from app.database import close_pool_connection, get_pool_connection, logger

def create_important_terms(important_terms_id, user_id, convo_id, terms):
    conn = get_pool_connection()
    try:
        logger.info("creating important terms")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO important_terms (important_terms_id, user_id, conversation_id, terms)
                VALUES (%s, %s, %s, %s)
                RETURNING *;
            ''', (important_terms_id, user_id, convo_id, terms))
            terms = cur.fetchone()
            conn.commit()
            return terms
    except Exception as e:
        logger.error(f"Error creating important terms: {e}")
        return None
    finally:
        close_pool_connection(conn)

def update_important_terms(important_terms_id, terms):
    conn = get_pool_connection()
    try:
        logger.info("updating important terms")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE important_terms SET terms = %s, updated_at = CURRENT_TIMESTAMP WHERE important_terms_id = %s
                RETURNING *;
            ''', (terms, important_terms_id))
            terms = cur.fetchone()
            conn.commit()
            return terms
    except Exception as e:
        logger.error(f"Error updating important terms: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_important_terms_by_id(important_terms_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching important terms by id")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM important_terms WHERE important_terms_id = %s AND deleted_at IS NULL', (important_terms_id,))
            terms = cur.fetchone()
            return terms
    except Exception as e:
        logger.error(f"Error fetching important terms by id: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_important_terms_by_conversation_id(convo_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching important terms by conversation id")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM important_terms WHERE conversation_id = %s AND deleted_at IS NULL', (convo_id,))
            terms = cur.fetchall()
            return terms
    except Exception as e:
        logger.error(f"Error fetching important terms by conversation id: {e}")
        return None
    finally:
        close_pool_connection(conn)
