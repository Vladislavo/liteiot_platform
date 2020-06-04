import msgpack
import struct
from collections import OrderedDict
import json

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

def read_data_ddm(data, ddm):
    if ddm['model'] == 'mpack':
        return msgpack.unpackb(data)
    elif ddm['model'] == 'raw':
        upstr = ddm['endianness'] + ''.join(dict(ddm['format']).values())
        data = struct.unpack(upstr, data)
        data = dict(zip(ddm['format'].keys(), data))
        for k, v in ddm['format'].items():
            if v[-1] == 's':
                data[k] = data[k].decode('utf-8')
        return data 
    elif ddm['model'] == 'json':
        return json.loads(data.decode('utf-8'))

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
