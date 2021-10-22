# wifi-selector

This sets up a WiFi selector on port 8000. This requires `NetworkManager`,
`iptables`, and
[linux-wifi-selector](https://github.com/lakinduakash/linux-wifi-hotspot).

## Setup

1. Find the location of the systemd service file:

- `pip show fair-winds | grep Location`

2. Using the above path,

- `sudo cp <path>/wifi_selector/wifi-selector.service /etc/systemd/system/`
- `sudo vim /etc/systemd/system/wifi-selector.service`
  - replace `<python-path>` with the output of `which python`
  - replace `<wifi-selector-path>` with the output of `which wifi-selector`
    - note that the outputs of `which <program>` should be the same except the
      value after the last `/`
  - replace `<name>` with the name you want to call the local network
  - replace `<password>` with the login password you want to use

3. `systemctl enable wifi-selector.service` and reboot
