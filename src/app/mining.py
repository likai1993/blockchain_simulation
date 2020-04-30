# coding:utf-8
from block import Block
import time
from transaction import Transaction
from account import Account
from storage import BlockChainDB, UnTransactionDB, TransactionDB
import json
REWARD = 20

class Miner():
    def __init__(self):
        self.publicKey = "" # account.publicKey #refer to the default account for the mining
        self.utx = []

    def reward(self):
        reward_transaction = Transaction('MINING', self.publicKey, REWARD)
        return reward_transaction

    def gensisBlock(self):
        reward_transaction = self.reward()
        gensis = Block(0, int(time.time()), [reward_transaction.dump()], "")
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
        newTransactions.append(rewardTx.dump())
        untxdb.clear()
        newBlock = Block(last_block['index'] + 1, int(time.time()), newTransactions, last_block['hash'])
        newBlock.miner = self.publicKey
        nouce = newBlock.pow()
        newBlock.make(nouce)
        # Save block and transactions to database.
        BlockChainDB().insert(newBlock.to_dict())
        TransactionDB().insert(newTransactions)
        return json.dumps(newBlock.to_dict(),indent=2)

if __name__ == '__main__':
    minerAcc = Account("test1")
    #minerAcc.create_account('123') ##password:123
    minerAcc.unlock_account('123')
    minerInstance = Miner(minerAcc)
    while True:
        print('New block generated')
        print(minerInstance.mine())
        time.sleep(10)
