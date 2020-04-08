import psycopg2
import bcrypt


class DeviceDao:
    
    def __init__(self):
        pass

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

    @staticmethod
    @with_psql
    def create(cur, name, dev_id, appkey, desc):
        query = """
        INSERT INTO 
            devices
        VALUES
            (%s, %s, %s, %s)
        """
        cur.execute(query, (name, dev_id, appkey, desc))
        return (True,)


    @staticmethod
    @with_psql
    def delete(cur, appkey, dev_id):
        query = """
        DELETE FROM 
            devices
        WHERE
            app_key = %s 
        AND
            dev_id = %s
        """
        cur.execute(query, (appkey, dev_id))
        return (True,)


    @staticmethod
    @with_psql
    def get(cur, appkey, dev_id):
        query = """
        SELECT * FROM
            devices
        WHERE
            app_key = %s
        AND
            dev_id = %s
        """
        cur.execute(query, (appkey, dev_id))
        dev = cur.fetchone()
        
        if (dev is None):
            return (False, 'There is no device with dev_id = {}'.format(dev_id))
        else:
            return (True, dev)


    @staticmethod
    @with_psql
    def get_list(cur, appkey):
        query = """
        SELECT * FROM
            devices
        WHERE
            app_key = %s
        """
        cur.execute(query, (appkey,))
        return (True, cur.fetchall())

