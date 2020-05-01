import hmac
import json
import cryptotools

# generate_nodeid() uses SHA256 so this will prevent replay-attacks,
# because every message will have a different nonce.
# It's not nessecary to compare the nonce, HMAC already gives message
# integrety.
nonce = lambda: cryptotools.generate_nodeid()
incr_nonce = lambda env: format(int(env["nonce"], 16) + 1, 'x')

class InvalidSignatureError(Exception):
    pass

class InvalidNonceError(Exception):
    pass

def make_envelope(msgtype, msg, nodeid):
    msg['nodeid'] = nodeid
    msg['nonce'] =  nonce()
    data = json.dumps(msg)
    sign = hmac.new(nodeid, data)
    envelope = {'data': msg,
                'sign': sign.hexdigest(),
                'msgtype': msgtype}
    return json.dumps(envelope)

def envelope_decorator(nodeid, func):
    msgtype = func.__name__.split("_")[0]
    def inner(*args, **kwargs):
        return make_envelope(msgtype, func(*args, **kwargs), nodeid)
    return inner

# ------
def create_ackhello(nodeid):
    msg = {}
    return make_envelope("ackhello", msg, nodeid)

def create_hello_1(nodeid, lsnport, version):
    msg = {'version': version,
	   'listenPort': lsnport
	}
    return make_envelope("hello", msg, nodeid)

def create_hello(nodeid, version):
    msg = {'version': version
	}
    return make_envelope("hello", msg, nodeid)

def create_ping(nodeid):
    msg = {}
    return make_envelope("ping", msg, nodeid)

def create_pong(nodeid):
    msg = {}
    return make_envelope("pong", msg, nodeid)

def create_getaddr(nodeid):
    msg = {}
    return make_envelope("getaddr", msg, nodeid)

def create_addr(nodeid, nodes):
    msg = {'nodes': nodes}
    return make_envelope("addr", msg, nodeid)

## APP
def createTxMsg(nodeid, tx):
    msg = {'tx':tx}
    return make_envelope("tx", msg, nodeid)

def createBlockMsg(nodeid, block):
    msg = {'block':block}
    return make_envelope("block", msg, nodeid)

# -------

def read_envelope(message):
    return json.loads(message)

def read_message(message):
    """Read and parse the message into json. Validate the signature
    and return envelope['data']
    """
    envelope = json.loads(message)
    nodeid = str(envelope['data']['nodeid'])
    signature = str(envelope['sign'])
    msg = json.dumps(envelope['data'])
    verify_sign = hmac.new(nodeid, msg)
    #print "read_message:", msg
    if hmac.compare_digest(verify_sign.hexdigest(), signature):
        return envelope['data']
    else:
        raise InvalidSignatureError

def read_message_noverify(message):
    """Read and parse the message into json. Validate the signature
    and return envelope['data']
    """
    envelope = json.loads(message)
    return envelope['data']