import uuid  

from app.database import close_pool_connection, get_pool_connection, logger
from psycopg2.extras import execute_values


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
                'SELECT * FROM important_terms WHERE important_terms_id = %s AND deleted_at IS NULL',
                (important_terms_id,
                 ))
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
                'SELECT * FROM important_terms WHERE conversation_id = %s AND deleted_at IS NULL',
                (convo_id,
                 ))
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


def delete_class(class_id):
    conn = get_pool_connection()
    try:
        logger.info("deleting class")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE classes SET deleted_at = CURRENT_TIMESTAMP WHERE class_id = %s
                RETURNING *;
            ''', (class_id,))
            classes = cur.fetchone()
            conn.commit()
            return classes
    except Exception as e:
        logger.error(f"Error deleting class: {e}")
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


def get_class_by_name(conversation_id, name):
    conn = get_pool_connection()
    try:
        logger.info("fetching class by name")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM classes WHERE name = %s AND conversation_id = %s AND deleted_at IS NULL', (name, conversation_id))
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
                'SELECT class_id, conversation_id, name, description, created_at FROM classes WHERE conversation_id = %s AND deleted_at IS NULL',
                (convo_id,
                 ))
            classes = cur.fetchall()
            return classes
    except Exception as e:
        logger.error(f"Error fetching classes by conversation id: {e}")
        return None
    finally:
        close_pool_connection(conn)


"""data properties"""


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


def delete_classes_data_junction(class_id="", data_property_id=""):
    conn = get_pool_connection()
    try:
        logger.info("deleting classes data junction")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE classes_data_junction SET deleted_at = CURRENT_TIMESTAMP WHERE (class_id = %s AND data_property_id = %s)
                RETURNING *;
            ''', (class_id, data_property_id))
            junction = cur.fetchone()
            conn.commit()
            return junction
    except Exception as e:
        logger.error(f"Error deleting classes data junction: {e}")
        return None
    finally:
        close_pool_connection(conn)


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


def delete_data_property(data_property_id):
    conn = get_pool_connection()
    try:
        logger.info("deleting data property")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE data_properties SET deleted_at = CURRENT_TIMESTAMP WHERE data_property_id = %s
                RETURNING *;
            ''', (data_property_id,))
            data_property = cur.fetchone()
            conn.commit()
            return data_property
    except Exception as e:
        logger.error(f"Error deleting data property: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_data_property_by_id(data_property_id):
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM data_properties WHERE data_property_id = %s AND deleted_at IS NULL',
                (data_property_id,
                 ))
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
                SELECT c.name as class_name, dp.data_property_id, dp.name as data_property_name, dp.data_type as data_property_type
                FROM data_properties dp
                RIGHT JOIN classes_data_junction cdj ON dp.data_property_id = cdj.data_property_id
                RIGHT JOIN classes c ON cdj.class_id = c.class_id
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


def delete_object_domains_ranges_junction(object_property_id):
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE domains_ranges_junction
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE object_property_id = %s
            ''', (object_property_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Error deleting object domains ranges junction: {e}")
        return None
    finally:
        close_pool_connection(conn)


def delete_classes_object_junction(class_id, object_property_id):
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE classes_object_junction
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE class_id = %s AND object_property_id = %s
            ''', (class_id, object_property_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Error deleting classes object junction: {e}")
        return None
    finally:
        close_pool_connection(conn)


def delete_object_property(object_property_id):
    conn = get_pool_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE object_properties
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE object_property_id = %s
            ''', (object_property_id,))
        conn.commit()
    except Exception as e:
        logger.error(f"Error deleting object property: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_object_property_by_id(object_property_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching object property by id")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM object_properties WHERE object_property_id = %s AND deleted_at IS NULL',
                (object_property_id,
                 ))
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
            # cur.execute('''
            #     SELECT
            #         op.name as object_property_name,
            #         op.object_property_id,
            #         op.created_at,
            #         json_agg(DISTINCT jsonb_build_object(
            #             'domain_id', d.domain_id,
            #             'domain_name', d.name
            #         )) AS domains,
            #         json_agg(DISTINCT jsonb_build_object(
            #             'range_id', r.range_id,
            #             'range_name', r.name
            #         )) AS ranges
            #     FROM object_properties op
            #     JOIN classes_object_junction coj ON op.object_property_id = coj.object_property_id
            #     JOIN classes c ON coj.class_id = c.class_id
            #     LEFT JOIN domains_ranges_junction drj ON op.object_property_id = drj.object_property_id
            #     LEFT JOIN domains d ON drj.domain_id = d.domain_id
            #     LEFT JOIN ranges r ON drj.range_id = r.range_id
            #     WHERE c.class_id = %s AND op.deleted_at IS NULL
            #     GROUP BY op.object_property_id, op.created_at, op.name, c.name
            # ''', (class_id,))
            cur.execute('''
            SELECT
                op.name as object_property_name,
                op.object_property_id,
                op.created_at,
                json_agg(DISTINCT jsonb_build_object(
                    'domain_id', d.domain_id,
                    'domain_name', d.name,
                    'ranges', (
                        SELECT json_agg(jsonb_build_object(
                            'range_id', r.range_id,
                            'range_name', r.name
                        ))
                        FROM ranges r
                        JOIN domains_ranges_junction drj2 ON r.range_id = drj2.range_id
                        WHERE drj2.domain_id = d.domain_id
                          AND drj2.object_property_id = op.object_property_id
                          AND drj2.deleted_at IS NULL
                          AND r.deleted_at IS NULL
                          AND r.range_id IS NOT NULL
                    )
                )) FILTER (WHERE d.domain_id IS NOT NULL) AS domains
                FROM object_properties op
                JOIN classes_object_junction coj ON op.object_property_id = coj.object_property_id
                JOIN classes c ON coj.class_id = c.class_id
                LEFT JOIN domains_ranges_junction drj ON op.object_property_id = drj.object_property_id
                LEFT JOIN domains d ON drj.domain_id = d.domain_id AND d.deleted_at IS NULL
                WHERE c.class_id = %s
                AND op.deleted_at IS NULL
                GROUP BY op.object_property_id, op.created_at, op.name;
            ''', (class_id,))
            object_properties = cur.fetchall()
            return object_properties
    except Exception as e:
        logger.error(
            f"Error fetching object properties by conversation id: {e}")
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


