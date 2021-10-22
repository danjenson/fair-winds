#!/usr/bin/env python3
from typing import Optional
import argparse
import pathlib
import subprocess
import sys

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)
import NetworkManager as nm
import uvicorn

# longer wireless device names usually indicate external devices, i.e.
# an internal device might be called wlp82s0, while an external device
# might be called wlp0s20f0u1; the defaults assume that the longer name
# i.e. the external device should be used for scanning and picking up
# external networks, under the assumption that it is likely more powerful
# than the internal, built-in wifi device, and the built-in device will
# be used for creating a local network
n_dev = sorted([(len(dev.Interface), dev)
                for dev in nm.NetworkManager.GetDevices()
                if dev.Interface.startswith('wl')],
               reverse=True)
dev = n_dev[0][1]
internal_iface, external_iface = dev.Interface, dev.Interface
# if more than 1, use the 2nd (likely built-in) for the internal network
if len(n_dev) > 1:
    internal_iface = n_dev[1][1].Interface

# parse command line arguments
parser = argparse.ArgumentParser(
    prog=sys.argv[0], formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('name', help='name (SSID) of local network')
parser.add_argument('password', help='password for local network')
parser.add_argument('-i',
                    '--internal_iface',
                    default=internal_iface,
                    help='internal interface')
parser.add_argument('-e',
                    '--external_iface',
                    default=external_iface,
                    help='external interface')
args = parser.parse_args(sys.argv[1:])

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
# create local network
subprocess.Popen([
    '/usr/bin/create_ap',
    '--ieee80211n',
    '--ht_capab',
    '[HT40+]',
    '--freq-band',
    '2.4',  # TODO: update when 5ghz becomes default
    '-g',
    '192.168.12.1',
    args.internal_iface,
    args.external_iface,
    args.name,
    args.password,
])

# setup server for selecting wifi
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
        'index.html', {
            'request': request,
            'name': args.name,
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
    cmd = f'nmcli device wifi connect {mac} ifname {args.external_iface}'
    if password:
        cmd += f' password {password}'
    # nmcli always returns exit code 0, so must check stderr
    if subprocess.run(cmd.split(), stderr=subprocess.PIPE,
                      encoding='utf-8').stderr:
        return RedirectResponse(f'/?ssid={ssid}&success=false',
                                status_code=303)
    return RedirectResponse(f'/?ssid={ssid}&success=true', status_code=303)

@app.post('/refresh', response_class=RedirectResponse)
def refresh():
    try:
        subprocess.run(['systemctl', 'restart', 'control-panel'])
    except subprocess.CalledProcessError:
        return RedirectResponse('/?success=false')
    return RedirectResponse('/')


@app.post('/reboot', response_class=RedirectResponse)
def reboot():
    try:
        subprocess.run(['reboot'])
    except subprocess.CalledProcessError:
        return RedirectResponse('/?success=false')
    return RedirectResponse('/')


if __name__ == '__main__':
    uvicorn.run('control_panel:app', timeout_keep_alive=300)
