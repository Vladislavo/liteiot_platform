from psycopg2 import sql
from app.helpers.misc import with_psql
from datetime import datetime


@with_psql
def create_table(cur, appkey, devid):
    tn = 'dev_' +str(appkey)+ '_' +str(devid)
    cur.execute(
        sql.SQL(
            """CREATE TABLE {} (
                utc NUMERIC(10) NOT NULL,
                timedate VARCHAR(100) NOT NULL,
                data bytea NOT NULL
            )"""
        ).format(sql.Identifier(tn)))
    return (True,)
    

@with_psql
def delete_table(cur, appkey, devid):
    tn = 'dev_' +str(appkey)+ '_' +str(devid)
    cur.execute(
        sql.SQL(
            "DROP TABLE {}"
        ).format(sql.Identifier(tn)))
    return (True,)


@with_psql
def get_last_n(cur, appkey, devid, n):
    tn = 'dev_' +str(appkey)+ '_' +str(devid)
    query = """
        SELECT * FROM 
            {}
        ORDER BY 
            utc DESC
        LIMIT %s
        """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [n])
    data = cur.fetchall()
        
    if (data == []):
        return (False, 'There is no data for the device.')
    else:
        return (True, data)


@with_psql
def get_last_range(cur, appkey, devid, r):
    tn = 'dev_' +str(appkey)+ '_' +str(devid)
    query = """
        SELECT * FROM 
            {}
        ORDER BY 
            utc DESC
        LIMIT %s OFFSET %s
        """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [r[0],r[1]])
    data = cur.fetchall()
        
    if (data == []):
        return (False, 'There is no data for the device.')
    else:
        return (True, data)


@with_psql
def get_last_hours(cur, appkey, devid, hours, p):
    tn = 'dev_' +str(appkey)+ '_' +str(devid)
    last = get_last_n(appkey, devid, 1)
    utcb = last[1][0][0] - hours*3600*p
    utcu = utcb + hours*3600
    query = """
        SELECT * FROM 
            {}
        WHERE 
            utc > %s
        AND
            utc <= %s
        ORDER BY utc DESC
        """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)), [utcb, utcu])
    data = cur.fetchall()
    
    if (data == []):
        return (False, 'There is no data for the device.')
    else:
        return (True, data)


@with_psql
def get_all(cur, appkey, devid):
    tn = 'dev_' +str(appkey)+ '_' +str(devid)
    query = """
        SELECT * FROM
            {}
        """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)))
    return (True, cur.fetchall())

@with_psql
def get_count(cur, appkey, devid):
    tn = 'dev_' +str(appkey)+ '_' +str(devid)
    query = """
        SELECT COUNT(*) FROM
            {}
        """
    cur.execute(
        sql.SQL(query).format(sql.Identifier(tn)))
    return (True, cur.fetchone())


