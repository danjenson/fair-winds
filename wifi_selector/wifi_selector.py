#!/usr/bin/env python3
from typing import Optional
import os
import subprocess
import pathlib

from dotenv import dotenv_values
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)
import NetworkManager as nm

cfg = dotenv_values(os.path.expanduser('~/.network'))
iface = cfg['EXTERNAL_WIFI_INTERFACE']
dev = nm.NetworkManager.GetDeviceByIpIface(iface)
app = FastAPI()
static_dir = pathlib.Path(__file__).parent.resolve().joinpath('static')
app.mount("/static", StaticFiles(directory=static_dir), name='static')
templates = Jinja2Templates(directory='templates')


@app.get('/', response_class=HTMLResponse)
def read_root(request: Request,
              ssid: Optional[str] = None,
              success: bool = False):
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
    return templates.TemplateResponse('index.html', {
        'request': request,
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
