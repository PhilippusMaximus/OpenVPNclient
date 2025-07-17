# OpenVPNClient

![License: GPL v2](https://img.shields.io/badge/License-GPL_v2-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-green.svg)

_OpenVPNClient is a graphical user interface for managing VPN sessions on Linux. Designed to make OpenVPN3 accessible and user-friendly, it lets you import `.ovpn` files, connect securely, and monitor your VPN traffic live – all in a clean and intuitive interface._

## Features

- Import `.ovpn` configuration files from your VPN provider
- Secure authentication with user credentials
- Live traffic statistics and connection status
- Simple connect/disconnect controls
- Cross-distro compatibility on Linux

## Requirements

- A Linux system with [openvpn3](https://github.com/OpenVPN/openvpn3-linux) installed
- Python 3.x
- VPN `.ovpn` profile from your provider

##  Installation

```bash
git clone https://github.com/PhilippusMaximus/OpenVPNClient.git
cd OpenVPNClient
python3 main.py
