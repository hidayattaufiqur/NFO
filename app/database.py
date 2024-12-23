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

# TODO: Change db_name retrieval to use environment variables
connection_string = f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PASSWORD')}@localhost/nfo"


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
                CREATE TABLE IF NOT EXISTS instances (
                    id SERIAL PRIMARY KEY,
                    instance_id UUID NOT NULL UNIQUE,
                    class_id UUID REFERENCES classes(class_id) ON DELETE SET NULL,
                    name VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS classes_instances_junction (
                    id SERIAL PRIMARY KEY,
                    class_id UUID REFERENCES classes(class_id),
                    instance_id UUID REFERENCES instances(instance_id),
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
    # psycopg is needed for PostgresChatMessageHistory.create_tables() on
    # chat_agent.py
    return psycopg.connect(connection_string)


def get_pool_connection():
    logger.info("establishing pool connection")
    if "conn" not in g:
        g.conn = pool.getconn()
    return g.conn  # return conn object from flask.g namespace for better efficiency


def close_pool_connection(conn):
    logger.info("closing db connection")
    conn = g.pop('conn', None)
    if conn is not None:
        pool.putconn(conn)


def close_all_pool_connection():
    logger.info("closing db pool connection")
    pool.closeall()
