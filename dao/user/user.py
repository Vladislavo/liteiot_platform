import psycopg2
import bcrypt


class UserDao:
    
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
    def create(cur, name, password):
        query = """
        INSERT INTO
            users
        VALUES
            (%s, %s)
        """
        cur.execute(query, (name, bcrypt.hashpw(password, bcrypt.gensalt())))
        return (True,)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

