# ReadResol

Reads data from a Resol solar controller via VBus/serial and forwards the parsed values to Homematic and/or ioBroker.

Current implementation status:

- Active runtime: `readresol.py` (Python 3).
- Legacy script: `readresol` (Perl, kept for reference, not used by systemd template).
- Systemd service template: `readresol.service.template` runs `python3 /home/rainer/Projects/ReadResol/readresol.py`.
- Packet handling includes VBus frame checksum validation before values are processed.
- ioBroker updates are sent per datapoint using `/set/<id>?value=...`.

## Hardware Connectivity

To connect a Resol solar regulator to Linux, use a serial-to-USB adapter (for example PL2303-based).

## Create Stable Device Name (`/dev/RESOL`)

Create a udev rule:

```bash
cd /etc/udev/rules.d
sudo nano 50-usb.rules
```

Add this line (adjust vendor/product IDs for your adapter):

```text
SUBSYSTEM=="tty", ATTRS{idVendor}=="067b", ATTRS{idProduct}=="2303", SYMLINK+="RESOL", MODE="0666"
```

If you use a different adapter:

```bash
dmesg
lsusb
```

Then reload rules (or reboot):

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

The script expects:

```text
/dev/RESOL
```

## Ubuntu Requirements (APT)

Install Python runtime and the Python modules used by `readresol.py` from Ubuntu packages:

```bash
sudo apt update
sudo apt install -y \
	python3 \
	python3-serial \
	python3-urllib3
```

Notes:

- `python3-serial` provides the `serial` module (`pyserial`).
- `python3-urllib3` provides the `urllib3` module.
- `logging`, `binascii`, `time`, and `sys` are part of Python standard library.
- The current `requirements.txt` appears to be a full system snapshot and is not required for normal deployment of `readresol.py`.

## Configuration

Create/adjust `config.py` (use `config.example.py` as template):

- `HOMEMATICPATH`
- `HMISEIDS`
- `IOBROKERPATH`
- `IOBROKERDIR`

Choose targets in `readresol.py` via `LOGTARGET` (`homematic`, `iobroker`, or both).

## Run as Systemd Service

Copy service template:

```bash
sudo cp readresol.service.template /lib/systemd/system/readresol.service
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable readresol.service
sudo systemctl start readresol.service
```

Check status:

```bash
sudo systemctl status readresol.service
```

## Logs

Default log file:

```text
/var/log/readresol.log
```
