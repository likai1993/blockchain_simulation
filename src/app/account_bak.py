#Description:
#Create account: with public key, secret key and store it in key storage
#Unlock the account: get the secret key
#Sign a transaction
#Verify the transaction

import sys
sys.path.append("../p2p")
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import Crypto.Random
import binascii
from os import stat, remove
import json
import os
import hashlib
from storage import UnTransactionDB, AccountDB
from transaction import Transaction
import file_enc_dec as filecrypto
from ecdsa import SigningKey,VerifyingKey, NIST384p

from twisted.internet import reactor
from log import _print
import network
from network import NCProtocol

# encryption/decryption buffer size - 64K

class Account():

    def __init__(self, protocol, name=""):
        self.name = name
        self.publicKey = ""
        self.privateKey = ""
        self.protocol = protocol

    def to_dict(self):
        return self.__dict__

    def generate_keys(self):
	private_key = SigningKey.generate(curve=NIST384p)
        public_key = private_key.verifying_key
        return private_key.to_string().encode("hex"), public_key.to_string().encode("hex")
    
    def create_account(self, name, pwd):
        self.name = name
        bufferSize = 64 * 1024
        privateKey, publicKey = self.generate_keys()
        keys = {'publicKey': publicKey, 'privateKey':privateKey}
        path = 'Data/Keystore/'
        fileName = path + str(self.name)+'tmp'
        with open(fileName, 'w') as json_file:
            json.dump(keys, json_file)
        #pyAesCrypt.encryptFile(fileName, path+str(self.name), pwd, bufferSize)
        filecrypto.encrypt_file(pwd, fileName, path+str(self.name))
        #print(keys)
        remove(fileName)
        # account transaction...
	return publicKey

    def unlock(self, name, pwd):
        self.name = name
        bufferSize = 64 * 1024
        path = 'Data/Keystore/'
        fileName = path + str(self.name)
        encFileSize = stat(fileName).st_size
        tmpfile = fileName+"tmp"
        #pyAesCrypt.decryptFile(fileName, tmpfile, pwd, bufferSize)
        filecrypto.decrypt_file(pwd, fileName, tmpfile)
        try:
            with open(tmpfile, "rb") as f:
                data = json.load(f)
                remove(tmpfile)
                self.publicKey = data['publicKey']
                self.privateKey = data['privateKey']
                return data['publicKey']
        except:
            print("account not exist!")
            return "not exist!"

    def relock(self):
        self.publicKey = ""
        self.privateKey = ""

    def import_account(self, privateKey, publicKey, pwd):
        bufferSize = 64 * 1024
        keys = {'publicKey': publicKey, 'privateKey':privateKey}
        path = 'Data/Keystorage/'
        fileName = path + str(self.name)+'tmp'
        with open(fileName, 'w') as json_file:
            json.dump(keys, json_file)
        pyAesCrypt.encryptFile(fileName, path+str(self.name), pwd, bufferSize)
        remove(fileName)

    def createTransaction(self, receiver, amount):
        sender = self.publicKey
        return Transaction(sender,receiver,amount)



    def sign_transaction(self, transaction):
        if self.privateKey is not "":
            signer_str = self.privateKey.decode("hex")
            signer = SigningKey.from_string(signer_str, curve=NIST384p)
            h = str(transaction.sender)+str(transaction.receiver)+str(transaction.amount)+str(transaction.time)
            print("*****",h)
            signature = signer.sign(bytes(h))
            #transaction.signature = binascii.hexlify(signature).decode('ascii')
            transaction.signature = signature.encode("hex")
            transaction.hash = hashlib.sha256((str(transaction.sender)+str(transaction.receiver)+str(transaction.amount)+str(transaction.time)).encode('utf8')).hexdigest()
            return transaction
        else:
            print("unlock first")

## Transaction
    def verify_transaction(self, transaction):
        public_key_str = transaction.sender.decode("hex")
        public_key = VerifyingKey.from_string(public_key_str, curve=NIST384p)
        h = bytes(str(transaction.sender) + str(transaction.receiver) + str(transaction.amount)+str(transaction.time))
        print("*****",h)
        verify_result = public_key.verify(transaction.signature.decode("hex"),h)
        return verify_result

    def submitTransaction(self, transaction):
        if self.verify_transaction(transaction) is True:
            UnTransactionDB().insert(transaction.to_dict())
            _print(" [TX] Created new transaction")
            reactor.callFromThread(self.protocol.broadcastTx, transaction.to_dict())
        return transaction.to_dict()['hash']

    def getBalance(self, publicKey):
        return AccountDB().getAccountBalance(publicKey)
