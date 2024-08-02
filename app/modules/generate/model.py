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


"""classes"""
def create_classes_data_junction(class_id, data_property_id):
    conn = get_pool_connection()
    try:
        logger.info("inserting classes data junction into database")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO classes_data_junction (class_id, data_property_id)
                VALUES (%s, %s)
                RETURNING *;
            ''', (class_id, data_property_id))
            junction = cur.fetchone()
            conn.commit()
            return junction
    except Exception as e:
        logger.error(f"Error inserting classes data junction: {e}")
        return None
    finally:
        close_pool_connection(conn)


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
            junction = cur.fetchone()
            conn.commit()
            return junction
    except Exception as e:
        logger.error(f"Error inserting classes object junction: {e}")
        return None
    finally:
        close_pool_connection(conn)


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
        

def update_class(class_id, name):
    conn = get_pool_connection()
    try:
        logger.info("updating class")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE classes SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE class_id = %s
                RETURNING *;
            ''', (name, class_id))
            classes = cur.fetchone()
            conn.commit()
            return classes
    except Exception as e:
        logger.error(f"Error updating class: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_class_by_id(class_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching class by id")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM classes WHERE class_id = %s AND deleted_at IS NULL', (class_id,))
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
            cur.execute(
                'SELECT * FROM classes WHERE name = %s AND deleted_at IS NULL', (name,))
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
            cur.execute(
                'SELECT * FROM classes WHERE conversation_id = %s AND deleted_at IS NULL', (convo_id,))
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


def update_data_property(data_property_id, name, data_type):
    conn = get_pool_connection()
    try:
        logger.info("updating data property")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE data_properties SET name = %s, data_type = %s, updated_at = CURRENT_TIMESTAMP WHERE data_property_id = %s
                RETURNING *;
            ''', (name, data_type, data_property_id))
            data_property = cur.fetchone()
            conn.commit()
            return data_property
    except Exception as e:
        logger.error(f"Error updating data property: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_data_property_by_id(data_property_id):
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM data_properties WHERE data_property_id = %s AND deleted_at IS NULL', (data_property_id,))
            data_property = cur.fetchone()
            return data_property
    except Exception as e:
        logger.error(f"Error fetching data property by id: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_all_data_properties_by_class_id(class_id):
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT dp.data_property_id, dp.name, dp.data_type, c.name as class_name, dp.created_at
                FROM data_properties dp
                JOIN classes_data_junction cdj ON dp.data_property_id = cdj.data_property_id
                JOIN classes c ON cdj.class_id = c.class_id
                WHERE c.class_id = %s AND dp.deleted_at IS NULL
            ''', (class_id,))
            data_properties = cur.fetchall()
            return data_properties
    except Exception as e:
        logger.error(f"Error fetching data properties by conversation id: {e}")
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

def update_object_property(object_property_id, name):
    conn = get_pool_connection()
    try:
        logger.info("updating object property")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE object_properties SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE object_property_id = %s
                RETURNING *;
            ''', (name, object_property_id))
            object_property = cur.fetchone()
            conn.commit()
            return object_property
    except Exception as e:
        logger.error(f"Error updating object property: {e}")
        return None
    finally:
        close_pool_connection(conn)

def get_object_property_by_id(object_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching object property by id")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM object_properties WHERE object_property_id = %s AND deleted_at IS NULL', (object_property_id,))
            object_property = cur.fetchone()
            return object_property
    except Exception as e:
        logger.error(f"Error fetching object property by id: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_all_object_properties_by_class_id(class_id):
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    c.name as class_name,
                    op.object_property_id,
                    op.name AS object_property,
                    op.created_at,
                    json_agg(DISTINCT jsonb_build_object(
                        'domain_id', d.domain_id,
                        'domain_name', d.name
                    )) AS domains,
                    json_agg(DISTINCT jsonb_build_object(
                        'range_id', r.range_id,
                        'range_name', r.name
                    )) AS ranges
                FROM object_properties op
                JOIN classes_object_junction coj ON op.object_property_id = coj.object_property_id
                JOIN classes c ON coj.class_id = c.class_id
                LEFT JOIN domains_ranges_junction drj ON op.object_property_id = drj.object_property_id
                LEFT JOIN domains d ON drj.domain_id = d.domain_id
                LEFT JOIN ranges r ON drj.range_id = r.range_id
                WHERE c.class_id = %s AND op.deleted_at IS NULL
                GROUP BY op.object_property_id, op.created_at, op.name, c.name
            ''', (class_id,))
            object_properties = cur.fetchall()
            return object_properties
    except Exception as e:
        logger.error(f"Error fetching object properties by conversation id: {e}")
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

