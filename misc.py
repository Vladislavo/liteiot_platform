from binascii import hexlify
import os

def rand_str(length):
    if length % 2 == 0:
        return hexlify(os.urandom(length//2))
    else:
        return hexlify(os.urandom(length//2 + 1))
