import psycopg, psycopg2, psycopg2.pool, psycopg2.extras
import os
import logging

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

psycopg2.extras.register_uuid()
logger.info("UUID extras has been registered on psycopg2")

pool = psycopg2.pool.ThreadedConnectionPool(
    1, 20,
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    host=os.environ.get('DB_HOST'),
    port=os.environ.get('DB_PORT'),
    database=os.environ.get('DB_NAME'),
    cursor_factory=psycopg2.extras.RealDictCursor
)

connection_string=f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@localhost/postgres" # TODO: Add the connection string to the .env file 

def init_db():
    conn = get_pool_connection()
    try:
        logger.info(f"initializing database")
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id UUID NOT NULL UNIQUE,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    profile_pic_url VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    conversation_id UUID NOT NULL UNIQUE,
                    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
                    title varchar(255),
                    domain VARCHAR(255) NOT NULL,
                    scope VARCHAR(255) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS competency_questions (
                    id SERIAL PRIMARY KEY,
                    cq_id UUID NOT NULL UNIQUE,
                    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
                    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL,
                    question VARCHAR(500) NOT NULL,
                    is_valid BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    validated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            logger.info(f"database initialized")
            conn.commit()
    finally:
        close_connection(conn)

        
"""db connections"""
def get_connection(): 
    logger.info("establishing psycopg connection")
    return psycopg.connect(connection_string)

def get_pool_connection():
    logger.info("establishing pool connection")
    return pool.getconn()

def close_connection(conn):
    logger.info("closing db connection")
    conn.close()

def close_pool():
    logger.info("closing db pool connection")
    pool.closeall()


"""users"""
def create_user(user_id, name, email, profile_pic_url):
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO users (user_id, name, email, profile_pic_url)
                VALUES (%s, %s, %s, %s)
                RETURNING *;
            ''', (user_id, name, email, profile_pic_url))
            user = cur.fetchone()
            conn.commit()
            return user
    except psycopg2.errors.UniqueViolation:
        return get_user_by_email(email)
    finally:
        close_connection(conn)

def get_user_by_email(email):
    conn = get_pool_connection()
    try:
        logger.info(f"fetching user by email")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE email = %s AND deleted_at IS NULL', (email,))
            user = cur.fetchone()
            return user
    except Exception as e: 
        logger.error(f"{e}")
        return None
    finally:
        close_connection(conn)


"""conversations"""
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
        logger.error(f"{e}")
        return None
    finally:
        close_connection(conn)

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
                JOIN message_store ON c.conversation_id = CAST(message_store.session_id AS UUID)
                WHERE c.conversation_id = %s AND deleted_at IS NULL
                GROUP BY c.domain, c.scope, c.user_id, c.is_active, c.id;
            ''', (convo_id,))
            convo = cur.fetchone()
            return convo
    except Exception as e: 
        logger.error(f"{e}")
        return None
    finally:
        close_connection(conn)

def get_all_conversations_from_a_user(user_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching conversations from a user")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM conversations WHERE user_id = %s AND deleted_at IS NULL', (user_id,))
            convos = cur.fetchall()
            return convos
    except Exception as e: 
        logger.error(f"{e}")
        return None
    finally:
        close_connection(conn)

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
        logger.error(f"{e}")
        return None
    finally:
        close_connection(conn)

def delete_conversation(conversation_id):
    conn = get_pool_connection()
    try: 
        logger.info("deleting a conversation")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE conversations 
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE conversation_id = %s; 
            ''', (conversation_id, ))
            conn.commit()
    except Exception as e: 
        logger.error(f"{e}")
        return None
    finally: 
        close_connection(conn)

"""competency questions"""
def create_competency_question(cq_id, user_id, convo_id, question):
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO competency_questions (cq_id, user_id, conversation_id, question)
                VALUES (%s, %s, %s, %s)
                RETURNING *;
            ''', (cq_id, user_id, convo_id, question))
            cq = cur.fetchone()
            conn.commit()
            return cq
    except: 
        return None
    finally:
        close_connection(conn)

def get_all_competency_questions_by_convo_id(convo_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching competency_questions from a conversation")
        with conn.cursor() as cur:
            cur.execute('SELECT id, is_valid, question, user_id FROM competency_questions WHERE conversation_id = %s AND deleted_at IS NULL', (convo_id,))
            cqs = cur.fetchall()
            return cqs
    except Exception as e: 
        logger.error(f"{e}")
        return None
    finally:
        close_connection(conn)

def validating_competency_question(cq_id, is_valid):
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE competency_questions
                SET is_valid = %s, updated_at = CURRENT_TIMESTAMP, validated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING *;
            ''', (is_valid, cq_id))
            cq = cur.fetchone()
            conn.commit()
            return cq
    except Exception as e: 
        logger.error(f"{e}")
        return None
    finally:
        close_connection(conn)
