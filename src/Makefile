setup:
	sudo python2.7 -m pip install twisted
	sudo python2.7 -m pip install scapy
	sudo python2.7 -m pip install python-jsonrpc
	sudo python2.7 -m pip install ecdsa
clean:
	rm -rf ./Data/
	find ./ -name '*.pyc' |xargs rm -rf
	mkdir -p ./Data/Keystore
	touch ./Data/Keystore/testAccount
