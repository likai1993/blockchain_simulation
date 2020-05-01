from account_bak import Account
import json

user1 = Account("test1")# empty instance
print("###create account###")
print(json.dumps(user1.to_dict(), indent=2))
user1.create_account('test1','123')# create pubkey, prikey
print("***",user1.privateKey,user1.publicKey)



print("###unlock Account###")
user1.unlock('test1','123')
print(json.dumps(user1.to_dict(), indent=2))###relock to remove

user2 = Account("test2")
user2.create_account('test2','123')#password
user2.unlock('test2','123')


print("###create Transaction###")
transaction = user1.createTransaction(user2.publicKey,10)
print(json.dumps(transaction.to_dict(), indent=2))
print("###sign Transaction###")
print(json.dumps(user1.sign_transaction(transaction).to_dict(), indent=2))

print("###verify Transaction###")
print(user2.verify_transaction(transaction))

