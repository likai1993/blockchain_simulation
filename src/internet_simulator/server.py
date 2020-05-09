#! /usr/bin/python3.6

import socket
import threading
import sys
from scapy.all import *
import ipaddress
import re

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
            print("receive packet from", conn.getpeername())
            pkt = IP(message)
            print("inside server: {} --> {}".format(pkt.src,pkt.dst))

            if len(message) == 0:
                conn.close()
                print ("Client", client_addr, "disconnected")

            if pkt.dst in clients_list.keys():
                print("send packet", "src", pkt.src, "dst", pkt.dst)
                clients_list[pkt.dst].send(message)
            time.sleep(0.1)
                        
    except (s.error, err_kbrd_intrpt):
        if client_ip in clients_list.keys():
            del clients_list[client_ip]
        conn.close()
        print ("Client", client_addr, "disconnected")
while True:
    try:
        conn, addr = ss.accept()
        client_addr = str(addr[0])
        port_bound = str(addr[1])
        client_ip = conn.recv(buffer_size)
        client_ip = client_ip[:18].decode('UTF-8')
        ip = re.findall( r'[0-9]+(?:\.[0-9]+){3}', client_ip)
        if len(ip) > 0:
            client_ip=ip[0]
            clients_list[client_ip]=conn
            print ("Connection from " + client_addr+":"+port_bound, "client configured ip:", client_ip)
            new_thread = threading.Thread(target=on_new_client_thread, args=(conn, ))
            new_thread.start()

    except KeyboardInterrupt:
        print ("Server is shutting down...")
        sys.exit(0)
    except:
        pass
