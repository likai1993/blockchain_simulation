#! /bin/bash
pubkey=$1
subnet=$2
curl -X POST --data '{"jsonrpc":"2.0","id":2,"method":"getBalance","params":['\"$pubkey\"']}' "http://192.168.$subnet:8888"