def delete_domain(domain_id):
    conn = get_pool_connection()
    try:
        logger.info("deleting domain")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE domains SET deleted_at = CURRENT_TIMESTAMP WHERE domain_id = %s
                RETURNING *;
            ''', (domain_id,))
            domain = cur.fetchone()
            conn.commit()
            return domain
    except Exception as e:
        logger.error(f"Error deleting domain: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_domain_by_id(domain_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching domain by id")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM domains WHERE domain_id = %s AND deleted_at IS NULL',
                (domain_id,
                 ))
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
                WHERE op.object_property_id = %s AND op.deleted_at IS NULL AND d.deleted_at IS NULL
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


def delete_domains_ranges_junction(
        domain_id="",
        range_id="",
        object_property_id=""):
    conn = get_pool_connection()
    try:
        logger.info("deleting domains ranges junction")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE domains_ranges_junction SET deleted_at = CURRENT_TIMESTAMP WHERE (domain_id = %s OR range_id = %s) AND object_property_id = %s
                RETURNING *;
            ''', (domain_id, range_id, object_property_id))
            junction = cur.fetchone()
            conn.commit()
            return junction
    except Exception as e:
        logger.error(f"Error deleting domains ranges junction: {e}")
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


def delete_range(range_id):
    conn = get_pool_connection()
    try:
        logger.info("deleting range")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE ranges SET deleted_at = CURRENT_TIMESTAMP WHERE range_id = %s
                RETURNING *;
            ''', (range_id,))
            range = cur.fetchone()
            conn.commit()
            return range
    except Exception as e:
        logger.error(f"Error deleting range: {e}")
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
                WHERE op.object_property_id = %s AND op.deleted_at IS NULL AND r.deleted_at IS NULL
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


"""instances"""


def create_classes_instances_junction(class_id, instance_id):
    conn = get_pool_connection()
    try:
        logger.info("inserting classes instances junction into database")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO classes_instances_junction (class_id, instance_id)
                VALUES (%s, %s)
                RETURNING *;
            ''', (class_id, instance_id))
            junction = cur.fetchone()
            conn.commit()
            return junction
    except Exception as e:
        logger.error(f"Error inserting classes instances junction: {e}")
        return None
    finally:
        close_pool_connection(conn)


