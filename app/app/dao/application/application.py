from app.helpers.misc import with_psql

@with_psql
def create(cur, name, appkey, username, desc, secure, secure_key):
    query = """
    INSERT INTO
        applications
    VALUES
        (%s, %s, %s, %s, %s, %s)
    """
    cur.execute(query, (name, appkey, username, desc, secure, secure_key))
       
    return (True,)

@with_psql
def delete(cur, appkey):
    query = """
    DELETE FROM
        applications
    WHERE
        app_key = %s
    """
    cur.execute(query, (appkey,))
        
    return (True,)

@with_psql
def get(cur, appkey):
    query = """
    SELECT * FROM
        applications
    WHERE
        app_key = %s
    """
    cur.execute(query, (appkey,))
    app = cur.fetchone()

    if app is None:
        return (False, 'Application with key {} does not exist'.format(appkey))
    else:
        return (True, app)

    
@with_psql
def get_list(cur, username):
    query = """
    SELECT * FROM
        applications
    WHERE
        username = %s
    """
    cur.execute(query, (username,))

    return (True, cur.fetchall())

@with_psql
def update(cur, appkey, name, desc, secure):
    query = """
    UPDATE
        applications
    SET
        name = %s,
        description = %s,
        secure = %s
    WHERE
        app_key = %s
    """
    cur.execute(query, (name, desc, secure, appkey))

    return (True,)

@with_psql
def get_count(cur):
    query = """
    SELECT COUNT(*) FROM
        applications
    """
    cur.execute(query, ())

    return (True, cur.fetchone())


@with_psql
def get_count_by_user(cur, username):
    query = """
    SELECT COUNT(*) FROM
        applications
    WHERE
        username = %s
    """
    cur.execute(query, (username,))

    return (True, cur.fetchone())
