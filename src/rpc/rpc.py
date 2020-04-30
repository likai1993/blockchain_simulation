import pyjsonrpc
from log import _print
from account import Account
from mining import Miner
from storage import BlockChainDB, AccountDB, TransactionDB

class RequestHandler(pyjsonrpc.HttpRequestHandler):

    @pyjsonrpc.rpcmethod
    def createAccount(self, _name, passwd):
        self.account.name = _name
        self.account.create_account(passwd)

    @pyjsonrpc.rpcmethod
    def unlock(self, _name, passwd):
        self.account.name = name
        self.account.unlock(passwd)
        return True

    @pyjsonrpc.rpcmethod
    def sendTransaction(self, _to, _amount):
        transaction = self.account.createTransaction(_to, int(_amount))
        self.account.sign_transaction(transaction)
        self.account.submitTransaction(transaction)
        return True

    # read-only
    @pyjsonrpc.rpcmethod
    def getBalance(self, address): #publickey
        print(AccountDB().getBalance(address))
        return True

    @pyjsonrpc.rpcmethod
    def getTransaction(self, _hash):
        print(TransactionDB().find(_hash))
        return True

    @pyjsonrpc.rpcmethod
    def getBlock(self, height):
        print(BlockChainDB().findIndex(height))
        return 

    @pyjsonrpc.rpcmethod
    def getBlockByHash(self, _hash):
        print(BlockChainDB().find(_hash))
        return 

# Threading HTTP-Server
class RPC(object):
    def __init__(self, ip, port, protocol):
        self.http_server = pyjsonrpc.ThreadingHttpServer(
        server_address = (ip, port),
        RequestHandlerClass = RequestHandler)
        _print(" [RPC] Starting RPC server ...")
        _print(" [RPC] URL: http://" + ip + ":" + str(port))
        self.account=Account()
        self.miner=Miner()
        self.protocol = protocol
        self.http_server.serve_forever()