def delete_classes_instances_junction(class_id="", instance_id=""):
    conn = get_pool_connection()
    try:
        logger.info("deleting classes instances junction")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE classes_instances_junction SET deleted_at = CURRENT_TIMESTAMP WHERE (class_id = %s AND instance_id = %s)
                RETURNING *;
            ''', (class_id, instance_id))
            junction = cur.fetchone()
            conn.commit()
            return junction
    except Exception as e:
        logger.error(f"Error deleting classes instances junction: {e}")
        return None
    finally:
        close_pool_connection(conn)


def create_instance(instance_id, class_id, name):
    conn = get_pool_connection()
    try:
        logger.info("inserting instance into database")
        with conn.cursor() as cur:
            cur.execute('''
                INSERT INTO instances (instance_id, class_id, name)
                VALUES (%s, %s, %s)
                RETURNING *;
            ''', (instance_id, class_id, name))
            instance = cur.fetchone()
            conn.commit()
            return instance
    except Exception as e:
        logger.error(f"Error inserting an instance: {e}")
        return None
    finally:
        close_pool_connection(conn)


def update_instance(instance_id, name):
    conn = get_pool_connection()
    try:
        logger.info("updating instance")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE instances SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE instance_id = %s
                RETURNING *;
            ''', (name, instance_id))
            instance = cur.fetchone()
            conn.commit()
            return instance
    except Exception as e:
        logger.error(f"Error updating instance: {e}")
        return None
    finally:
        close_pool_connection(conn)


