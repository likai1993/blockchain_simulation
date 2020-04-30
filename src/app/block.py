# coding:utf-8
import hashlib
import time
from model import Model


class Block(Model):

    def __init__(self, index, timestamp, tx, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.tx = tx
        self.previous_block = previous_hash
        self.miner = ""


    def header_hash(self):
        """
        Refer to bitcoin block header hash
        """
        return hashlib.sha256((str(self.index) + str(self.timestamp) + str(self.tx) + str(self.previous_block)).encode(
            'utf-8')).hexdigest()

    def pow(self):
        ## not flexible
        nouce = 0
        while self.valid(nouce) is False:
            nouce += 1
        self.nouce = nouce
        return nouce


    def make(self, nouce):

        self.hash = self.ghash(nouce)

    def ghash(self, nouce):

        header_hash = self.header_hash()
        token = ''.join((header_hash, str(nouce))).encode('utf-8')
        return hashlib.sha256(token).hexdigest()

    def valid(self, nouce):
        return self.ghash(nouce)[:4] == "0000"

    def to_dict(self):
        return self.__dict__



