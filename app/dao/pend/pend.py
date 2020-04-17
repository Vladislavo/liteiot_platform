from app.helpers.misc import with_psql

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

