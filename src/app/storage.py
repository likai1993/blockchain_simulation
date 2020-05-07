'''
File description:
Here is the Storage operation for the blockchain:
"Blockstore": will store the whole blockchain information
"Keystore": will store the accounts on this node
"Peerstore": will store the peer of this node
"TXstore": will store the detail of the transactions
"UTXstore": will the transactions not being included in the blockchain so far
"Account"
'''

# coding:utf-8
import json
import os
from transaction import Transaction
import Crypto.Random
import binascii
from ecdsa import SigningKey,VerifyingKey, NIST192p
BASEDBPATH = 'Data'
BLOCKFILE = 'Blockstore'
TXFILE = 'TXstore'
UNTXFILE = 'UTXpool'
NODEFILE = 'Node'  # for p2p module to store the peer node
ACCOUNT = 'Account'

def verify_transaction( transaction):
    public_key_str = transaction['sender'].decode("hex")
    public_key = VerifyingKey.from_string(public_key_str, curve=NIST192p)
    h = bytes(str(transaction['sender']) + str(transaction['receiver']) +
                    str(transaction['amount']) + str(transaction['time']))
    verify_result = public_key.verify(transaction['signature'].decode("hex"),h)
    return verify_result

class BaseDB():
    filepath = ''
    def __init__(self):
        self.set_path()
        self.filepath = '/'.join((BASEDBPATH, self.filepath))

    def set_path(self):
        pass

    def find_all(self):
        return self.read()

    def insert(self, item):
        self.write(item)

    def read(self):
        raw = ''
        if not os.path.exists(self.filepath):
            return []
        with open(self.filepath,'r+') as f:
            raw = f.readline()
        if len(raw) > 0:
            data = json.loads(raw)
        else:
            data = []
        return data

    def write(self, item):
        data = self.read()
        if isinstance(item,list):
            data = data + item
        else:
            data.append(item)
        with open(self.filepath,'w+') as f:
            f.write(json.dumps(data))
        return True

    def update(self,data):
        with open(self.filepath, 'w+') as f:
            f.write(json.dumps(data))

    def clear(self):
        with open(self.filepath,'w+') as f:
            f.write('')

    def hash_insert(self, item):
        #print("****",item)
        exists = False
        for i in self.find_all():
            if item['hash'] == i['hash']:
                exists = True
                break
        if not exists:
            self.write(item)
        return exists

    def sig_insert(self, item):
        exists = False
        for i in self.find_all():
            if item['signature'] == i['signature']:
                exists = True
                break
        if not exists:
            self.write(item)
        return exists

    def acc_rollback(self, tx):
        data = self.read
        for i in data:
            if i['publicKey'] == tx['receiver']:
                i['balance'] = i['balance'] - tx['amount']
                self.update(data)
                if tx['sender'] is not 'MINING':
                    if j['publicKey'] == tx['sender']:
                        j['balance'] = j['balance'] + tx['amount']
                        self.update(data)
                        break
                break


    def acc_insert(self,tx):
        exists = False
        data = self.read()
        for i in data:
            if i['publicKey'] == tx['receiver']:
                exists = True
                i['balance'] = i['balance'] + tx['amount']
                print("*********update******")
                self.update(data)

                if tx['sender'] is not 'MINING':
                    #print("sender update")
                    for j in data:
                        if j['publicKey'] == tx['sender']:
                            j['balance'] = j['balance'] - tx['amount']
                            self.update(data)
                            break
                break
        if not exists:
            new_acc = {'publicKey':tx['receiver'],'balance':tx['amount']}
            if tx['sender'] is not 'MINING':
                #print("sender update")
                for m in data:
                    if m['publicKey'] == tx['sender']:
                        m['balance'] = m['balance'] - tx['amount']
                        self.update(data)
                        break
            self.write(new_acc)


class NodeDB(BaseDB):

    def set_path(self):
        self.filepath = NODEFILE

