#! /usr/bin/python3
import fcntl
import struct
import os
from scapy.all import *
from log import _print

class setUpVPNClient(object):
    def __init__(self, ip, s_ip, s_port):
        TUNSETIFF = 0X400454ca
        IFF_TUN   = 0x0001
        IFF_TAP   = 0x0002
        IFF_NO_PI = 0x1000
        SERVER_IP = s_ip          #"128.230.208.73"
        SERVER_PROT = int(s_port) #int(sys.argv[1])
        tun = os.open("/dev/net/tun", os.O_RDWR)
        ifr = struct.pack('16sH',b'tun%d', IFF_TUN | IFF_NO_PI)
        ifname_bytes = fcntl.ioctl(tun, TUNSETIFF, ifr)
        ifname = ifname_bytes.decode('UTF-8')[:16].strip("\x00")
        _print(" [VPN] Interface Name: {}".format(ifname))
        command = "ip addr add "+ip+"/24 dev {}"
        os.system(command.format(ifname))
        os.system("ip link set dev {} up".format(ifname))
        network_buf = ip.split(".")
        network_id = network_buf[0]+"."+network_buf[1] 
        os.system("ip route add "+network_id+".0.0/16 dev {}".format(ifname))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP,SERVER_PROT))
        sock.send(ip.encode('UTF-8'))
        fds = [sock, tun]
        while True:
            #setup routing table
            #sudo ip route add origninal dst to tun0; iproute
            ready,_,_ = select(fds, [], [])
            for fd in ready:
                if fd is sock:
                    data = sock.recv(4096)
                    pkt = IP(data)
                    #_print(" [VPN] server: {} --> {}".format(pkt.src,pkt.dst))
                    if len(data) > 0:
                        #_print(" [VPN] to tun", len(data))
                        try:
                            os.write(tun, data)
                        except:
                            pass
                if fd is tun:
                    packet = os.read(tun, 4096)
                    if len(packet) > 0:
                        try:
                            pkt = IP(packet)
                            #_print(" [VPN] tun ==>: {} --> {}".format(pkt.src, pkt.dst))
                            sock.send(packet)
                        except:
                            pass
