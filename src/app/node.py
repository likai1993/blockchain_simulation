from database import NodeDB, TransactionDB, BlockChainDB

def start_node():
    init_node()

def init_node():
    # Get the blockchain data

    # Get the transaction data
    bcdb = BlockChainDB()
    txdb = TransactionDB()
    blockchain = bcdb.find_all()
    transactions = txdb.find_all()
    # If there is a blochain downloaded longer than local database then relace local's.
    for bc in all_node_blockchains:
        if len(bc) > len(blockchain):
            bcdb.clear()
            bcdb.write(bc)
    for txs in all_node_txs:
        if len(txs) > len(transactions):
            txdb.clear()
            txdb.write(txs)

def get_nodes():
    return NodeDB().find_all()


def add_node(address):
    ndb = NodeDB()
    all_nodes = ndb.find_all()
    if address.find('http') != 0:
        address = 'http://' + address
    all_nodes.append(address)
    ndb.clear()
    ndb.write(rm_dup(all_nodes))
    return address

def check_node(address):
    pass

def rm_dup(nodes):
    return sorted(set(nodes))

if __name__ == '__main__':
    start_node(3009)
