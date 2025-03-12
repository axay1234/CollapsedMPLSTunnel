# Encrypted Password Generator & MPLS Collapsed Tunnel Detector
Requirements
This project requires Python 3.6 or above.
## Overview
This repository contains two Python scripts:
1. **Encrypted Password Generator** - Encrypts a password using Base64 encoding and updates a configuration file.
2. **MPLS Collapsed Tunnel Detector** - Detects MPLS tunnels with identical working and protect paths.

## Features
### Encrypted Password Generator
- Prompts the user to enter a password.
- Encrypts the password using Base64 encoding.
- Provides an option to update the encrypted password in `config.properties`.

### MPLS Collapsed Tunnel Detector
- Reads device and authentication information from `config.properties`.
- Uses an API to retrieve device and tunnel data from an EPNM server.
- Identifies collapsed tunnels where working and protect paths are identical.
- Sends an email alert with instructions for resolving collapsed tunnels.
- Logs execution details and automatically deletes old logs.

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/axay1234/CollapsedMPLSTunnel.git
   cd CollapsedMPLSTunnel
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Configuration
Modify the `config.properties` file to include the necessary credentials and server details:
```ini
[epnm]
ipAddr = <EPNM Server IP>
EPNM_UserName = <Username>
EPNM_PWD = <Encrypted Password>
getDevices = <API Endpoint for Devices>

[template]
upload = <Upload API>
deploy = <Deploy API>
delete = <Delete API>

[mail]
toAddr = <Recipient Email>

[logs]
log_delete_days = 7
```

## Usage
### Encrypting a Password
Run the password encryption script:
```sh
python encrypt.py
```
Follow the prompts to generate and optionally save an encrypted password.

### Detecting Collapsed Tunnels
Run the tunnel detection script:
```sh
python IdentifyCollapsedTunnels.py
```
This will:
- Retrieve device and tunnel information from EPNM.
- Identify tunnels with identical working and protect paths.
- Send an email alert if collapsed tunnels are found.

## Logging
- Logs are stored in the `logs/` directory.
- Old logs are automatically deleted based on the `log_delete_days` setting in `config.properties`.

## Contributing
Feel free to submit issues or pull requests to improve the scripts.