class BlockChainDB(BaseDB):

    def set_path(self):
        self.filepath = BLOCKFILE

    def last(self):
        bc = self.read()
        if len(bc) > 0:
            return bc[-1]
        else:
            return []

    def updateByIndex(self, block):
        exist = False
        data = self.read()
        for i in data:
            if i['index'] == block['index']:
                if i['timestamp'] > block['timestamp']:
                # update block info
                    i = block
                    exist = True
                    self.update(data)
                elif i['timestamp'] == block['timestamp']:
                    if i['nouce'] < block['nouce']:
                        i = block
                        exist = True
                        self.update(data)
            if exist is True:
                #account balance rollback
                for tx in block['tx']:
                    AccountDB.acc_rollback(tx)
                break
                
        return exist


    def find(self, hash):
        one = {}
        for item in self.find_all():
            if item['hash'] == hash:
                one = item
                break
        return one

    def findIndex(self, index):
        one = {}
        for item in self.find_all():
            if item['index'] == index:
                one = item
                break
        return one

    def insert(self, item):
        self.hash_insert(item)

    def verify(self, block):
        valid = True
        current_height=0
        last_block = self.last()
        if len(last_block) > 0:
            current_height=last_block['index']
        if block['index'] > current_height:
            newTransactions = block['tx']
            BlockChainDB().insert(block)
            if TransactionDB().verify(newTransactions):
                TransactionDB().insert(newTransactions)
                for tx in newTransactions:
                    UnTransactionDB().delete(tx['hash'])
            else:
                valid = False
        elif block['index'] >= current_height - 6:
            #Todo: replace the block
            valid = self.updateByIndex(block)
        else:            
            valid = False 
        return valid 

class AccountDB(BaseDB):
    def set_path(self):
        self.filepath = ACCOUNT

    def insert(self, txs):
        if not isinstance(txs,list):
            txs = [txs]
        for tx in txs:
            self.acc_insert(tx)

    def getAccountBalance(self,account):
        balance=0
        for item in self.find_all():
            if item['publicKey'] == account:
                #print("findit", item)
                balance = item['balance']
                break
        return balance 

class TransactionDB(BaseDB):

    def set_path(self):
        self.filepath = TXFILE

    def find(self, hash):
        one = {}
        for item in self.find_all():
            if item['hash'] == hash:
                one = item
                break
        return one

    def exists(self, hash):
        ret = False 
        for item in self.find_all():
            if item['hash'] == hash:
                ret = True
                break
        return ret 

    def verify(self, txs):
        validTxs=[]
        if not isinstance(txs, list):
            txs = [txs]
        for tx in txs:
            if tx['sender'] == 'MINING':
                if (not self.exists(tx)) and (tx not in validTxs):
                    validTxs.append(tx)
                else:
                    return None 
            else:
                #print("user tx", tx)
                sender_balance = AccountDB().getAccountBalance(tx['sender'])
                if sender_balance >= tx['amount'] and verify_transaction(tx):
                    if (not self.exists(tx)) and (tx not in validTxs):
                        validTxs.append(tx)
                    else:
                        return None 
                else:
                   return None
        return validTxs 

    def insert(self, txs):
        if not isinstance(txs, list):
            txs = [txs]
        for tx in txs:
            if tx['sender'] == 'MINING':
                self.hash_insert(tx)
                AccountDB().acc_insert(tx)
            else:
                self.hash_insert(tx)
                AccountDB().acc_insert(tx)
        return True 

class UnTransactionDB(TransactionDB):

    def set_path(self):
        self.filepath = UNTXFILE

    def all_hashes(self):
        hashes = []
        for item in self.find_all():
            hashes.append(item['hash'])
        return hashes

    def insert(self, txs):
        if not isinstance(txs, list):
            txs = [txs]
        for tx in txs:
            self.hash_insert(tx)

    def find(self, hash):
        one = {}
        for item in self.find_all():
            if item['hash'] == hash:
                one = item
                break
        return one

    def delete(self, hash):
	data = []
	for item in self.find_all():
            if item['hash'] == hash:
                continue
            else:
                data.append(item)
        self.insert(data)
