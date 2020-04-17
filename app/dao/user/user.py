from app.helpers.misc import with_psql
import bcrypt


@with_psql
def create(cur, name, password):
    query = """
    INSERT INTO
        users
    VALUES
        (%s, %s)
    """
    cur.execute(query, (name, bcrypt.hashpw(password, bcrypt.gensalt())))
    return (True,)

@with_psql 
def delete(cur, name):
    query = """
    DELETE FROM
        users
    WHERE
        name = %s
    """
    cur.execute(query, (name,))
    return (True,)

@with_psql
def update_name(cur, old_name, new_name):
    query = """
    UPDATE users SET
        name = %s
    WHERE
        name = %s
    """
    cur.execute(query, (new_name,))
    return (True,)

@with_psql
def update_password(cur, name, password):
    query = """
    UPDATE users SET
        password = %s
    WHERE
        name = %s
    """
    cur.execute(query, (password, name))
    return (True,)

@with_psql
def get(cur, name, password):
    query = """
    SELECT * FROM
        users
    WHERE 
        name = %s
    """
    cur.execute(query, (name,))
    user = cur.fetchall()[0]
    
    if user[1].encode('utf-8') == bcrypt.hashpw(password, user[1].encode('utf-8')):
        return (True, user)
    else:
        return (False, 'Password or username do not match')

