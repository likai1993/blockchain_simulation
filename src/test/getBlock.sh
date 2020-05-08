#! /bin/bash
number=$1
subnet=$2
curl -X POST --data '{"jsonrpc":"2.0","id":2,"method":"getBlock","params":['$number']}' "http://192.168.$subnet:8888"
