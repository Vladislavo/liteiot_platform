from binascii import hexlify
import os
import psycopg2
import json

def rand_str(length):
    if length % 2 == 0:
        return hexlify(os.urandom(length//2))
    else:
        return hexlify(os.urandom(length//2 + 1))

def prep_id_range(devlist):
    r = range(1,255)

    for dev in devlist:
        del r[r.index(dev[1])]

    s = ''
    inr = False
    for i in range(len(r)-1):
        if r[i+1] - r[i] > 1:
            if inr:
                s += str(r[i])+'], '
                inr = False
            else:
                s += str(r[i])+', '
        else:
            if not inr:
                s += '['+str(r[i])+'-'
                inr = True
   
    if r[-1] - r[-2] > 1:
        if inr:
            s += str(r[-1])+']'
        else:
            s += str(r[-1])
    else:
        if not inr:
            s += str(r[-1])
        else:
            s += str(r[-1])+']'

    return s

# decorator implementation
def with_psql(f):
    def _with_psql(*args, **kwargs):
        db_conf = read_json_file('db.conf')
        conn = psycopg2.connect(
                database = db_conf['name'], 
                user = db_conf['user'], 
                password = db_conf['password'],
                host = db_conf['host'],
                port = db_conf['port']
            )
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

def read_json_file(path):
    json_dict = None
    try:
        with open(path) as json_file:
            json_dict = json.load(json_file)
    except Exception, e:
        print("{} : {}".format(path, e))

    return json_dict
