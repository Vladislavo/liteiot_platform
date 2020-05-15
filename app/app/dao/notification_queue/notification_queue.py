from app.helpers.misc import with_psql

@with_psql
def create(cur, nid, appkey, devid):
    query = """
    INSERT INTO
        notifications_queue
    VALUES
        (%s, %s, %s)
    """
    cur.execute(query, (nid, appkey, devid))
       
    return (True,)

@with_psql
def delete(cur, appkey, devid, nid):
    query = """
    DELETE FROM
        notifications_queue
    WHERE
         nf_id = %s
    AND
        app_key = %s
    AND
        dev_id = %s
    """
    cur.execute(query, (nid, appkey, devid))
        
    return (True,)

@with_psql
def get(cur, appkey, devid, nid):
    query = """
    SELECT * FROM
        notifications_queue
    WHERE
        nf_id = %s
    AND
        app_key = %s
    AND
        dev_id = %s
    """
    cur.execute(query, (nid, appkey, devid))
    nf = cur.fetchone()

    if nf is None:
        return (False, 'Queued notification with appkey {} and id {} does not exist'.format(appkey, nid))
    else:
        return (True, nf)

@with_psql
def delete_list(cur, appkey):
    query = """
    DELETE FROM
        notifications_queue
    WHERE
        app_key = %s
    """
    cur.execute(query, (appkey,))
    
    return (True,)
    
@with_psql
def get_all(cur):
    query = """
    SELECT * FROM
        notifications_queue
    """
    cur.execute(query)

    return (True, cur.fetchall())


@with_psql
def get_count(cur):
    query = """
    SELECT COUNT(*) FROM
        notifications_queue
    """
    cur.execute(query, ())

    return (True, cur.fetchone())
