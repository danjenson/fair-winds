# wifi-selector

This sets up a WiFi selector on port 8000.

# Requirements

- Linux:
  - NetworkManager
- Python:
  - `pip install requirements.txt`

# Install daemon

1. `sudo cp wifi-selector.service /etc/systemd/system/`
2. `sudo systemctl daemon-reload`
3. `systemctl start wifi-selector.service`
4. `systemctl enable wifi-selector.service`