def update_domain(domain_id, name):
    conn = get_pool_connection()
    try:
        logger.info("updating domain")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE domains SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE domain_id = %s
                RETURNING *;
            ''', (name, domain_id))
            domain = cur.fetchone()
            conn.commit()
            return domain
    except Exception as e:
        logger.error(f"Error updating domain: {e}")
        return None
    finally:
        close_pool_connection(conn)

        
def get_domain_by_id(domain_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching domain by id")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM domains WHERE domain_id = %s AND deleted_at IS NULL', (domain_id,))
            domain = cur.fetchone()
            return domain
    except Exception as e:
        logger.error(f"Error fetching domain by id: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_all_domains_by_object_property_id(object_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching domains by object property id")
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    op.object_property_id,
                    op.name AS object_property,
                    json_agg(DISTINCT jsonb_build_object(
                        'domain_id', d.domain_id,
                        'domain_name', d.name,
                        'created_at', d.created_at
                    )) AS domains
                FROM domains d
                JOIN domains_ranges_junction drj ON d.domain_id = drj.domain_id
                JOIN object_properties op ON drj.object_property_id = op.object_property_id
                WHERE op.object_property_id = %s AND op.deleted_at IS NULL
                GROUP BY op.object_property_id, op.name
            ''', (object_property_id,))
            domains = cur.fetchall()
            return domains
    except Exception as e:
        logger.error(f"Error fetching domains by object property id: {e}")
        return None
    finally:
        close_pool_connection(conn)


"""ranges"""
def create_domains_ranges_junction(object_property_id, domain_id, range_id):
    conn = get_pool_connection()
    try:
        logger.info("inserting domains ranges junction into database")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO domains_ranges_junction (object_property_id, domain_id, range_id)
                VALUES (%s, %s, %s)
                RETURNING *;
            ''', (object_property_id, domain_id, range_id))
            junction = cur.fetchone()
            conn.commit()
            return junction
    except Exception as e:
        logger.error(f"Error inserting domains ranges junction: {e}")
        return None
    finally:
        close_pool_connection(conn)


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


def update_range(range_id, name):
    conn = get_pool_connection()
    try:
        logger.info("updating range")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE ranges SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE range_id = %s
                RETURNING *;
            ''', (name, range_id))
            range = cur.fetchone()
            conn.commit()
            return range
    except Exception as e:
        logger.error(f"Error updating range: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_range_by_id(range_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching range by id")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM ranges WHERE range_id = %s AND deleted_at IS NULL', (range_id,))
            range = cur.fetchone()
            return range
    except Exception as e:
        logger.error(f"Error fetching range by id: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_all_ranges_by_object_property_id(object_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching ranges by object property id")
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    op.object_property_id,
                    op.name AS object_property,
                    json_agg(DISTINCT jsonb_build_object(
                        'range_id', r.range_id,
                        'range_name', r.name,
                        'created_at', r.created_at
                    )) AS ranges
                FROM ranges r
                JOIN domains_ranges_junction drj ON r.range_id = drj.range_id
                JOIN object_properties op ON drj.object_property_id = op.object_property_id
                WHERE op.object_property_id = %s AND op.deleted_at IS NULL
                GROUP BY op.object_property_id, op.name
            ''', (object_property_id,))
            ranges = cur.fetchall()
            return ranges
    except Exception as e:
        logger.error(f"Error fetching ranges by object property id: {e}")
        return None

def update_object_property_range(range_id, range_name):
    conn = get_pool_connection()
    try:
        logger.info("updating object property range")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE ranges SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE range_id = %s
                RETURNING *;
            ''', (range_name, range_id))
            range = cur.fetchone()
            conn.commit()
            return range
    except Exception as e:
        logger.error(f"Error updating object property range: {e}")
        return None
    finally:
        close_pool_connection(conn)
