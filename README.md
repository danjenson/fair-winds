# wifi-selector

This sets up a WiFi selector on port 8000. This requires the Linux program
NetworkManager.

## To start

- `wifi-selector`

## Run on startup

1. `sudo cp wifi-selector.service /etc/systemd/system/`
2. `sudo systemctl daemon-reload`
3. `systemctl start wifi-selector.service`
4. `systemctl enable wifi-selector.service`
