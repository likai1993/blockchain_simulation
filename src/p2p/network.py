from datetime import datetime
from time import time
from functools import partial
from log import _print
import json
from storage import BlockChainDB, UnTransactionDB, TransactionDB

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet.endpoints import connectProtocol
from twisted.internet.task import LoopingCall

from log import _print

import messages
import cryptotools

PING_INTERVAL = 20.0 # seconds 
BOOTSTRAP_NODES = [ 
                  "192.168.53.5:5555"]

class NCProtocol(Protocol):
    def __init__(self, factory, state="GETHELLO", kind="INBOUND"):
        self.factory = factory
        self.state = state
        self.VERSION = 0
        self.remote_nodeid = None
        self.kind = kind
        self.nodeid = self.factory.nodeid
        self.lsnport = self.factory.lsnport
        self.lc_ping = LoopingCall(self.send_PING)
        self.message = partial(messages.envelope_decorator, self.nodeid)

    def dumpClient(self):
        if len(self.factory.clients) > 0:
            _print(" [p2p] Connected clients")
            for clients in self.factory.clients: 
                _print("    ", clients.remote_ip)

    def connectionMade(self):
        r_ip = self.transport.getPeer()
        h_ip = self.transport.getHost()
        self.remote_ip = r_ip.host + ":" + str(r_ip.port)
        self.host_ip = h_ip.host + ":" + str(h_ip.port)
        self.factory.clients.append(self)
        self.dumpClient()
        self.factory.knownTxs[self.remote_ip]=[] # avoid re-propagation, TODO size protection
        self.factory.knownBlocks[self.remote_ip]=[] # avoid re-propagation, TODO size protection

    def print_peers(self):
        if len(self.factory.peers) == 0:
            _print(" [!] PEERS: No peers connected.")
        else:
            _print(" [P2P] PEERS:")
            for peer in self.factory.peers:
                addr, kind = self.factory.peers[peer][:2]
                _print("     [*]", peer, "at", addr, kind)

    def write(self, line):
        self.transport.write(line + "\n")

    def connectionLost(self, reason):
        # NOTE: It looks like the NCProtocol instance will linger in memory
        # since ping keeps going if we don't .stop() it.
        try: self.lc_ping.stop()
        except AssertionError: pass

        try:
            self.factory.peers.pop(self.remote_nodeid)
            if self.nodeid != self.remote_nodeid:
                self.print_peers()
        except KeyError:
            if self.nodeid != self.remote_nodeid:
                _print(" [P2P] CLIENTS LEAVES: from", self.remote_nodeid, self.remote_ip)
                self.factory.clients.remove(self)
                self.dumpClient()

    def dataReceived(self, data):
        for line in data.splitlines():
            line = line.strip()
            try:
                envelopes = messages.read_envelope(line)
                for envelope in envelopes:
                    if self.state in ["GETHELLO", "SENTHELLO"]:
                        # Force first message to be HELLO or crash
                        if envelope['msgtype'] == 'hello':
                            self.handle_HELLO(json.dumps(envelope))
                        else:
                            _print(" [!] Ignoring", envelope['msgtype'], "in", self.state)
                    else:
                        if envelope['msgtype'] == 'ping':
                            self.handle_PING(json.dumps(envelope))
                        elif envelope['msgtype'] == 'pong':
                            self.handle_PONG(json.dumps(envelope))
                        elif envelope['msgtype'] == 'addr':
                            self.handle_ADDR(json.dumps(envelope))
                        elif envelope['msgtype'] == 'tx':
                            self.receiveTx(json.dumps(envelope))
                        elif envelope['msgtype'] == 'block':
                            self.receiveBlock(json.dumps(envelope))
            except:
                pass

    def send_PING(self):
        _print(" [>] PING   to", self.remote_nodeid, "at", self.remote_ip)
        ping = messages.create_ping(self.nodeid)
        self.write(ping)

    def handle_PING(self, ping):
        if messages.read_message(ping):
            pong = messages.create_pong(self.nodeid)
            self.write(pong)

    def send_ADDR(self):
        _print(" [>] Telling " + self.remote_nodeid + " about my peers")
        # Shouldn't this be a list and not a dict?
        peers = self.factory.peers
        listeners = [(n, peers[n][0], peers[n][1], peers[n][2])
                     for n in peers]
        addr = messages.create_addr(self.nodeid, listeners)
        self.write(addr)

    def handle_ADDR(self, addr):
        try:
            nodes = messages.read_message(addr)['nodes']
            _print(" [<] Recieved addr list from peer " + self.remote_nodeid)
            #for node in filter(lambda n: nodes[n][1] == "SEND", nodes):
            for node in nodes:
                _print("     [*] "  + node[0] + " " + node[1])
                host, port = node[1].split(":")
                remote_lsnport = str(node[2])
                if node[0] == self.nodeid:
                    _print(" [!] Not connecting to " + node[0] + ": thats me!")
                    continue
                if node[3] == "INBOUND":
                    port = remote_lsnport
                    _print(" [P2P] INBOUND connecting to " + host + ":" + remote_lsnport)
                if node[0] in self.factory.peers:
                    _print(" [P2P] Not connecting to " + node[0]  + ": already connected")
                    continue
                _print(" [P2P] Trying to connect to peer " + node[0] + " " + node[1])
                point = TCP4ClientEndpoint(reactor, host, int(port))
                d = connectProtocol(point, NCProtocol(self.factory, "SENDHELLO", "OUTBOUND"))
                d.addCallback(runProtocol)

        except messages.InvalidSignatureError:
            print(addr)
            _print(" [!] ERROR: Invalid addr sign ", self.remote_ip)
            self.transport.loseConnection()

    def handle_PONG(self, pong):
        pong = messages.read_message(pong)
        _print(" [<] PONG from", self.remote_nodeid, "at", self.remote_ip)
        # hacky
        addr, kind, listenPort = self.factory.peers[self.remote_nodeid][:3]
        self.factory.peers[self.remote_nodeid] = (addr, kind, listenPort, time())

    def send_HELLO(self):
        hello = messages.create_hello_1(self.nodeid, self.lsnport, self.VERSION)
        _print(" [P2P] SEND_HELLO:", self.nodeid, "to", self.remote_ip)
        self.transport.write(hello + "\n")
        self.state = "SENTHELLO"

    def handle_HELLO(self, hello):
        try:
            hello = messages.read_message(hello)
            self.remote_nodeid = hello['nodeid']
            self.remote_lsnport = hello['listenPort']
            if self.remote_nodeid == self.nodeid:
                _print(" [!] Found myself at", self.host_ip)
                self.transport.loseConnection()
            else:
                if self.state == "GETHELLO":
                    my_hello = messages.create_hello_1(self.nodeid, self.lsnport, self.VERSION)
                    self.transport.write(my_hello + "\n")
                self.add_peer()
                self.state = "READY"
                self.print_peers()
                #self.write(messages.create_ping(self.nodeid))
                if self.kind == "INBOUND":
                    # The listener pings it's audience
                    _print(" [P2P] Starting pinger to " + self.remote_nodeid)
                    self.lc_ping.start(PING_INTERVAL, now=False)
                    # Tell new audience about my peers
                    self.send_ADDR()
        except messages.InvalidSignatureError:
            _print(" [!] ERROR: Invalid hello sign ", self.remoteip)
            self.transport.loseConnection()

    def add_peer(self):
        entry = (self.remote_ip, self.remote_lsnport, self.kind, time())
        self.factory.peers[self.remote_nodeid] = entry

    def receiveTx(self, msg):
        try:
            newTx = messages.read_message_noverify(msg)['tx']
            _print(" [<] Recieve tx=" + newTx['hash'] +" from peer " + self.remote_nodeid)
            UnTransactionDB().insert(newTx)
            self.factory.knownTxs[self.remote_ip].append(newTx['hash'])
            # propagate to the unknown peers
            for client in self.factory.clients:
                if newTx['hash'] not in self.factory.knownTxs[client.remote_ip]:
                    client.transport.write(msg)

        except messages.InvalidSignatureError:
            _print(" [!] ERROR: Invalid tx sign ", self.remote_ip)
            self.transport.loseConnection()

    def receiveBlock(self, msg):
        try:
            newBlock = messages.read_message_noverify(msg)['block']
            _print(" [<] Recieve block="+newBlock['hash']+" from peer " + self.remote_nodeid+", index="+ str(newBlock['index']) + ", timestamp="+ str(newBlock['timestamp']) + ", miner="+str(newBlock['miner']))
            if BlockChainDB().verify(newBlock):
                self.factory.knownBlocks[self.remote_ip].append(newBlock['hash'])
                # only propagate valid block to peers 
                for client in self.factory.clients:
                    if newBlock['hash'] not in self.factory.knownBlocks[client.remote_ip]:
                        client.transport.write(msg)

        except messages.InvalidSignatureError:
            _print(" [!] ERROR: Invalid block sign ", self.remote_ip)
        except:
            pass

    def broadcastTx(self, tx):
        _print(" [P2P] Broadcast tx=", tx['hash'])
        txMsg=messages.createTxMsg(self.nodeid, tx)
        for client in self.factory.clients: 
            client.transport.write(txMsg)
            client.factory.knownTxs[client.remote_ip].append(tx['hash'])

    def broadcastBlock(self, block):
        _print(" [P2P] Broadcast block="+str(block['hash'])+", index="+ str(block['index'])+", miner="+str(block['miner']))
        blockMsg=messages.createBlockMsg(self.nodeid, block)
        for client in self.factory.clients: 
            client.transport.write(blockMsg)
            client.factory.knownBlocks[client.remote_ip].append(block['hash'])

# Split into NCRecvFactory and NCSendFactory (also reconsider the names...:/)
class NCFactory(Factory):
    def __init__(self, port):
        self.lsnport = port
        pass

    def startFactory(self):
        self.peers = {}
        self.clients = [] 
        self.knownBlocks = {} 
        self.knownTxs = {} 
        self.numProtocols = 0
        self.nodeid = cryptotools.generate_nodeid()[:10]
        _print(" [P2P] NODEID:", self.nodeid)

    def stopFactory(self):
        pass

    def buildProtocol(self, addr):
        return NCProtocol(self, "GETHELLO", "INBOUND")

def runProtocol(p):
    # ClientFactory instead?
    p.send_HELLO()
