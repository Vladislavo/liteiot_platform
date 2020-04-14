import psycopg2
from psycopg2 import sql
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
    def create_datatable(cur, appkey, dev_id):
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

    
    @staticmethod
    @with_psql
    def delete_datatable(cur, appkey, dev_id):
        tn = 'dev_' +str(appkey)+ '_' +str(dev_id)
        cur.execute(
            psycopg2.sql.SQL(
                "DROP TABLE {}"
            ).format(sql.Identifier(tn)))
        return (True,)

    @staticmethod
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

    
    @staticmethod
    @with_psql
    def delete_table(cur, appkey):
        tn = 'devices_' +str(appkey)
        cur.execute(
            psycopg2.sql.SQL(
                "DROP TABLE {}"
            ).format(sql.Identifier(tn)))
        return (True,)




    @staticmethod
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


    @staticmethod
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


    @staticmethod
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


    @staticmethod
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

