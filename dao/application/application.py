import psycopg2
import bcrypt
from misc import rand_str

APP_KEY_LEN = 8

class ApplicationDao:
    
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
    def create(cur, name, username, desc):
        query = """
        INSERT INTO
            applications
        VALUES
            (%s, %s, %s, %s)
        """
        cur.execute(query, (name, rand_str(APP_KEY_LEN), username, desc))
        
        return (True,)

    @staticmethod
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

    @staticmethod
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

    
    @staticmethod
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

    @staticmethod
    @with_psql
    def update(cur, appkey, name, desc):
        query = """
        UPDATE
            applications
        SET
            name = %s,
            description = %s,
        WHERE
            app_key = %s
        """
        cur.execute(query, (name, desc, appkey))

        return (True,)


