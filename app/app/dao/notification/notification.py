from app.helpers.misc import with_psql

@with_psql
def create(cur, nid, appkey, devid, name, desc, action_type, action):
    query = """
    INSERT INTO
        notifications
    VALUES
        (%s, %s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, (nid, appkey, devid, name, desc, action_type, action))
       
    return (True,)

@with_psql
def delete(cur, appkey, nid, devid):
    query = """
    DELETE FROM
        notifications
    WHERE
        id = %s
    AND
        app_key = %s
    AND
        dev_id = %s
    """
    cur.execute(query, (nid, appkey, devid))
        
    return (True,)

@with_psql
def get(cur, appkey, nid):
    query = """
    SELECT * FROM
        notifications
    WHERE
        id = %s
    AND
        app_key = %s
    """
    cur.execute(query, (nid, appkey))
    nf = cur.fetchone()

    if nf is None:
        return (False, 'Notification with appkey {} and id {} does not exist'.format(appkey, nid))
    else:
        return (True, nf)

    
@with_psql
def get_list(cur, appkey):
    query = """
    SELECT * FROM
        notifications
    WHERE
        app_key = %s
    """
    cur.execute(query, (appkey,))

    return (True, cur.fetchall())


@with_psql
def get_count(cur):
    query = """
    SELECT COUNT(*) FROM
        notifications
    """
    cur.execute(query, ())

    return (True, cur.fetchone())
