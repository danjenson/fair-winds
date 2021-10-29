#!/usr/bin/env python3
from typing import Optional
import argparse
import glob
import os
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
import bluetooth
import dbus
import uvicorn

# parse command line arguments
parser = argparse.ArgumentParser(
    prog=sys.argv[0], formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-i', '--ignore_ssid', help='ignore this SSID')
parser.add_argument('-e',
                    '--external_iface',
                    default='wlan1',
                    help='external interface that scans for networks')
args = parser.parse_args(sys.argv[1:])

dev = nm.NetworkManager.GetDeviceByIpIface(args.external_iface)
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

# setup server for selecting wifi
app = FastAPI()
app_dir = pathlib.Path(__file__).parent.resolve()
app.mount("/static",
          StaticFiles(directory=app_dir.joinpath('static')),
          name='static')
templates = Jinja2Templates(directory=app_dir.joinpath('templates'))
aps = []


@app.get('/', response_class=HTMLResponse)
def read_root(request: Request,
              ssid: Optional[str] = None,
              bt: Optional[str] = None,
              success: bool = False):
    global aps
    try:
        aps = wifi_scan()
    except dbus.exceptions.DBusException:
        pass
    bts = bluetooth_scan()
    dvd = dvd_scan()
    return templates.TemplateResponse(
        'index.html', {
            'request': request,
            'ssid': ssid,
            'bt': bt,
            'success': success,
            'aps': aps,
            'bts': bts,
            'dvd': dvd,
        })


def wifi_scan():
    dev.RequestScan({})
    acs = [
        ac.SpecificObject.Ssid for ac in nm.NetworkManager.ActiveConnections
        if hasattr(ac.SpecificObject, 'Ssid')
    ]
    all_aps = sorted([{
        'ssid': ap.Ssid,
        'strength': ap.Strength,
        'freq': ap.Frequency,
        'secured': ap.RsnFlags > 0,
        'mac': ap.HwAddress.replace(':', '-'),
        'active': ap.Ssid in acs,
    } for ap in dev.GetAccessPoints() if ap.Ssid != args.ignore_ssid],
                     key=lambda d: d['strength'],
                     reverse=True)
    # only list the strongest ap for each SSID
    strongest_aps = []
    seen = []
    for ap in all_aps:
        if ap['ssid'] not in seen:
            strongest_aps.append(ap)
            seen.append(ap['ssid'])
    return strongest_aps


def bluetooth_scan():
    return [{
        'name': name,
        'addr': addr,
        'active': len(bluetooth.find_service(address=addr)) > 0,
    } for addr, name in bluetooth.discover_devices(lookup_names=True)]


def dvd_scan():
    dvd = None
    dvds = glob.glob('/run/media/pi/*')
    if dvds:
        dvd = os.path.basename(dvds[0])
    return dvd


@app.post('/wifi', response_class=RedirectResponse)
def wifi(ssid: str = Form(...),
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
        return RedirectResponse(f'/?success=false&ssid={ssid}',
                                status_code=303)
    return RedirectResponse(f'/?success=true&ssid={ssid}', status_code=303)


@app.post('/bt')
def bt(addr: str = Form(...), name: str = Form(...)):
    pair = f'bluetoothctl pair {addr}'
    connect = f'bluetoothctl connect {addr}'
    try:
        p_pair = subprocess.run(pair.split(),
                                stderr=subprocess.PIPE,
                                encoding='utf-8',
                                check=True)
        p_conn = subprocess.run(connect.split(),
                                stderr=subprocess.PIPE,
                                encoding='utf-8',
                                check=True)
        if p_pair.stderr or p_conn.stderr:
            return RedirectResponse(f'/?success=false&bt={name}',
                                    status_code=303)
    except Exception:
        return RedirectResponse(f'/?success=false&bt={name}', status_code=303)
    return RedirectResponse(f'/?success=true&bt={name}', status_code=303)


@app.post('/dvd', response_class=RedirectResponse)
def dvd(name: str = Form(...)):
    try:
        subprocess.run([
            'ghb', '-i', '/media/VIDEO_TS', '-o', f'/data/media/dvds/{name}',
            '-e', 'x264'
        ])
    except subprocess.CalledProcessError:
        return RedirectResponse('/?success=false')
    return RedirectResponse('/')


@app.get('/reboot', response_class=RedirectResponse)
def reboot(request: Request):
    try:
        subprocess.run(['reboot'])
    except subprocess.CalledProcessError:
        return RedirectResponse('/?success=false')
    return RedirectResponse('/')


@app.get('/poweroff', response_class=RedirectResponse)
def poweroff(request: Request):
    try:
        subprocess.run(['shutdown', '-h', 'now'])
    except subprocess.CalledProcessError:
        return RedirectResponse('/?success=false')
    return RedirectResponse('/')


if __name__ == '__main__':
    uvicorn.run('control_panel:app', timeout_keep_alive=300)
