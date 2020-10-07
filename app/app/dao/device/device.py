from psycopg2 import sql, Binary
from app.helpers.misc import with_psql
import app.dao.application.application as ad
import json


@with_psql
def create_datatable(cur, appkey, dev_id, model):
    tn = 'dev_' +str(appkey)+ '_' +str(dev_id)
    cur.execute(
        sql.SQL(
            """CREATE TABLE {} (
                utc NUMERIC(10) DEFAULT EXTRACT(EPOCH FROM now())::int NOT NULL,
                timedate VARCHAR(100) NOT NULL,
                data bytea NOT NULL
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
                description VARCHAR(200),
                device_data_model bytea NOT NULL
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
def create(cur, name, dev_id, appkey, desc, ddm):
    tn = 'devices_' +str(appkey)
    query = """
    INSERT INTO 
        {}
    VALUES
        (%s, %s, %s, %s)
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [name, dev_id, desc, Binary(json.dumps(ddm).encode('utf-8'))])
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
    #print(json.loads(dev[3].tobytes()))
    if (dev is None):
        return (False, 'There is no device with dev_id = {}'.format(dev_id))
    else:
        dev = [d for d in dev]
        dev[3] = json.loads(dev[3].tobytes())
        return (True, dev)


@with_psql
def update(cur, appkey, devid, name, desc, ddm):
    tn = 'devices_'+appkey
    query = """
        UPDATE
            {}
        SET
            name = %s,
            description = %s,
            device_data_model = %s
        WHERE
            dev_id = %s
    """.format(tn)
    cur.execute(query, (name, desc, Binary(json.dumps(ddm).encode('utf-8')), devid))

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
    
    devlist = cur.fetchall()
    for i in range(len(devlist)):
        devlist[i] = [d for d in devlist[i]]
        devlist[i][3] = json.loads(devlist[i][3].tobytes())

    return (True, devlist)


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


@with_psql
def check_devid(cur, appkey, dev_id):
    tn = 'devices_' +str(appkey)
    query = """
    SELECT dev_id FROM 
        {}
    WHERE
        dev_id = %s
    """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [dev_id])
    dev = cur.fetchone()
   
    return dev is None

