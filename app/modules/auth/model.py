from app.database import close_pool_connection, get_pool_connection, logger


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
        close_pool_connection(conn)


def get_user_by_email(email):
    conn = get_pool_connection()
    try:
        logger.info("fetching user by email")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT user_id, name, email, profile_pic_url, created_at FROM users WHERE email = %s AND deleted_at IS NULL',
                (email,
                 ))
            user = cur.fetchone()
            return user
    except Exception as e:
        logger.error(f"Error fetching user by email: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_user_by_id(user_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching user by email")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT user_id, name, email, profile_pic_url, created_at FROM users WHERE user_id = %s AND deleted_at IS NULL',
                (user_id,
                 ))
            user = cur.fetchone()
            return user
    except Exception as e:
        logger.error(f"Error fetching user by user_id: {e}")
        return None
    finally:
        close_pool_connection(conn)
