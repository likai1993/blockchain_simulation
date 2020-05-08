#!/usr/bin/python2.7
import sys
sys.path.append("./p2p")
sys.path.append("./rpc")
sys.path.append("./vpn")
sys.path.append("./app")

import argparse
from datetime import datetime
import thread, time

from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.internet.error import CannotListenError
from twisted.internet.endpoints import connectProtocol

from log import _print
import network
from network import NCFactory, NCProtocol

from rpc import RPC
from vpnclient import setUpVPNClient

DEFAULT_PORT = 5555
DEFAULT_RPCPORT = 8888

parser = argparse.ArgumentParser(description="blockchain_simulation")
parser.add_argument('--port', type=int, default=DEFAULT_PORT)
parser.add_argument('--rpcport', type=int, default=DEFAULT_RPCPORT)
parser.add_argument('--listen', default="192.168.53.5")
parser.add_argument('--imAddr', default="128.230.208.73")
parser.add_argument('--imPort', default=55555)
parser.add_argument('--bootstrap', action="append", default=[])

def protoBroadcast(_protocol, data):
    while (True):
        reactor.callFromThread(_protocol.broadcastTx, data)
        time.sleep(2)

if __name__ == "__main__":
    args = parser.parse_args()
    try:
        thread.start_new_thread(setUpVPNClient, (args.listen, args.imAddr, args.imPort, ))
        time.sleep(1)
        endpoint = TCP4ServerEndpoint(reactor, args.port, interface=args.listen)
        _print(" [P2P] LISTEN ON:", args.listen, ":", args.port)
        ncfactory = NCFactory(args.port)
        endpoint.listen(ncfactory)

    except CannotListenError:
        _print("[!] Address in use")
        raise SystemExit

    # connect to bootstrap addresses
    _print(" [P2P] Trying to connect to bootstrap hosts:")
    for bootstrap in network.BOOTSTRAP_NODES + [a+":"+str(DEFAULT_PORT) for a in args.bootstrap]:
        _print("     [*] ", bootstrap)
        host, port = bootstrap.split(":")
        point = TCP4ClientEndpoint(reactor, host, int(port))
        protocol = NCProtocol(ncfactory, "SENDHELLO", "OUTBOUND")
        d=connectProtocol(point, protocol)
        d.addCallback(network.runProtocol)
        #thread.start_new_thread(protoBroadcast, (protocol, "<<<<TX>>>>",))
	# start application
        thread.start_new_thread(RPC, (args.listen, args.rpcport, protocol,))
    reactor.run()
