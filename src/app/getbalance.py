
#test process
# one thread submit transactions
# one thread mining
from account import Account
import json


user1 = Account("test1")  # empty instance
#print("###create account###")
#print(json.dumps(user1.dump(), indent=2))
# user1.create_account('123')# create pubkey, prikey

#print("###unlock Account###")
user1.unlock_account('123')
#print(json.dumps(user1.dump(), indent=2))  ###relock to remove

print("UserName: test1",user1.getBalance(user1.publicKey))

user2 = Account("test2")
# user2.create_account('123')#password
user2.unlock_account('123')


print("UserName: test2",user2.getBalance(user2.publicKey))