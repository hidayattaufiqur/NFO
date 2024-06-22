from langchain_community.chat_message_histories.sql import SQLChatMessageHistory
from flask import current_app, g

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

connection_string = f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@localhost/postgres"

def init_db(app):
    global pool
    pool = psycopg2.pool.ThreadedConnectionPool(
        1, 20,
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        host=os.environ.get('DB_HOST'),
        port=os.environ.get('DB_PORT'),
        database=os.environ.get('DB_NAME'),
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    app.teardown_appcontext(close_pool_connection)
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
                CREATE TABLE IF NOT EXISTS classes (
                    id SERIAL PRIMARY KEY,
                    class_id UUID NOT NULL UNIQUE,
                    conversation_id UUID REFERENCES conversations(conversation_id) ON DELETE SET NULL,
                    name VARCHAR(100),
                    description TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS data_properties (
                    id SERIAL PRIMARY KEY,
                    data_property_id UUID NOT NULL UNIQUE,
                    class_id UUID REFERENCES classes(class_id) ON DELETE SET NULL,
                    name VARCHAR(100),
                    data_type VARCHAR(50),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS object_properties (
                    id SERIAL PRIMARY KEY,
                    object_property_id UUID NOT NULL UNIQUE,
                    class_id UUID REFERENCES classes(class_id) ON DELETE SET NULL,
                    name VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS domains (
                    id SERIAL PRIMARY KEY,
                    domain_id UUID NOT NULL UNIQUE,
                    object_property_id UUID REFERENCES object_properties(object_property_id) ON DELETE SET NULL,
                    name VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS ranges (
                    id SERIAL PRIMARY KEY,
                    range_id UUID NOT NULL UNIQUE,
                    object_property_id UUID REFERENCES object_properties(object_property_id) ON DELETE SET NULL,
                    name VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS classes_data_junction (
                    id SERIAL PRIMARY KEY,
                    class_id UUID REFERENCES classes(class_id),
                    data_property_id UUID REFERENCES data_properties(data_property_id),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                ); 
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS classes_object_junction (
                    id SERIAL PRIMARY KEY,
                    class_id UUID REFERENCES classes(class_id),
                    object_property_id UUID REFERENCES object_properties(object_property_id),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                ); 
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS domains_ranges_junction (
                    id SERIAL PRIMARY KEY,
                    object_property_id UUID REFERENCES object_properties(object_property_id) ON DELETE SET NULL,
                    domain_id UUID REFERENCES domains(domain_id) ON DELETE SET NULL,
                    range_id UUID REFERENCES ranges(range_id) ON DELETE SET NULL,
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
                CREATE INDEX IF NOT EXISTS idx_important_terms_conversation_id ON important_terms(user_id);

                CREATE INDEX IF NOT EXISTS idx_classes_class_id ON classes(class_id);
                CREATE INDEX IF NOT EXISTS idx_classes_conversation_id ON classes(conversation_id);

                CREATE INDEX IF NOT EXISTS idx_data_properties_data_property_id ON data_properties(data_property_id);
                CREATE INDEX IF NOT EXISTS idx_data_properties_class_id ON data_properties(class_id);

                CREATE INDEX IF NOT EXISTS idx_object_properties_object_property_id ON object_properties(object_property_id);
                CREATE INDEX IF NOT EXISTS idx_object_properties_object_class_id ON object_properties(class_id);

                CREATE INDEX IF NOT EXISTS idx_domains_domain_id ON domains(domain_id);
                CREATE INDEX IF NOT EXISTS idx_domains_object_property_id ON domains(object_property_id);

                CREATE INDEX IF NOT EXISTS idx_ranges_range_id ON ranges(range_id);
                CREATE INDEX IF NOT EXISTS idx_ranges_object_property_id ON ranges(object_property_id);

                CREATE INDEX IF NOT EXISTS idx_domains_ranges_junction_object_property_id ON domains_ranges_junction(object_property_id);
                CREATE INDEX IF NOT EXISTS idx_domains_ranges_junction_domain_id ON domains_ranges_junction(domain_id);
                CREATE INDEX IF NOT EXISTS idx_domains_ranges_junction_range_id ON domains_ranges_junction(range_id);

                CREATE INDEX IF NOT EXISTS idx_classes_data_junction_class_id ON classes_data_junction(class_id);
                CREATE INDEX IF NOT EXISTS idx_classes_object_junction_class_id ON classes_object_junction(class_id);
            ''')

            logger.info("database initialized")
            conn.commit()
    finally:
        close_pool_connection(conn)


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
    if "conn" not in g: 
        g.conn = pool.getconn()  
    return g.conn # return conn object from flask.g namespace for better efficiency

def close_pool_connection(conn):
    logger.info("closing db connection")
    conn = g.pop('conn', None)
    if conn is not None:
        pool.putconn(conn)
        
def close_all_pool_connection():
    logger.info("closing db pool connection")
    pool.closeall()


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
            cur.execute('SELECT conversation_id, title, domain, scope, is_active, created_at FROM conversations WHERE user_id = %s AND deleted_at IS NULL', (user_id,))
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
        close_pool_connection(conn)

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
        close_pool_connection(conn)

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
        close_pool_connection(conn)


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
        close_pool_connection(conn)

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
        close_pool_connection(conn)

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
        close_pool_connection(conn)


"""classes"""
def create_class(class_id, convo_id, name, desc=""):
    conn = get_pool_connection()
    try: 
        logger.info("inserting class into database")
        with conn.cursor() as cur: 
            cur.execute('''
                INSERT INTO classes (class_id, conversation_id, name, description)
                VALUES (%s, %s, %s, %s)
                RETURNING *;
            ''', (class_id, convo_id, name, desc))
            classes = cur.fetchone()
            conn.commit()
            return classes 
    except Exception as e:
        logger.error(f"Error inserting a class: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_class_by_id(class_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching class by id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM classes WHERE class_id = %s AND deleted_at IS NULL', (class_id,))
            classes = cur.fetchone()
            return classes
    except Exception as e:
        logger.error(f"Error fetching class by id: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_class_by_name(name):
    conn = get_pool_connection()
    try:
        logger.info("fetching class by name")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM classes WHERE name = %s AND deleted_at IS NULL', (name,))
            name = cur.fetchone()
            return name 
    except Exception as e:
        logger.error(f"Error fetching class by name: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_all_classes_by_conversation_id(convo_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching classes by conversation id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM classes WHERE conversation_id = %s AND deleted_at IS NULL', (convo_id,))
            classes = cur.fetchall()
            return classes 
    except Exception as e:
        logger.error(f"Error fetching classes by conversation id: {e}")
        return None
    finally:
        close_pool_connection(conn)


"""data properties"""
def create_data_property(data_property_id, class_id, name, data_type):
    conn = get_pool_connection()
    try:
        logger.info("inserting data property into database")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO data_properties (data_property_id, class_id, name, data_type)
                VALUES (%s, %s, %s, %s)
                RETURNING *;
            ''', (data_property_id, class_id, name, data_type))
            data_property = cur.fetchone()
            conn.commit()
            return data_property
    except Exception as e:
        logger.error(f"Error inserting a data property: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_data_property_by_id(data_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching data property by id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM data_properties WHERE data_property_id = %s AND deleted_at IS NULL', (data_property_id,))
            data_property = cur.fetchone()
            return data_property
    except Exception as e:
        logger.error(f"Error fetching data property by id: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_data_property_by_name(name):
    conn = get_pool_connection()
    try:
        logger.info("fetching data property by name")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM data_properties WHERE name = %s AND deleted_at IS NULL', (name,))
            data_property = cur.fetchone()
            return data_property
    except Exception as e:
        logger.error(f"Error fetching data property by name: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_all_data_properties_by_class_id(class_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching data properties by class id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM data_properties WHERE class_id = %s AND deleted_at IS NULL', (class_id,))
            data_properties = cur.fetchall()
            return data_properties
    except Exception as e:
        logger.error(f"Error fetching data properties by class id: {e}")
        return None
    finally:
        close_pool_connection(conn)


"""object properties"""
def create_object_property(object_property_id, class_id, name):
    conn = get_pool_connection()
    try:
        logger.info("inserting object property into database")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO object_properties (object_property_id, class_id, name)
                VALUES (%s, %s, %s)
                RETURNING *;
            ''', (object_property_id, class_id, name))
            object_property = cur.fetchone()
            conn.commit()
            return object_property
    except Exception as e:
        logger.error(f"Error inserting an object property: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_object_property_by_id(object_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching object property by id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM object_properties WHERE object_property_id = %s AND deleted_at IS NULL', (object_property_id,))
            object_property = cur.fetchone()
            return object_property
    except Exception as e:
        logger.error(f"Error fetching object property by id: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_object_property_by_name(name):
    conn = get_pool_connection()
    try:
        logger.info("fetching object property by name")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM object_properties WHERE name = %s AND deleted_at IS NULL', (name,))
            object_property = cur.fetchone()
            return object_property
    except Exception as e:
        logger.error(f"Error fetching object property by name: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_all_object_properties_by_domain_id(domain_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching object properties by domain id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM object_properties WHERE domain_id = %s AND deleted_at IS NULL', (domain_id,))
            object_properties = cur.fetchall()
            return object_properties
    except Exception as e:
        logger.error(f"Error fetching object properties by domain id: {e}")
        return None
    finally:
        close_pool_connection(conn)


"""classes data junction"""
# TODO: create classes data junction 
# TODO: consider create this function in upper layer and not in database.py
def create_classes_data_junction(class_id, data_property_id):
    conn = get_pool_connection()
    try:
        logger.info("inserting classes data junction into database")

        # logger.info("checking if class exists")
        # data = get_class_by_name(name) 
        # if data:
        #     class_id = _class['class_id']
        # else:
        #     _class = create_class(class_id, convo_id, name, desc)
        #     class_id = _class['class_id']

        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO classes_data_junction (class_id, data_property_id)
                VALUES (%s, %s)
                RETURNING *;
            ''', (class_id, data_property_id))
            classes_data_junction = cur.fetchone()
            conn.commit()
            return classes_data_junction
    except Exception as e:
        logger.error(f"Error inserting classes data junction: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_classes_data_junction_by_class_id(class_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching classes data junction by class id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM classes_data_junction WHERE class_id = %s AND deleted_at IS NULL', (class_id,))
            classes_data_junction = cur.fetchall()
            return classes_data_junction
    except Exception as e:
        logger.error(f"Error fetching classes data junction by class id: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_classes_data_junction_by_data_property_id(data_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching classes data junction by data property id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM classes_data_junction WHERE data_property_id = %s AND deleted_at IS NULL', (data_property_id,))
            classes_data_junction = cur.fetchall()
            return classes_data_junction
    except Exception as e:
        logger.error(f"Error fetching classes data junction by data property id: {e}")
        return None
    finally:
        close_pool_connection(conn)


"""classes object junction"""
def create_classes_object_junction(class_id, object_property_id):
    conn = get_pool_connection()
    try:
        logger.info("inserting classes object junction into database")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO classes_object_junction (class_id, object_property_id)
                VALUES (%s, %s)
                RETURNING *;
            ''', (class_id, object_property_id))
            classes_object_junction = cur.fetchone()
            conn.commit()
            return classes_object_junction
    except Exception as e:
        logger.error(f"Error inserting classes object junction: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_classes_object_junction_by_class_id(class_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching classes object junction by class id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM classes_object_junction WHERE class_id = %s AND deleted_at IS NULL', (class_id,))
            classes_object_junction = cur.fetchall()
            return classes_object_junction
    except Exception as e:
        logger.error(f"Error fetching classes object junction by class id: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_classes_object_junction_by_object_property_id(object_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching classes object junction by object property id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM classes_object_junction WHERE object_property_id = %s AND deleted_at IS NULL', (object_property_id,))
            classes_object_junction = cur.fetchall()
            return classes_object_junction
    except Exception as e:
        logger.error(f"Error fetching classes object junction by object property id: {e}")
        return None
    finally:
        close_pool_connection(conn)

"""domains"""
def create_domain(domain_id, object_property_id, name):
    conn = get_pool_connection()
    try:
        logger.info("inserting domain into database")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO domains (domain_id, object_property_id, name)
                VALUES (%s, %s, %s)
                RETURNING *;
            ''', (domain_id, object_property_id, name))
            domain = cur.fetchone()
            conn.commit()
            return domain
    except Exception as e:
        logger.error(f"Error inserting a domain: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_domain_by_id(domain_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching domain by id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM domains WHERE domain_id = %s AND deleted_at IS NULL', (domain_id,))
            domain = cur.fetchone()
            return domain
    except Exception as e:
        logger.error(f"Error fetching domain by id: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_domain_by_name(name):
    conn = get_pool_connection()
    try:
        logger.info("fetching domain by name")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM domains WHERE name = %s AND deleted_at IS NULL', (name,))
            domain = cur.fetchone()
            return domain
    except Exception as e:
        logger.error(f"Error fetching domain by name: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_all_domains_by_object_property_id(object_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching domains by object property id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM domains WHERE object_property_id = %s AND deleted_at IS NULL', (object_property_id,))
            domains = cur.fetchall()
            return domains
    except Exception as e:
        logger.error(f"Error fetching domains by object property id: {e}")
        return None
    finally:
        close_pool_connection(conn)


"""ranges"""
def create_range(range_id, object_property_id, name):
    conn = get_pool_connection()
    try:
        logger.info("inserting range into database")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO ranges (range_id, object_property_id, name)
                VALUES (%s, %s, %s)
                RETURNING *;
            ''', (range_id, object_property_id, name))
            range = cur.fetchone()
            conn.commit()
            return range
    except Exception as e:
        logger.error(f"Error inserting a range: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_range_by_id(range_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching range by id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM ranges WHERE range_id = %s AND deleted_at IS NULL', (range_id,))
            range = cur.fetchone()
            return range
    except Exception as e:
        logger.error(f"Error fetching range by id: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_range_by_name(name):
    conn = get_pool_connection()
    try:
        logger.info("fetching range by name")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM ranges WHERE name = %s AND deleted_at IS NULL', (name,))
            range = cur.fetchone()
            return range
    except Exception as e:
        logger.error(f"Error fetching range by name: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_all_ranges_by_object_property_id(object_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching ranges by object property id")
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM ranges WHERE object_property_id = %s AND deleted_at IS NULL', (object_property_id,))
            ranges = cur.fetchall()
            return ranges
    except Exception as e:
        logger.error(f"Error fetching ranges by object property id: {e}")
        return None
