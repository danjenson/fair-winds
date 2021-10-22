#!/bin/sh
sudo sysctl net.ipv4.conf.all.route_localnet=1
sudo iptables -t nat -A PREROUTING -p tcp --dport 8000 -j DNAT --to-destination 127.0.0.1:8000
