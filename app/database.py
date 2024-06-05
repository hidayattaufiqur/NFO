from langchain_community.chat_message_histories.sql import SQLChatMessageHistory

import psycopg
import psycopg2
import psycopg2.pool
import psycopg2.extras
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

connection_string = f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@localhost/postgres"

def init_db():
    conn = get_pool_connection()
    try:
        logger.info("initializing database")
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
                    title VARCHAR(255),
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

            cur.execute('''
                CREATE TABLE IF NOT EXISTS important_terms (
                    id SERIAL PRIMARY KEY,
                    important_terms_id UUID NOT NULL UNIQUE,
                    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
                    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL,
                    terms VARCHAR(1000) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            cur.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_conversations_conversation_id ON conversations(conversation_id);
                CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
                CREATE INDEX IF NOT EXISTS idx_competency_questions_cq_id ON competency_questions(cq_id);
                CREATE INDEX IF NOT EXISTS idx_competency_questions_user_id ON competency_questions(user_id);
                CREATE INDEX IF NOT EXISTS idx_important_terms_important_terms_id ON important_terms(important_terms_id);
                CREATE INDEX IF NOT EXISTS idx_important_terms_user_id ON important_terms(user_id);
            ''')

            logger.info("database initialized")
            conn.commit()
    finally:
        close_connection(conn)

"""db connections"""
def get_chat_message_history_connection(table_name, session_id):
    logger.info("establishing SQLChatMessageHistory connection")
    history = SQLChatMessageHistory( 
        table_name=table_name,
        session_id=session_id,
        connection_string=connection_string
    )
    return history

def get_connection():
    logger.info("establishing psycopg connection")
    return psycopg.connect(connection_string) # psycopg is needed for PostgresChatMessageHistory.create_tables() on chat_agent.py

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
                ON CONFLICT (email) DO NOTHING
                RETURNING *;
            ''', (user_id, name, email, profile_pic_url))
            user = cur.fetchone()
            conn.commit()
            return user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None
    finally:
        close_connection(conn)

def get_user_by_email(email):
    conn = get_pool_connection()
    try:
        logger.info("fetching user by email")
        with conn.cursor() as cur:
            cur.execute('SELECT user_id, name, email, profile_pic_url, created_at FROM users WHERE email = %s AND deleted_at IS NULL', (email,))
            user = cur.fetchone()
            return user
    except Exception as e:
        logger.error(f"Error fetching user by email: {e}")
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
        logger.error(f"Error creating conversation: {e}")
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
        close_connection(conn)

def get_all_conversations_from_a_user(user_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching conversations from a user")
        with conn.cursor() as cur:
            cur.execute('SELECT conversation_id, title, domain, scope, is_active, created_at FROM conversations WHERE user_id = %s AND deleted_at IS NULL', (user_id,))
            convos = cur.fetchall()
            return convos
    except Exception as e:
        logger.error(f"Error fetching conversations from a user: {e}")
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
        logger.error(f"Error updating conversation: {e}")
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
                SET is_active = FALSE
                WHERE conversation_id = %s; 
            ''', (conversation_id,))
            conn.commit()
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
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
    except Exception as e:
        logger.error(f"Error creating competency question: {e}")
        return None
    finally:
        close_connection(conn)

def get_all_competency_questions_by_convo_id(convo_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching competency_questions from a conversation")
        with conn.cursor() as cur:
            cur.execute('SELECT cq_id, user_id, conversation_id, is_valid, question, created_at FROM competency_questions WHERE conversation_id = %s AND deleted_at IS NULL', (convo_id,))
            cqs = cur.fetchall()
            return cqs
    except Exception as e:
        logger.error(f"Error fetching competency questions by conversation id: {e}")
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
        logger.error(f"Error validating competency question: {e}")
        return None
    finally:
        close_connection(conn)


"""important terms"""
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
        close_connection(conn)

def get_important_terms_by_id(important_terms_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching important terms by id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM important_terms WHERE important_terms_id = %s AND deleted_at IS NULL', (important_terms_id,))
            terms = cur.fetchone()
            return terms
    except Exception as e:
        logger.error(f"Error fetching important terms by id: {e}")
        return None
    finally:
        close_connection(conn)

def get_important_terms_by_conversation_id(convo_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching important terms by conversation id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM important_terms WHERE conversation_id = %s AND deleted_at IS NULL', (convo_id,))
            terms = cur.fetchall()
            return terms
    except Exception as e:
        logger.error(f"Error fetching important terms by conversation id: {e}")
        return None
    finally:
        close_connection(conn)
