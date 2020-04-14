import psycopg2

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
def create(cur, appkey, devid, msg):
    query = """
    INSERT INTO
        pend_msgs
    VALUES
        (%s, %s, %s)
    """
    cur.execute(query, (appkey, devid, msg))
    return (True,)

