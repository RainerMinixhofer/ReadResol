# Code for reading the Resol Solar Regulator
## Hardware connectivity
To connect the Resol Solar Regulator to a Linux box, one needs to convert the Serial Bus Protocol to an USB Protocol using an [Serial to USB Converter](https://www.amazon.de/Prolific-PL2303-Adapterkabel-ESP8266-Arduino/dp/B07N8Z22SR).
## Hardware interface
To generate a unique device id for the USB port of the Serial to USB converter we have to define it's vendor and product id in the definition files for the udev daemon:

> cd /etc/udev/rules.d
>
> sudo nano 50-usb.rules

enter the following line into the editor

> SUBSYSTEM=="tty", ATTRS{idVendor}=="067b", ATTRS{idProduct}=="2303", SYMLINK+="RESOL", MODE="0666"

where the vendor id and the product id are the ones of the above mentioned converter. If you use a different product you'll need to inspect the output of

> dmesg

to identify which USB port the converter has been connected to and then

> lsusb

to get the vendor and product id of the respective device at this port.
After reboot the new symlink

> /dev/RESOL

has been created which is the default port the script is accessing.

Alternatively to a reboot one can issue

> sudo udevadm control --reload-rules && sudo udevadm trigger

## Daemonizing script

Since the code has been transferred from Perl to Python, the architecture has been moved to the much simpler and newer systemd implementation as well.
Please refer to e.g. the article [Setup a python script as a service through systemctl/systemd](https://medium.com/codex/setup-a-python-script-as-a-service-through-systemctl-systemd-f0cc55a42267) for further details how to do this.
