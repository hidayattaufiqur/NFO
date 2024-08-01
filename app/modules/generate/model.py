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


def get_data_property_by_id(data_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching data property by id")
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


def get_data_property_by_name(name):
    conn = get_pool_connection()
    try:
        logger.info("fetching data property by name")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM data_properties WHERE name = %s AND deleted_at IS NULL', (name,))
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
            cur.execute(
                'SELECT * FROM data_properties WHERE class_id = %s AND deleted_at IS NULL', (class_id,))
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
            cur.execute(
                'SELECT * FROM object_properties WHERE object_property_id = %s AND deleted_at IS NULL', (object_property_id,))
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
            cur.execute(
                'SELECT * FROM object_properties WHERE name = %s AND deleted_at IS NULL', (name,))
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
            cur.execute(
                'SELECT * FROM object_properties WHERE domain_id = %s AND deleted_at IS NULL', (domain_id,))
            object_properties = cur.fetchall()
            return object_properties
    except Exception as e:
        logger.error(f"Error fetching object properties by domain id: {e}")
        return None
    finally:
        close_pool_connection(conn)


"""classes data junction"""
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
            cur.execute(
                'SELECT * FROM classes_data_junction WHERE class_id = %s AND deleted_at IS NULL', (class_id,))
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
            cur.execute(
                'SELECT * FROM classes_data_junction WHERE data_property_id = %s AND deleted_at IS NULL', (data_property_id,))
            classes_data_junction = cur.fetchall()
            return classes_data_junction
    except Exception as e:
        logger.error(
            f"Error fetching classes data junction by data property id: {e}")
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
            cur.execute(
                'SELECT * FROM classes_object_junction WHERE class_id = %s AND deleted_at IS NULL', (class_id,))
            classes_object_junction = cur.fetchall()
            return classes_object_junction
    except Exception as e:
        logger.error(
            f"Error fetching classes object junction by class id: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_classes_object_junction_by_object_property_id(object_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching classes object junction by object property id")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM classes_object_junction WHERE object_property_id = %s AND deleted_at IS NULL', (object_property_id,))
            classes_object_junction = cur.fetchall()
            return classes_object_junction
    except Exception as e:
        logger.error(
            f"Error fetching classes object junction by object property id: {e}")
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
            cur.execute(
                'SELECT * FROM domains WHERE domain_id = %s AND deleted_at IS NULL', (domain_id,))
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
            cur.execute(
                'SELECT * FROM domains WHERE name = %s AND deleted_at IS NULL', (name,))
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
            cur.execute(
                'SELECT * FROM domains WHERE object_property_id = %s AND deleted_at IS NULL', (object_property_id,))
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


def get_range_by_name(name):
    conn = get_pool_connection()
    try:
        logger.info("fetching range by name")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM ranges WHERE name = %s AND deleted_at IS NULL', (name,))
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
            cur.execute(
                'SELECT * FROM ranges WHERE object_property_id = %s AND deleted_at IS NULL', (object_property_id,))
            ranges = cur.fetchall()
            return ranges
    except Exception as e:
        logger.error(f"Error fetching ranges by object property id: {e}")
        return None
