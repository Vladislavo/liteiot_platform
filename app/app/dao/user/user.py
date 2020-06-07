from app.helpers.misc import with_psql
import bcrypt


@with_psql
def create(cur, name, password, role):
    query = """
    INSERT INTO
        users
    VALUES
        (%s, %s, %s)
    """
    cur.execute(query, (name, bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8'), role))
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
    cur.execute(query, (new_name,old_name))
    return (True,)

@with_psql
def update_password(cur, name, password):
    query = """
    UPDATE users SET
        password = %s
    WHERE
        name = %s
    """
    cur.execute(query, (bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8'), name))
    return (True,)


@with_psql
def update_role(cur, name, role):
    query = """
    UPDATE users SET
        role = %s
    WHERE
        name = %s
    """
    cur.execute(query, (role,name))
    return (True,)

@with_psql
def get(cur, name):
    query = """
    SELECT * FROM
        users
    WHERE 
        name = %s
    """
    cur.execute(query, (name,))
    return (True, cur.fetchone())

@with_psql
def check(cur, name, password):
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

@with_psql
def get_count(cur):
    query = """
    SELECT COUNT(*) FROM
        users
    """
    cur.execute(query, ())
    return (True, cur.fetchone())


@with_psql
def get_range(cur, rng):
    query = """
    SELECT * FROM
        users
    ORDER BY
        name ASC
    LIMIT %s OFFSET %s
    """
    cur.execute(query, (rng[0],rng[1]))
    return (True, cur.fetchall())


@with_psql
def get_range_name(cur, name, rng):
    name += '%'
    query = """
    SELECT * FROM
        users
    WHERE name LIKE %s
    ORDER BY
        name ASC
    LIMIT %s OFFSET %s
    """
    cur.execute(query, (name, rng[0],rng[1]))
    return (True, cur.fetchall())


