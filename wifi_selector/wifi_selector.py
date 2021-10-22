#!/usr/bin/env python3
from typing import Optional
import os
import pathlib
import subprocess

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)
import NetworkManager as nm

# setup network
# allows external traffic to be routed to local loopback
subprocess.run(['sysctl', 'net.ipv4.conf.all.route_localnet=1'], check=True)
# routes traffic from port 80 to localhost:8000 (wifi selector server)
subprocess.run([
    'iptables',
    '-t',
    'nat',
    '-A',
    'PREROUTING',
    '-p',
    'tcp',
    '--dport',
    '80',
    '-j',
    'DNAT',
    '--to-destination',
    '127.0.0.1:8000',
],
               check=True)

# setup wifi selector
# TODO use longest inteface name under assumption it is external
ifaces = [
    dev.Interface for dev in nm.NetworkManager.GetDevices()
    if dev.DeviceType == 2  # Wireless
]
iface = ifaces[0]
if cfg['EXTERNAL_WIFI_INTERFACE'] in ifaces:
    iface = cfg['EXTERNAL_WIFI_INTERFACE']
dev = nm.NetworkManager.GetDeviceByIpIface(iface)
app = FastAPI()
app_dir = pathlib.Path(__file__).parent.resolve()
app.mount("/static",
          StaticFiles(directory=app_dir.joinpath('static')),
          name='static')
templates = Jinja2Templates(directory=app_dir.joinpath('templates'))


@app.get('/', response_class=HTMLResponse)
def read_root(request: Request,
              ssid: Optional[str] = None,
              success: bool = False):
    dev.RequestScan({})
    acs = [
        ac.SpecificObject.HwAddress
        for ac in nm.NetworkManager.ActiveConnections
    ]
    aps = sorted([{
        'ssid': ap.Ssid,
        'strength': ap.Strength,
        'freq': ap.Frequency,
        'secured': ap.RsnFlags > 0,
        'mac': ap.HwAddress.replace(':', '-'),
        'active': ap.HwAddress in acs,
    } for ap in dev.GetAccessPoints()],
                 key=lambda d: d['strength'],
                 reverse=True)
    return templates.TemplateResponse(
        'index.html',
        {
            'request': request,
            'name': os.uname().nodename,  # hostname
            'ssid': ssid,
            'success': success,
            'aps': aps,
        })


@app.post('/connect', response_class=RedirectResponse)
def connect(ssid: str = Form(...),
            mac: str = Form(...),
            password: Optional[str] = Form(None)):
    # subprocess in python protects against shell injection
    # https://docs.python.org/3/library/subprocess.html#security-considerations
    cmd = f'nmcli device wifi connect {mac} ifname {iface}'
    if password:
        cmd += f' password {password}'
    try:
        subprocess.run(cmd.split(), check=True)
    except subprocess.CalledProcessError:
        return RedirectResponse(f'/?ssid={ssid}&success=false',
                                status_code=303)
    return RedirectResponse(f'/?ssid={ssid}&success=true', status_code=303)