def delete_instance(instance_id):
    conn = get_pool_connection()
    try:
        logger.info("deleting instance")
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE instances SET deleted_at = CURRENT_TIMESTAMP WHERE instance_id = %s
                RETURNING *;
            ''', (instance_id,))
            instance = cur.fetchone()
            conn.commit()
            return instance
    except Exception as e:
        logger.error(f"Error deleting instance: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_instance_by_id(instance_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching instance by id")
        with conn.cursor() as cur:
            cur.execute(
                'SELECT * FROM instances WHERE instance_id = %s AND deleted_at IS NULL',
                (instance_id,
                 ))
            instance = cur.fetchone()
            return instance
    except Exception as e:
        logger.error(f"Error fetching instance by id: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_all_instances_by_class_id(class_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching instances by class id")
        with conn.cursor() as cur:
            cur.execute('''
                SELECT i.instance_id, i.name as instance_name, i.created_at
                FROM instances i
                JOIN classes_instances_junction cij ON i.instance_id = cij.instance_id
                JOIN classes c ON cij.class_id = c.class_id
                WHERE c.class_id = %s AND i.deleted_at IS NULL
            ''', (class_id,))
            instances = cur.fetchall()
            return instances
    except Exception as e:
        logger.error(f"Error fetching instances by class id: {e}")
        return None
    finally:
        close_pool_connection(conn)


def get_all_instances_by_conversation_id(conversation_id):
    conn = get_pool_connection()
    try:
        logger.info("fetching instances by conversation id")
        with conn.cursor() as cur:
            cur.execute('''
                SELECT
                    c.class_id,
                    c.name AS class_name,
                    json_agg(
                        DISTINCT jsonb_build_object(
                            'instance_id', i.instance_id,
                            'instance_name', i.name
                        )
                    ) AS instances
                FROM
                    conversations cv
                JOIN
                    classes c ON c.conversation_id = cv.conversation_id
                LEFT JOIN
                    classes_instances_junction cij ON cij.class_id = c.class_id
                LEFT JOIN
                    instances i ON i.instance_id = cij.instance_id
                WHERE
                    cv.conversation_id = %s
                    AND cv.deleted_at IS NULL
                    AND c.deleted_at IS NULL
                    AND i.deleted_at IS NULL
                GROUP BY
                    c.class_id, c.name;
            ''', (conversation_id,))
            instances = cur.fetchall()
            return instances
    except Exception as e:
        logger.error(f"Error fetching instances by conversation id: {e}")
        return None
    finally:
        close_pool_connection(conn)


"""batches"""


def save_classes_and_properties_service(llm_response_json, conversation_id):  
    conn = get_pool_connection()  
    try:  
        conn.autocommit = False  
        cursor = conn.cursor()  
  
        cursor.execute("""  
            SELECT name, class_id FROM classes WHERE conversation_id = %s  
        """, (conversation_id,))  
        existing_classes = {row[0]: row[1] for row in cursor.fetchall()}  
  
        new_classes = []  
        new_instances = []  
        new_data_properties = []  
        new_object_properties = []  
        new_domains = []  
        new_ranges = []  
        new_classes_instances_junctions = []  
        new_classes_data_junctions = []  
        new_classes_object_junctions = []  
        new_domains_ranges_junctions = []  
  
        for cls in llm_response_json["classes"]:  
            class_name = cls["name"].replace(" ", "")  
            if class_name not in existing_classes:  
                class_id = uuid.uuid4()  
                new_classes.append((class_id, conversation_id, class_name))  
                existing_classes[class_name] = class_id  
            else:  
                class_id = existing_classes[class_name]  
  
            for instance in cls["instances"]:  
                instance_name = instance.replace(" ", "")  
                instance_id = uuid.uuid4()  
                new_instances.append((instance_id, class_id, instance_name))  
                new_classes_instances_junctions.append((class_id, instance_id))  
  
            for data_prop in cls["data_properties"]:  
                data_property_name = data_prop["name"].replace(" ", "")  
                data_property_type = data_prop["recommended_data_type"]  
                data_property_id = uuid.uuid4()  
                new_data_properties.append((data_property_id, class_id, data_property_name, data_property_type))  
                new_classes_data_junctions.append((class_id, data_property_id))  
  
            for obj_prop in cls["object_properties"]:  
                object_property_name = obj_prop["name"].replace(" ", "")  
                object_property_id = uuid.uuid4()  
                new_object_properties.append((object_property_id, class_id, object_property_name))  
                new_classes_object_junctions.append((class_id, object_property_id))  
  
                for domain_name in obj_prop["recommended_domain"]:  
                    domain_name = domain_name.replace(" ", "")  
                    domain_id = uuid.uuid4()  
                    new_domains.append((domain_id, object_property_id, domain_name))  
  
                    for range_name in obj_prop["recommended_range"]:  
                        range_name = range_name.replace(" ", "")  
                        range_id = uuid.uuid4()  
                        new_ranges.append((range_id, object_property_id, range_name))  
                        new_domains_ranges_junctions.append((object_property_id, domain_id, range_id))  
  
        if new_classes:  
            execute_values(cursor, """  
                INSERT INTO classes (class_id, conversation_id, name) VALUES %s  
            """, new_classes)  
  
        if new_instances:  
            execute_values(cursor, """  
                INSERT INTO instances (instance_id, class_id, name) VALUES %s  
            """, new_instances)  
  
        if new_data_properties:  
            execute_values(cursor, """  
                INSERT INTO data_properties (data_property_id, class_id, name, data_type) VALUES %s  
            """, new_data_properties)  
  
        if new_object_properties:  
            execute_values(cursor, """  
                INSERT INTO object_properties (object_property_id, class_id, name) VALUES %s  
            """, new_object_properties)  
            
        if new_domains:  
            execute_values(cursor, """  
                INSERT INTO domains (domain_id, object_property_id, name) VALUES %s  
            """, new_domains)  
  
        if new_ranges:  
            execute_values(cursor, """  
                INSERT INTO ranges (range_id, object_property_id, name) VALUES %s  
            """, new_ranges)  
  
        if new_classes_instances_junctions:  
            execute_values(cursor, """  
                INSERT INTO classes_instances_junction (class_id, instance_id) VALUES %s  
            """, new_classes_instances_junctions)  
  
        if new_classes_data_junctions:  
            execute_values(cursor, """  
                INSERT INTO classes_data_junction (class_id, data_property_id) VALUES %s  
            """, new_classes_data_junctions)  
  
        if new_classes_object_junctions:  
            execute_values(cursor, """  
                INSERT INTO classes_object_junction (class_id, object_property_id) VALUES %s  
            """, new_classes_object_junctions)  
  
        if new_domains_ranges_junctions:  
            execute_values(cursor, """  
                INSERT INTO domains_ranges_junction (object_property_id, domain_id, range_id) VALUES %s  
            """, new_domains_ranges_junctions)  
  
        conn.commit()  
  
        return {  
            "message": "Saving Classes and Properties Has Been Successful",  
            "status_code": 200,  
            "data": None  
        }  
    except Exception as e:  
        conn.rollback()  
        logger.error(f"An error occurred while saving classes and properties: {e}")  
        return {  
            "message": f"An error occurred: {str(e)}",  
            "status_code": 500,  
            "data": None  
        }  
    finally:  
        cursor.close()  
        close_pool_connection(conn)
