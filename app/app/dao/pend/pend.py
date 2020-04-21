from app.helpers.misc import with_psql

@with_psql
def create(cur, appkey, devid, msg):
    query = """
    INSERT INTO
        pend_msgs
    VALUES
        (%s, %s, %s)
    """
    cur.execute(query, (appkey, devid, msg))
    return (True,)

@with_psql
def get_list(cur, appkey, devid):
    query = """
    SELECT * FROM
        pend_msgs
    WHERE
        app_key = %s
    AND
        dev_id = %s
    """
    cur.execute(query, (appkey, devid))
    return (True, cur.fetchall())

@with_psql
def delete(cur, appkey, devid, msg):
    query = """
    DELETE FROM
        pend_msgs
    WHERE
        app_key = %s
    AND
        dev_id = %s
    AND
        msg LIKE %s
    """
    cur.execute(query, (appkey, devid, msg))
    return (True,)
