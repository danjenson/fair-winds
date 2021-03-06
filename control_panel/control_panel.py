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
              bt_name: Optional[str] = None,
              success: bool = False):
    global aps
    # ap scan is async, so ask before sync bt_scan
    try:
        dev.RequestScan({})
    except dbus.exceptions.DBusException:
        pass
    bts = bt_scan()
    aps = wifi_scan()
    dvd = dvd_scan()
    # html does not like ':' in identifiers
    for ap in aps:
        ap['mac'] = ap['mac'].replace(':', '-')
    for bt in bts:
        bt['addr'] = bt['addr'].replace(':', '-')
    return templates.TemplateResponse(
        'index.html', {
            'request': request,
            'ssid': ssid,
            'bt_name': bt_name,
            'success': success,
            'aps': aps,
            'bts': bts,
            'dvd': dvd,
        })


def wifi_scan():
    all_aps = sorted([{
        'ssid': ap.Ssid,
        'strength': ap.Strength,
        'freq': ap.Frequency,
        'secured': ap.RsnFlags > 0,
        'mac': ap.HwAddress,
        'active': is_active(ap),
    } for ap in dev.GetAccessPoints() if is_valid(ap)],
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


def is_active(ap):
    return hasattr(ap, 'Ssid') and hasattr(
        dev.ActiveAccessPoint,
        'Ssid') and ap.Ssid == dev.ActiveAccessPoint.Ssid


def is_valid(ap):
    return hasattr(ap, 'Ssid') and ap.Ssid != args.ignore_ssid


def bt_scan(timeout=10):
    try:
        subprocess.run(['bluetoothctl', 'scan', 'on'], timeout=timeout)
    except subprocess.TimeoutExpired:
        pass
    items = subprocess.check_output(['bluetoothctl',
                                     'devices']).decode('utf-8').split('\n')
    bts = []
    for item in items:
        if item:
            _, addr, name = item.split(' ', 2)
            bts.append({'addr': addr.strip(), 'name': name.strip()})
    return bts


def dvd_scan():
    dvd = None
    dvds = glob.glob('/media/pi/*')
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
    try:
        if not bt_paired(addr):
            bt_pair(addr)
        if not bt_connected(addr):
            bt_connect(addr)
        bt_audio(addr)
    except Exception:
        return RedirectResponse(f'/?success=false&bt_name={name}',
                                status_code=303)
    return RedirectResponse(f'/?success=true&bt_name={name}', status_code=303)


def bt_paired(addr):
    items = subprocess.check_output(['bluetoothctl', 'paired-devices'
                                     ]).decode('utf-8').split('\n')
    for item in items:
        if addr in item:
            return True
    return False


def bt_pair(addr):
    subprocess.run(['bluetoothctl', 'pair', addr])


def bt_connected(addr):
    cmd = f'bluetoothctl info "{addr}" | grep -q "Connected: yes"'
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        return False
    return True


def bt_connect(addr):
    subprocess.run(['bluetoothctl', 'connect', addr])


def bt_audio(addr):
    for name, idx in audio_sinks().items():
        if addr.replace(':', '_') in name:
            # NOTE: pactl must be run in userspace
            subprocess.run(['pactl', 'set-default-sink', idx],
                           preexec_fn=set_user)


def audio_sinks():
    # NOTE: pactl must be run in userspace
    audio_items = subprocess.check_output(
        ['pactl', 'list', 'short', 'sinks'],
        preexec_fn=set_user).decode('utf-8').split('\n')
    audio_sinks = {}
    for item in audio_items:
        if item:
            idx, name, _ = item.split('\t', 2)
            audio_sinks[name] = idx
    return audio_sinks


def set_user():
    os.setgid(1000)
    os.setuid(1000)
    os.environ['XDG_RUNTIME_DIR'] = '/run/user/1000'


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
