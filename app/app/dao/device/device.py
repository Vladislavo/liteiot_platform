from psycopg2 import sql
from app.helpers.misc import with_psql
import app.dao.application.application as ad

@with_psql
def create_datatable(cur, appkey, dev_id):
    tn = 'dev_' +str(appkey)+ '_' +str(dev_id)
    cur.execute(
        sql.SQL(
            """CREATE TABLE {} (
                utc NUMERIC(10) DEFAULT EXTRACT(EPOCH FROM now())::int NOT NULL,
                timedate VARCHAR(100) NOT NULL,
                data json NOT NULL
            )"""
        ).format(sql.Identifier(tn)))
    return (True,)

    
@with_psql
def delete_datatable(cur, appkey, dev_id):
    tn = 'dev_' +str(appkey)+ '_' +str(dev_id)
    cur.execute(
        sql.SQL(
            "DROP TABLE {}"
        ).format(sql.Identifier(tn)))
    return (True,)

@with_psql
def create_table(cur, appkey):
    tn = 'devices_' +str(appkey)
    cur.execute(
        sql.SQL(
            """CREATE TABLE {} (
                name VARCHAR(30) NOT NULL,
                dev_id NUMERIC(3) PRIMARY KEY,
                description VARCHAR(200)
            )"""
        ).format(sql.Identifier(tn)))
    return (True,)

    
@with_psql
def delete_table(cur, appkey):
    tn = 'devices_' +str(appkey)
    cur.execute(
        sql.SQL(
            "DROP TABLE {}"
        ).format(sql.Identifier(tn)))
    return (True,)

@with_psql
def create(cur, name, dev_id, appkey, desc):
    tn = 'devices_' +str(appkey)
    query = """
    INSERT INTO 
        {}
    VALUES
        (%s, %s, %s)
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [name, dev_id, desc])
    return (True,)


@with_psql
def delete(cur, appkey, dev_id):
    tn = 'devices_' +str(appkey)
    query = """
    DELETE FROM 
        {}
    WHERE
        dev_id = %s
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [dev_id])
    return (True,)


@with_psql
def get(cur, appkey, dev_id):
    tn = 'devices_' +str(appkey)
    query = """
    SELECT * FROM 
        {}
    WHERE
        dev_id = %s
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [dev_id])
    dev = cur.fetchone()
    
    if (dev is None):
        return (False, 'There is no device with dev_id = {}'.format(dev_id))
    else:
        return (True, dev)

@with_psql
def update(cur, appkey, devid, name, desc):
    tn = 'devices_'+appkey
    query = """
        UPDATE
            {}
        SET
            name = %s,
            description = %s
        WHERE
            dev_id = %s
    """.format(tn)
    cur.execute(query, (name, desc, devid))

    return (True,)

@with_psql
def get_list(cur, appkey):
    tn = 'devices_' +str(appkey)
    query = """
    SELECT * FROM 
        {}
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)))
    return (True, cur.fetchall())


@with_psql
def get_count(cur, appkey):
    tn = 'devices_' +str(appkey)
    query = """
    SELECT COUNT(*) FROM 
        {}
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [appkey])
        
    return (True, cur.fetchone())

@with_psql
def get_count_all(cur):
    query = """
        SELECT COUNT(*) FROM
            information_schema.tables
        WHERE
            table_name ~ '^dev_'
        """
    cur.execute(query, ())
    return(True, cur.fetchone())


@with_psql
def get_count_by_user(cur, username):
    apps = ad.get_list(username)[1]
    count = 0

    for a in apps:
        query = """
        SELECT COUNT(*) FROM
            information_schema.tables
        WHERE
            table_name ~ '^dev_{}'
        """.format(a[1])
        cur.execute(query, ())
        count += cur.fetchone()[0]

    return count
