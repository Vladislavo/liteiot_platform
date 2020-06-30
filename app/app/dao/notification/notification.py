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
def delete(cur, appkey, devid, nid):
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
def get(cur, appkey, devid, nid):
    query = """
    SELECT * FROM
        notifications
    WHERE
        id = %s
    AND
        app_key = %s
    AND
        dev_id = %s
    """
    cur.execute(query, (nid, appkey, devid))
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
def get_per_device(cur, appkey, devid):
    query = """
    SELECT * FROM
        notifications
    WHERE
        app_key = %s
    AND
        dev_id = %s
    """
    cur.execute(query, (appkey, devid))

    return (True, cur.fetchall())

@with_psql
def get_alerts_list(cur, appkey):
    query = """
    SELECT * FROM
        notifications
    WHERE
        app_key = %s
    AND
        action_type LIKE 'alert_%%'
    """
    cur.execute(query, (appkey,))
    
    return (True, cur.fetchall())


@with_psql
def get_automation_list(cur, appkey):
    query = """
    SELECT * FROM
        notifications
    WHERE
        app_key = %s
    AND
        action_type = 'automation'
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
