import msgpack
import struct
from collections import OrderedDict
import json
import app.helpers.misc as misc
from psycopg2 import Binary
from datetime import datetime

MODELS = {
    'json' : 'JSON',
    'mpack' : 'MessagePack',
    'raw' : 'raw bytes'
}

def test_dev():
    # Aim: support 3 data models:
    #  1) JSON (already supported) - no ddm
    #  2) msgpack - no ddm
    #  3) raw bytes - ddm

    # to be stored in db
    ddm = {
        'model': 'json'
    }

    data = {
        'some_int': 45,
        'some_float': 20.5,
        'some_bool': True,
        'some_str': 'foo:bar'
    }
    print ('Normal JSON:')       
    print (data)


    # to be stored in db
    ddm = {
        'model': 'mpack'
    }

    mpdata = msgpack.packb(data)
    print('msgpack packed:')
    print(mpdata)
    print('msgpack unpacked:')
    print(msgpack.unpackb(mpdata))

    # to be stored in db
    ddm = {
        'model' : 'raw',
        'endianness': '<',
        'format' : OrderedDict([('some_int', 'H'), ('some_float', 'f'), ('some_bool', '?'), ('some_str', '7s')])
    }
    print(''.join(dict(ddm['format']).values())) 
    for k, v in ddm['format'].items():
        if v[-1] == 's':
            print (v, k)

    # endianess: little
    # uint16_t some_int    = 45;        // 2 bytes
    # float    some_float  = 20.5;      // 4
    # uint8_t  some_bool   = 1;         // 1
    # char     some_str[8] = "foo:bar"; // 8

    #        | uint16 |     float     | b |             str               |
    rdata = b'\x2d\x00\x00\x00\xa4\x41\x01\x66\x6f\x6f\x3a\x62\x61\x72'

    print ('raw data:')
    print (rdata)
    print ('raw data unpacked:')
    print (struct.unpack('<Hf?7s', rdata))
    ru = struct.unpack('<Hf?7s', rdata)
    dru = dict(zip(['some_int','some_float','some_bool','some_str'],ru))
    dru['some_str'] = dru['some_str'].decode('utf-8')
    print ('raw data json:')
    print (dru)

def test_done():
    print ('test with json:')
    ddm = {
        'model': 'json'
    }
    print(read_data_ddm(json.dumps(data).encode('utf-8'), ddm))

    print ('test with mpack:')
    ddm = {
        'model': 'mpack'
    }
    print(read_data_ddm(mpdata, ddm))

    print ('test with raw:')
    ddm = {
        'model' : 'raw',
        'endianness': '<',
        'format' : OrderedDict([('some_int', 'H'), ('some_float', 'f'), ('some_bool', '?'), ('some_str', '7s')])
    }
    print(read_data_ddm(rdata, ddm))

@misc.with_psql
def mpack_test(cur):
    import random
    
    m = {
            "temperature" : random.randint(0, 100),
            "lever": random.randint(0,1)
        }
    m = msgpack.packb(m)
    query = """
        INSERT INTO dev_3b56f3d8_3 VALUES ({}, '{}', {})
    """.format(misc.get_utc(), datetime.now().strftime('%H:%M:%S'), Binary(m))
    print (query)
    cur.execute(query)
    
    return (True,)


@misc.with_psql
def raw_test(cur):
    import random
    
    upstr = '<fQ20s?h'
    m = struct.pack(upstr, random.random()*1000, random.randint(10000,10000000), 'hello'.encode('utf-8'), random.randint(0,2), random.randint(0, 30000))
    query = """
        INSERT INTO dev_3b56f3d8_2 VALUES ({}, '{}', {})
    """.format(misc.get_utc(), datetime.now().strftime('%H:%M:%S'), Binary(m))
    cur.execute(query)
    
    return (True,)


def decode_datum(data, ddm):
    data = [d for d in data]
    data[2] = read_data(data[2].tobytes(), ddm)
    return data

def read_data(data, ddm):
    if ddm['model'] == 'mpack':
        return msgpack.unpackb(data)
    elif ddm['model'] == 'raw':
        upstr = ddm['endianness'] + ''.join(dict(ddm['format']).values())
        data = struct.unpack(upstr, data)
        data = dict(zip(ddm['format'].keys(), data))
        for k, v in ddm['format'].items():
            if v[-1] == 's':
                data[k] = data[k].decode('utf-8')
                data[k] = data[k][:data[k].index('\0')]
        return data 
    elif ddm['model'] == 'json':
        return json.loads(data.decode('utf-8'))


def extract(request):
    ddmin = {'model':request.form['ddm'], 'format':{}}
    try:
        ddmin['endianness'] = request.form['endianness']
    except:
        pass

    # create dict with variables
    for k,v in request.form.items():
        if k.startswith("var"):
            i = k.split("_")
            if not int(i[1]) in ddmin['format']:
                ddmin['format'][int(i[1])] = { i[0][3:] : v }
            else:
                ddmin['format'][int(i[1])][i[0][3:]] = v
    # format size
    for k,v in ddmin['format'].items():
        if 'size' in v:
            ddmin['format'][k]['type'] = v['size'] + 's'
            ddmin['format'][k].pop('size')
    # order dict
    od = OrderedDict(sorted(ddmin['format'].items()))
    ddmin.pop('format')
    ddmin['format'] = OrderedDict()
    # give it defined ddm format
    for k,v in od.items():
        ddmin['format'][v['name']] = v['type']

    return ddmin

print('mpack insert', mpack_test())
print('raw insert', raw_test())
