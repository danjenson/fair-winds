# control-panel

## Setup (Raspberry Pi 4)

1. Flash [raspios](https://www.raspberrypi.com/software/operating-systems/);
   at various times, attempted ubuntu, ubuntu server, ubuntu mate, and arch arm;
   all froze or had package compatibility issues; raspios appears to be the best
   supported
2. Update and install system packages

- `sudo apt update && sudo apt upgrade`
- `sudo apt install handbrake vlc firefox-esr libdvdcss2`

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
- `cd fair-winds && ./install-locally.sh`
  - add `export PATH=~/.local/bin:$PATH` to `~/.bashrc`
- `pip3 show fair-winds | grep Location` -> `<path>`
- `sudo cp <path>/control_panel/control-panel.service /etc/systemd/system/`
- `sudo vim /etc/systemd/system/control-panel.service`
  - replace `<python-path>` with the output of `which python`
  - replace `<control-panel-path>` with the output of `which control-panel`
    - note that the outputs of `which <program>` should be the same except the
      value after the last `/`
- `systemctl enable control-panel.service` and reboot
