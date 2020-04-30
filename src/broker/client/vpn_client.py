#!/usr/bin/python3
import fcntl
import struct
import os
from scapy.all import *
TUNSETIFF = 0X400454ca
IFF_TUN   = 0x0001
IFF_TAP   = 0x0002
IFF_NO_PI = 0x1000
SERVER_IP = "128.230.208.73"
SERVER_PROT = int(sys.argv[1])
tun = os.open("/dev/net/tun", os.O_RDWR)
ifr = struct.pack('16sH',b'tun%d', IFF_TUN | IFF_NO_PI)
ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)
ifname = ifname_bytes.decode('UTF-8')[:16].strip("\x00")
print("Interface Name: {}".format(ifname))
os.system("ip addr add 192.168.53.6/24 dev {}".format(ifname))
os.system("ip link set dev {} up".format(ifname))
os.system("ip route add 192.168.53.0/24 dev {}".format(ifname))
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP,SERVER_PROT))
sock.send(b'192.168.53.5')
fds = [sock, tun]
while True:
    #setup routing table
    #sudo ip route add origninal dst to tun0; iproute
    ready,_,_ = select(fds, [], [])
    for fd in ready:
        if fd is sock:
            print("sock...")
            data = sock.recv(2048)
            pkt = IP(data)
            print("inside server: {} --> {}".format(pkt.src,pkt.dst))
            os.write(tun,data)
        if fd is tun:
            packet = os.read(tun, 2048)
            pkt = IP(packet)
            print("From tun ==>: {} --> {}".format(pkt.src, pkt.dst))
            sock.send(packet)
