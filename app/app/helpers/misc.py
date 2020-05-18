from app import app
from binascii import hexlify
import os
import psycopg2
import binascii

def rand_str(length):
    if length % 2 == 0:
        return hexlify(os.urandom(length//2))
    else:
        return hexlify(os.urandom(length//2 + 1))

def prep_id_range(devlist):
    r = list(range(1,255))

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

def with_psql(f):
    def _with_psql(*args, **kwargs):
        conn = psycopg2.connect(
                database = app.config['DB_NAME'], 
                user = app.config['DB_USERNAME'],
                password = app.config['DB_PASSWORD'],
                host = app.config['DB_HOST'],
                port = app.config['DB_PORT']
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

def clean_data_folder():
    try:
        filelist = [f for f in os.listdir(app.config['DATA_DOWNLOAD_DIR_OS'])]
        for f in filelist:
            os.remove(app.config['DATA_DOWNLOAD_DIR_OS']+'/'+f)
    except OSError:
        pass

def paging(cur_pg, ent_cnt, max_ent, max_pg):
    npg = int(ent_cnt/max_ent)+1
    ps = int(max_pg/2)

    # next and previous pages
    pp = False
    np = False
    pr = None # current pages range

    if npg < max_pg:
        # 1, ... , npg
        pr = [1, npg+1]
    else:
        if cur_pg - ps <= 1:
            # 1, 2, ..., MAX_PG >>
            pr = [1, max_pg+1]
            np = cur_pg + max_pg + ps
        else:
            if cur_pg + ps >= npg:
                # << npg-MAX_PG-1, ..., npg
                pp = cur_pg - max_pg
                pr = [npg-max_pg-1, npg+1]
            else:
                # << cur_pg-ps, ... , cur_pg + ps >>
                pp = cur_pg - max_pg
                np = cur_pg + max_pg
                pr = [cur_pg-ps, cur_pg+ps+1]

    return [pp, pr, np]

def pend_base64_encode(arg, confid):
    argslen = len(arg) + 1
    args = bytearray(argslen + 2)
    args[0] = int(confid)
    args[1] = argslen

    bstr = bytes(arg.encode('utf-8'))
    i = 0
    while i < argslen - 1:
        args[2+i] = bstr[i]
        i += 1

    return binascii.b2a_base64(args).decode('utf-8')
