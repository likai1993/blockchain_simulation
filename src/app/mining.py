# coding:utf-8
import time, thread
import json

from twisted.internet import reactor
from log import _print
import network
from network import NCProtocol

from block import Block
from transaction import Transaction
from account import Account
from storage import BlockChainDB, UnTransactionDB, TransactionDB
import hashlib

REWARD = 20

class Miner():
    def __init__(self, protocol):
        self.publicKey = "" # account.publicKey #refer to the default account for the mining
        self.utx = []
        self.protocol = protocol
        self.running=False
        thread.start_new_thread(self.MiningWorker, ())

    def reward(self):
	_hash = hashlib.sha256((str(time.time())).encode('utf8')).hexdigest()
        reward_transaction = Transaction('MINING', self.publicKey, REWARD)
        reward_transaction.hash = _hash
        return reward_transaction

    def gensisBlock(self):
        reward_transaction = self.reward()
        gensis = Block(0, int(time.time()), [reward_transaction.to_dict()], "")
        nouce = gensis.pow()
        gensis.make(nouce)
        #_print(' [MINER] Genesis:',gensis.to_dict())
        # Save block and transactions to database.
        BlockChainDB().insert(gensis.to_dict())

        return gensis

    def mine(self):
        last_block = BlockChainDB().last()
        if len(last_block) == 0:
            last_block = self.gensisBlock().to_dict()
        untxdb = UnTransactionDB()
        rewardTx = self.reward()
        newTransactions = untxdb.find_all()
        newTransactions.append(rewardTx.to_dict())
        untxdb.clear()
        validTxs = TransactionDB().verify(newTransactions)
        newBlock = Block(last_block['index'] + 1, int(time.time()), validTxs, last_block['hash'])
        newBlock.miner = self.publicKey
        nouce = newBlock.pow()
        newBlock.make(nouce)

		#TransactionDB().insert(validTxs)
        # Save block and transactions to database.
        BlockChainDB().verify(newBlock.to_dict())

        return newBlock.to_dict()

    def stopMining(self):
        if self.running == True:
            _print(' [MINER] Worker stops..')
        self.running = False

    def startMining(self):
        self.running = True

    def MiningWorker(self):
        while True:
            if self.running:
                newBlock = self.mine()
                _print(' [MINER] Mined new block:', newBlock['index'])
                reactor.callFromThread(self.protocol.broadcastBlock, newBlock)
                time.sleep(10)
