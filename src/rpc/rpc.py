import pyjsonrpc
import thread
from log import _print
from account import Account
from mining import Miner
from storage import BlockChainDB, AccountDB, TransactionDB,UnTransactionDB

class RequestHandler(pyjsonrpc.HttpRequestHandler):

    @pyjsonrpc.rpcmethod
    def createAccount(self, _name, _passwd):
        publicKey = self.server.account.create_account(_name, _passwd)
	return publicKey

    @pyjsonrpc.rpcmethod
    def loadAccount(self, _name, _passwd):
	print("Keep your key file inside keystore dir")
        publicKey = self.server.account.unlock(_name, _passwd)
        return publicKey   

    @pyjsonrpc.rpcmethod
    def unlock(self, _name, _passwd):
        publicKey = self.server.account.unlock(_name, _passwd)
        return publicKey

    @pyjsonrpc.rpcmethod
    def mining(self, _name, _passwd):
        self.server.account.unlock(_name, _passwd)
        self.server.miner.publicKey = self.server.account.publicKey
        self.server.miner.startMining()
        return True

    @pyjsonrpc.rpcmethod
    def stopMining(self):
        self.server.miner.stopMining()
        return True

    @pyjsonrpc.rpcmethod
    def sendTransaction(self, _to, _amount):
        transaction = self.server.account.createTransaction(_to, int(_amount))
        self.server.account.sign_transaction(transaction)
        return self.server.account.submitTransaction(transaction)

    # read-only
    @pyjsonrpc.rpcmethod
    def getBalance(self, address): #publickey
        return AccountDB().getAccountBalance(address)

    @pyjsonrpc.rpcmethod
    def getTransaction(self, _hash):
        tx = UnTransactionDB().find(_hash)
        if tx == {}:
            print "not in UTXpool"
            tx = TransactionDB().find(_hash)
            if tx == {}:
                return  "no Record"
        return tx	

    @pyjsonrpc.rpcmethod
    def getBlock(self, _height):
        return BlockChainDB().findIndex(_height)

    @pyjsonrpc.rpcmethod
    def getBlockByHash(self, _hash):
        return BlockChainDB().find(_hash)

# Threading HTTP-Server
class RPC(object):
    def __init__(self, ip, port, protocol):
        http_server = pyjsonrpc.ThreadingHttpServer(
        server_address = (ip, port),
        RequestHandlerClass = RequestHandler)

        http_server.account = Account(protocol)
        http_server.miner = Miner(protocol)
        _print(" [RPC] Starting RPC server ...")
        _print(" [RPC] URL: http://" + ip + ":" + str(port))
        http_server.serve_forever()
