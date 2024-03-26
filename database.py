import psycopg2, psycopg2.pool, psycopg2.extras
import os

from dotenv import load_dotenv

load_dotenv()

pool = psycopg2.pool.ThreadedConnectionPool(
    1, 20,
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    host=os.environ.get('DB_HOST'),
    port=os.environ.get('DB_PORT'),
    database=os.environ.get('DB_NAME'),
    cursor_factory=psycopg2.extras.RealDictCursor
)

print(pool)

def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
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
                    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
                    domain VARCHAR(100) NOT NULL,
                    scope VARCHAR(100) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            cur.execute('''
                CREATE TABLE IF NOT EXISTS competency_questions (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(user_id) ON DELETE SET NULL,
                    convo_id INT REFERENCES conversations(id) ON DELETE SET NULL,
                    question VARCHAR(500) NOT NULL,
                    is_valid BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    validated_at TIMESTAMP,
                    deleted_at TIMESTAMP
                );
            ''')

            conn.commit()
    finally:
        close_connection(conn)

        
"""connections"""
def get_connection():
    return pool.getconn()

def close_connection(conn):
    conn.close()

def close_pool():
    pool.closeall()


"""users"""
def create_user(name, email, profile_pic_url):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO users (name, email, profile_pic_url)
                VALUES (%s, %s, %s)
                RETURNING *;
            ''', (name, email, profile_pic_url))
            user = cur.fetchone()
            conn.commit()
            return user
    except psycopg2.errors.UniqueViolation:
        return get_user_by_email(email)
    finally:
        close_connection(conn)

def get_user_by_email(email):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cur.fetchone()
            return user
    except: 
        return None
    finally:
        close_connection(conn)


"""conversations"""
def create_conversation(user_id, domain, scope):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO conversations (user_id, domain, scope)
                VALUES (%s, %s, %s)
                RETURNING *;
            ''', (user_id, domain, scope))
            convo = cur.fetchone()
            conn.commit()
            return convo
    except: 
        return None
    finally:
        close_connection(conn)

def get_conversation_by_id(convo_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM conversations WHERE id = %s', (convo_id,))
            convo = cur.fetchone()
            return convo
    finally:
        close_connection(conn)

def get_conversations_by_user_id(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM conversations WHERE user_id = %s', (user_id,))
            convos = cur.fetchall()
            return convos
    except: 
        return None
    finally:
        close_connection(conn)

def update_conversation(convo_id, domain, scope, is_active):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE conversations
                SET domain = %s, scope = %s, is_active = %s
                WHERE id = %s
                RETURNING *;
            ''', (domain, scope, is_active, convo_id))
            convo = cur.fetchone()
            conn.commit()
            return convo
    except: 
        return None
    finally:
        close_connection(conn)

"""competency questions"""
def create_competency_question(user_id, convo_id, question):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO competency_questions (user_id, convo_id, question)
                VALUES (%s, %s, %s)
                RETURNING *;
            ''', (user_id, convo_id, question))
            cq = cur.fetchone()
            conn.commit()
            return cq
    except: 
        return None
    finally:
        close_connection(conn)

def get_competency_questions_by_convo_id(convo_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM competency_questions WHERE convo_id = %s', (convo_id,))
            cqs = cur.fetchall()
            return cqs
    except: 
        return None
    finally:
        close_connection(conn)

def update_competency_question(cq_id, is_valid):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE competency_questions
                SET is_valid = %s
                WHERE id = %s
                RETURNING *;
            ''', (is_valid, cq_id))
            cq = cur.fetchone()
            conn.commit()
            return cq
    except: 
        return None
    finally:
        close_connection(conn)
