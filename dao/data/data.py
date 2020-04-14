import psycopg2
from psycopg2 import sql

# decorator implementation
def with_psql(f):
    def _with_psql(*args, **kwargs):
        conn = psycopg2.connect('dbname=gateway')
        cur = conn.cursor()

        try:
            res = f(cur, *args, **kwargs)
        except (Exception, psycopg2.DatabaseError) as error:
            conn.rollback()
            res = (False, error)
        else:
            conn.commit()
        finally:
            cur.close()
            conn.close()
    
        return res
    return _with_psql


@with_psql
def create_table(cur, appkey, dev_id):
    tn = 'dev_' +str(appkey)+ '_' +str(dev_id)
    cur.execute(
        sql.SQL(
            """CREATE TABLE {} (
                utc NUMERIC(10) NOT NULL,
                timedate VARCHAR(100) NOT NULL,
                data json NOT NULL
            )"""
        ).format(sql.Identifier(tn)))
    return (True,)

    
@with_psql
def delete_table(cur, appkey, dev_id):
    tn = 'dev_' +str(appkey)+ '_' +str(dev_id)
    cur.execute(
        psycopg2.sql.SQL(
            "DROP TABLE {}"
        ).format(sql.Identifier(tn)))
    return (True,)


@with_psql
def get_last_n(cur, appkey, dev_id, n):
    tn = 'dev_' +str(appkey)+ '_' +str(dev_id)
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
def get_all(cur, appkey, devid):
    tn = 'dev_' +str(appkey)+ '_' +str(dev_id)
        query = """
        SELECT * FROM
            {}
        """
        cur.execute(
            sql.SQL(query).format(sql.Identifier(tn)))
        return (True, cur.fetchall())

