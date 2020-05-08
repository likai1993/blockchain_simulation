#! /bin/bash
name=$1
psw=$2
subnet=$3
curl -X POST --data '{"jsonrpc":"2.0","id":2,"method":"mining","params":['\"$name\"', '\"$psw\"']}' "http://192.168.$subnet:8888"
