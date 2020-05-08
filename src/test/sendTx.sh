#! /bin/bash
name=$1
psw=$2
receiver=$3
amount=$4
subnet=$5

curl -X POST --data '{"jsonrpc":"2.0","id":2,"method":"unlock","params":['\"$name\"','\"$psw\"']}' "http://192.168.$subnet:8888"
echo -e "\n"
curl -X POST --data '{"jsonrpc":"2.0","id":2,"method":"sendTransaction","params":['\"$receiver\"','\"$amount\"']}' "http://192.168.$subnet:8888"
