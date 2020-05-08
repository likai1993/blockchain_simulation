#! /bin/bash
txhash=$1
subnet=$2

curl -X POST --data '{"jsonrpc":"2.0","id":2,"method":"getTransaction","params":['\"$txhash\"']}' "http://192.168.$subnet:8888"
