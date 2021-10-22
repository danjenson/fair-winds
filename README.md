# wifi-selector

This sets up a WiFi selector on port 8000. This requires `NetworkManager`,
`iptables`, and
[linux-wifi-selector](https://github.com/lakinduakash/linux-wifi-hotspot).

[translate iptables to nftables](https://wiki.nftables.org/wiki-nftables/index.php/Moving_from_iptables_to_nftables)
[nftables port fowarding](https://jensd.be/1086/linux/forward-a-tcp-port-to-another-ip-or-port-using-nat-with-nftables)

## Running

- create the file `/etc/wifi-selector.conf`, and add the following entries,
  changing the interface after the `=`; you can list network device interfaces
  with with `nmcli device`; you can use the same interface for internal and
  external connections, although it's more common to have an external antenna
  that plugs in via a USB port for greater range, as here:
  - `NAME=Fair Winds`
  - `INTERNAL_WIFI_INTERFACE=wlp82s0`
  - `EXTERNAL_WIFI_INTERFACE=wlp0s20f0u1`
- run the program: `wifi-selector`

## Automatically run on startup

1. Find the location of the systemd service file:

- `pip show fair-winds | grep Location`

2. Using the above path,

- `sudo cp <path>/wifi_selector/wifi-selector.service /etc/systemd/system/`
- `sudo vim /etc/systemd/system/wifi-selector.service`
  - replace `<python-path>` with the output of `which python`
  - replace `<wifi-selector-path>` with the output of `which wifi-selector`
  - note that the outputs of `which <program>` should be the same except the
    value after the last `/`

3. `systemctl enable wifi-selector.service` and reboot
