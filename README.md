# control-panel

## Setup (Raspberry Pi 4)

1. Flash [raspios](https://www.raspberrypi.com/software/operating-systems/);
   at various times, attempted ubuntu, ubuntu server, ubuntu mate, and arch arm;
   all froze or had package compatibility issues; raspios appears to be the best
   supported
2. Update and install system packages

- `sudo apt update && sudo apt upgrade`
- `sudo apt install handbrake handbrake-cli vlc libdvdcss2`
- `sudo hostnamectl set-hostname <name>`

3. [Setup as access point](https://www.raspberrypi.com/documentation/computers/configuration.html#setting-up-a-routed-wireless-access-point)

- if you get a persistent error in the Network Panel of the task bar that
  says, 'Set WiFi Country', you need to create two files in
  `/etc/wpa_supplicant/` called `wpa_supplicant-wlan0.conf` and
  `wpa_supplicant-wlan1.conf` each with contents like:

  ```
  ctrl_interface=DIR=/var/run/wpa_supplicant
  GROUP=netdev
  update_config=1
  country=US

  network={
          ssid="<SSID>"
          psk="<password>"
  }
  ```

- setting up `wlan0` as a local AP will also cause the network panel to show
  `No wireless interfaces found` (as of 2020-10-29); it will still work with
  `nmcli` though

4. Setup `fair-winds` repo

- `mkdir ~/.ssh && ssh-keygen && cat id_rsa.pub`
- copy and paste to github
- `git clone git@github.com:danjenson/fair-winds.git`
- `python3 -m venv ~/.venv/v && source ~/.venv/v/bin/activate`
- `cd fair-winds && ./install-locally.sh`
- add to end of `~/.bashrc`
  - `source ~/.venv/v/bin/activate`
  - `export PATH=~/.local/bin:$PATH`
- `pip3 show fair-winds | grep Location` -> `<path>`
- `sudo cp <path>/control_panel/control-panel.service /etc/systemd/system/`
- `sudo vim /etc/systemd/system/control-panel.service`
  - replace `<python-path>` with the output of `which python`
  - replace `<control-panel-path>` with the output of `which control-panel`
    - note that the outputs of `which <program>` should be the same except the
      value after the last `/`
- `systemctl enable control-panel.service`

5. [Optional] open browser/control-panel

- set browser home to `localhost:8000`
- `vim ~/.config/lxsession/LDXE-pi/autostart`

```
@lxpanel --profile LXDE-pi
@pcmanfm --desktop --profile LXDE-pi
#@xscreensaver -no-splash
point-rpi
@chromium-browser
```

### Debugging

- useful script to have on pi in `~/update-fair-winds.sh`:
  ```
  cd fair-winds \
  && git pull --rebase \
  && ./install-locally.sh \
  && sudo systemctl restart control-panel \
  && systemctl status control-panel
  ```
- if bluetooth is acting up
  - `systemctl status bluetooth`
    - if there are SAP errors
      - `vim /etc/systemd/system/bluetooth.target.wants/bluetooth.service`
        - `..../bluetoothd --noplugin=sap`
    - new bthelper (2020-05-12)
      - `wget https://raw.githubusercontent.com/RPi-Distro/pi-bluetooth/master/usr/bin/bthelper`
      - `chmod +755 bthelper && sudo cp bthelper /usr/bin`
- if dvd playing is acting up:
  - `sudo dpkg-reconfigure libdvd-pkg`


### Extra

- remap caps lock to control
  - `sudo vim /etc/default/keyboard`
    - `XKBOPTIONS="ctrl:nocaps"`
  - `sudo dpkg-reconfigure keyboard-configuration`
