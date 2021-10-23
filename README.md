# control-panel

-- TODO:

- Add UI for ripping dvds
  - install and set up plex
  - install handbrake, libdvdcss, vlc on arch
  - get it working so you can show ripping progress in web UI
- setup rpi4

## Raspberry Pi 4 Ubuntu Server Setup

This requires `NetworkManager`,
`iptables`, and
[linux-wifi-selector](https://github.com/lakinduakash/linux-wifi-hotspot).

1. Clear disk, / partition 25 GB, rest on /data
2. [Download image](https://ubuntu.com/download/raspberry-pi)
3. Flash image to /, reload
4. Enable wifi and ssh

- `cd <mount>/system-boot`
- `touch ssh`
- `vim network-config` and edit to add SSID and passphrase

4. Boot and update system, `sudo apt-get update`
5. Install python and `pip install fair-winds`
6. Install handbrake, libdvdcss, and vlc
7. Setup automounting of disks, i.e. dvds
8. Install and set up plex server
9. Set up Control Panel below

## Setup Control Panel

1. Find the location of the systemd service file:

- `pip show fair-winds | grep Location`

2. Using the above path,

- `sudo cp <path>/control_panel/control-panel.service /etc/systemd/system/`
- `sudo vim /etc/systemd/system/control-panel.service`
  - replace `<python-path>` with the output of `which python`
  - replace `<control-panel-path>` with the output of `which control-panel`
    - note that the outputs of `which <program>` should be the same except the
      value after the last `/`
  - replace `<name>` with the name you want to call the local network
  - replace `<password>` with the login password you want to use

3. `systemctl enable control-panel.service` and reboot
