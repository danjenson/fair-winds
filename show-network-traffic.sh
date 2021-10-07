#!/bin/sh
tshark -f "host 127.0.0.1 and port 8000" -i lo
