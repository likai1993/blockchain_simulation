#! /usr/bin/python3.6

import socket
import threading
import sys
from scapy.all import *

backlog = 10000
buffer_size = 2048
s = socket
IPv4 = s.AF_INET
TCP = s.SOCK_STREAM
ss = s.socket(IPv4, TCP)

HOST = "0.0.0.0"
PORT = int(sys.argv[1])

ss.bind((HOST, PORT))
ss.listen(backlog)

# maintain all connections from local ip address
clients_list = {} 

err_kbrd_intrpt = KeyboardInterrupt

def on_new_client_thread(conn):
    global s
    global clients_list
    global err_kbrd_intrpt

    try:
        while 1:    
            message = conn.recv(buffer_size)
            print("receive packet", message, "from", conn.getpeername())
            pkt = IP(message)
            print("inside server: {} --> {}".format(pkt.src,pkt.dst))

            if len(message) == 0:
                conn.close()
                print ("Client", client_addr, "disconnected")

            if pkt.dst in clients_list.keys():
                print("send packet", "src", pkt.src, "dst", pkt.dst, "msg:", message)
                clients_list[pkt.dst].send(message)
                        
    except (s.error, err_kbrd_intrpt):
        conn.close()
        del clients_list[client_ip]
        print ("Client", client_addr, "disconnected")
try:
    while True:
        conn, addr = ss.accept()
        client_addr = str(addr[0])
        port_bound = str(addr[1])
        client_ip = conn.recv(buffer_size)
        client_ip = client_ip.decode() 
        print(client_ip)
        clients_list[client_ip]=conn
        print ("Connection from " + client_addr+":"+port_bound, "client configured ip:", client_ip)
        new_thread = threading.Thread(target=on_new_client_thread, args=(conn, ))
        new_thread.start()

except KeyboardInterrupt:
    print ("Server is shutting down...")
    sys.exit(0)
