# rename to cryptotools

import os
import hashlib

def generate_nodeid():
    a= os.urandom(int(256/8))
    b=hashlib.sha256(a).hexdigest()
    return b
