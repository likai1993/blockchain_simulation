#! /bin/bash
subnet=$1
curl -X POST --data '{"jsonrpc":"2.0","id":2,"method":"stopMining","params":[]}' "http://192.168.$subnet:8888"
