import time

class Transaction():
        def __init__(self,sender='', receiver='', amount=''):
            self.sender = sender
            self.receiver = receiver
            self.amount = amount
            self.time = time.time()
            self.signature = ""
            self.hash = ""

        def to_dict(self):
            return self.__dict__

#def getTransaction(hash_v):
