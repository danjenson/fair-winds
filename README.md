# control-panel

# TODO:

1. Install/enable plex server
2. Install handbrake and add command to server: `HandBrakeCLI -i VIDEO_TS -o movie.mp4 -e x264`
3. Add tab for ripping dvds

This sets up a WiFi selector on port 8000. This requires `NetworkManager`,
`iptables`, and
[linux-wifi-selector](https://github.com/lakinduakash/linux-wifi-hotspot).

## Setup

1. Find the location of the systemd service file:

- `pip show fair-winds | grep Location`

2. Using the above path,

- `sudo cp <path>/control_panel/control-panel.service /etc/systemd/system/`
- `sudo vim /etc/systemd/system/control-panel.service`
  - replace `<python-path>` with the output of `which python`
  - replace `<wifi-selector-path>` with the output of `which wifi-selector`
    - note that the outputs of `which <program>` should be the same except the
      value after the last `/`
  - replace `<name>` with the name you want to call the local network
  - replace `<password>` with the login password you want to use

3. `systemctl enable control-panel.service` and reboot

## Raspberry Pi 4 Ubuntu Server Setup

1. [Download image](https://ubuntu.com/download/raspberry-pi)
2. Flash to disk, reload disk
3. Enable ssh and wifi-selector

- `cd <mount>/system-boot`
- `touch ssh`
- `vim network-config` and edit to add SSID and passphrase

4. Install python and `pip install fair-winds`
5. Run setup for wifi-selector above
