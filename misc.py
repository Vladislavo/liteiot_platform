from binascii import hexlify
import os

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
