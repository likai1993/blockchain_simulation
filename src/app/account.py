#Description:
#Create account: with public key, secret key and store it in key storage
#Unlock the account: get the secret key
#Sign a transaction
#Verify the transaction

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

# encryption/decryption buffer size - 64K

class Account():

    def __init__(self, name=""):
        self.name = name
        self.publicKey = ""
        self.privateKey = ""

    def dump(self):
        return self.__dict__

    def generate_keys(self):
        private_key = RSA.generate(1024, Crypto.Random.new().read)
        public_key = private_key.publickey()

        return (binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
                binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii'))

    def create_account(self, pwd):
        bufferSize = 64 * 1024
        privateKey, publicKey = self.generate_keys()
        keys = {'publicKey': publicKey, 'privateKey':privateKey}
        path = 'Data/Keystorage/'
        fileName = path + str(self.name)+'tmp'
        with open(fileName, 'w') as json_file:
            json.dump(keys, json_file)
        #pyAesCrypt.encryptFile(fileName, path+str(self.name), pwd, bufferSize)
        filecrypto.encrypt_file(pwd, fileName, path+str(self.name))
        #print(keys)
        remove(fileName)
        # account transaction...

    def unlock_account(self, pwd):
        bufferSize = 64 * 1024
        path = 'Data/Keystorage/'
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
                return data
        except:
            print("account not exist!")

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
            signer = PKCS1_v1_5.new(RSA.importKey(
                binascii.unhexlify(self.privateKey)))
            h = SHA256.new((str(transaction.sender)+str(transaction.receiver)+str(transaction.amount)+str(transaction.time)).encode('utf8'))
            signature = signer.sign(h)
            transaction.signature = binascii.hexlify(signature).decode('ascii')
            transaction.hash = hashlib.sha256((str(transaction.sender)+str(transaction.receiver)+str(transaction.amount)+str(transaction.time)).encode('utf8')).hexdigest()
            return transaction
        else:
            print("unlock first")

## Transaction
    def verify_transaction(self, transaction):
        public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA256.new((str(transaction.sender) + str(transaction.receiver) +
                        str(transaction.amount)+str(transaction.time)).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(transaction.signature))

    def submitTransaction(self, transaction):
        if self.verify_transaction(transaction) is True:
            UnTransactionDB().insert(transaction.dump())
            print("new Transaction inserted")

    def getBalance(self, publicKey):
        return AccountDB().getAccountBalance(publicKey)
