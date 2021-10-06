#!/usr/bin/env python3
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)
import NetworkManager as nm

iface = 'wlp82s0'  # change this accordingly
dev = nm.NetworkManager.GetDeviceByIpIface(iface)
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get('/', response_class=HTMLResponse)
def read_root(request: Request):
    aps = sorted([{
        'ssid': ap.Ssid,
        'strength': ap.Strength,
        'secured': ap.WpaFlags > 0,
        'mac': ap.HwAddress.replace(':', '-'),
    } for ap in dev.GetAccessPoints()],
                 key=lambda d: d['strength'],
                 reverse=True)
    return templates.TemplateResponse('index.html', {
        'request': request,
        'aps': aps,
    })


@app.post('/connect')
def connect(mac: str = Form(...), password: str = Form(...)):
    # TODO
    return {'mac': mac, 'password': password}
