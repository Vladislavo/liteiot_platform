from app import app
from flask import session,flash,redirect,url_for
from binascii import hexlify
import os
import psycopg2
import binascii
from datetime import datetime

import collections
import json


USER_LEVELS = {
    # user can only see applications and devices as interface.
    'interface' : 0,       
    # user has the control over all user aspects. CRUD:applications+devices+alarms+automation + device configuration and data download
    'user'      : 40, 
    # + CRUD:user expect admins
    'admin'     : 80,
    # total control (1 superuser per platform)
    'superuser' : 100
}

def grant_view(require, wants):
    return USER_LEVELS[require] <= USER_LEVELS[wants]
app.jinja_env.globals.update(grant_view=grant_view)

def rand_str(length):
    if length % 2 == 0:
        return hexlify(os.urandom(length//2))
    else:
        return hexlify(os.urandom(length//2 + 1))

def gen_skey_b64(nbytes):
    return binascii.b2a_base64(os.urandom(nbytes)).decode('utf-8')

def skey_b64_to_hex(b64_skey):
    return hexlify(binascii.a2b_base64(b64_skey))

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

def utc_roundhour(hour_offset = 0):
    n = datetime.utcnow()
    return int((datetime(n.year, n.month, n.day, n.hour) - datetime(1970,1,1,hour_offset)).total_seconds())


def utc_roundday(day_offset = 0):
    n = datetime.utcnow()
    return int((datetime(n.year, n.month, n.day) - datetime(1970,1,1+day_offset)).total_seconds())


def utc_hour(hour_offset):
    return ((datetime.utcnow().hour - hour_offset) % 24)

def utc_weekday(day_offset = 0):
    d = {0:'Mo',1:'Tu',2:'We',3:'Th',4:'Fr',5:'Sa',6:'Su'}
    return (d[((datetime.utcnow().weekday() - day_offset) % 7)])

def local_hour(hour_offset):
    return ((datetime.now().hour - hour_offset) % 24)

def local_weekday(day_offset = 0):
    d = {0:'Mo',1:'Tu',2:'We',3:'Th',4:'Fr',5:'Sa',6:'Su'}
    return (d[((datetime.now().weekday() - day_offset) % 7)])

def utc_local_diff():
    return abs((datetime.now() - datetime.utcnow()).total_seconds())

def get_utc():
    return int((datetime.now() - datetime(1970,1,1)).total_seconds())
