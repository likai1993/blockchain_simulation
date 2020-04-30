#! /bin/bash
sudo ifconfig tun0 192.168.53.5/24 up
sudo route add -net 192.168.52.0/24 tun0
