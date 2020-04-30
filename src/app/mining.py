# coding:utf-8
from block import Block
import time
from transaction import Transaction
from account import Account
from storage import BlockChainDB, UnTransactionDB, TransactionDB
import json

from twisted.internet import reactor
from log import _print
import network
from network import NCProtocol

REWARD = 20

class Miner():
    def __init__(self, protocol):
        self.publicKey = "" # account.publicKey #refer to the default account for the mining
        self.utx = []
        self.protocol = protocol

    def reward(self):
        reward_transaction = Transaction('MINING', self.publicKey, REWARD)
        return reward_transaction

    def gensisBlock(self):
        reward_transaction = self.reward()
        gensis = Block(0, int(time.time()), [reward_transaction.to_dict()], "")
        nouce = gensis.pow()
        gensis.make(nouce)
        print(gensis.to_dict())
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
        newBlock = Block(last_block['index'] + 1, int(time.time()), newTransactions, last_block['hash'])
        newBlock.miner = self.publicKey
        nouce = newBlock.pow()
        newBlock.make(nouce)
        # Save block and transactions to database.
        BlockChainDB().insert(newBlock.to_dict())
        TransactionDB().insert(newTransactions)

        return newBlock.to_dict()

    def startMining(self):
        while True:
            newBlock = self.mine()
            _print(' [MINER] Mined new block:', newBlock['index'])
            reactor.callFromThread(self.protocol.broadcastBlock, newBlock)
            time.sleep(10)
