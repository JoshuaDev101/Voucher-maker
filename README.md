# Gravoso Voucher Maker

A lightweight local web app for Orange Pi / Armbian / Debian / Ubuntu.

## Features

- Open from any PC or phone on the same LAN using the Orange Pi IP
- Paste voucher codes or upload a `.txt` file
- One voucher code per line
- Configurable brand, duration and price
- 58mm and 80mm thermal paper modes
- Browser preview
- Direct printing through CUPS
- Optional admin password
- Auto-start on boot with systemd
- GitHub-ready backup/restore

## 1. Upload this project to GitHub

Create an empty repository, then from your PC:

```bash
git init
git add .
git commit -m "Initial voucher maker"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

## 2. Install on Orange Pi

Clone your repo:

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO
chmod +x install.sh run.sh uninstall.sh
./install.sh
```

The installer installs:

- Python 3
- Flask environment
- CUPS
- systemd service

After install, find the Orange Pi IP:

```bash
hostname -I
```

Example:

```text
192.168.1.50
```

Open from your PC or phone:

```text
http://192.168.1.50:5000
```

## 3. Add the mini thermal printer

Connect the USB thermal printer to the Orange Pi.

Check detected USB devices:

```bash
lsusb
```

Check CUPS printers:

```bash
lpstat -p
```

CUPS web UI:

```text
http://ORANGE_PI_IP:631
```

If CUPS web administration is not accessible:

```bash
sudo cupsctl --remote-admin --remote-any --share-printers
sudo systemctl restart cups
```

Then open port `631` again in your browser.

Add the printer, then return to the Voucher Maker:

**Settings → CUPS Printer → Refresh**

Select the printer and save.

## 4. Voucher TXT format

One code per line:

```text
6idHR1
Twd1YX
SG1nGK
g4SVvM
vJWzxt
AlvpZE
9z98i6
```

You can upload that TXT or paste the codes directly.

## 5. Printing

There are two ways:

### Preview / browser print

Click **Preview** → **Open Thermal Print Layout**.

This is useful while testing.

### Direct Print

Choose the CUPS printer in Settings and click **Print Direct**.

The Orange Pi sends the generated voucher page to CUPS using the `lp` command.

## 6. Change voucher details

Open **Settings** in the web app.

Default values:

```text
Brand: Gravoso Voucher WIFI
Duration: 1 Day
Price: ₱20
Paper: 58mm
```

The settings are saved in `config.json`.

## 7. Admin password

By default there is no password.

To enable one:

**Settings → Admin Password**

Save the password, then reload the page.

Do not commit a real password into a public GitHub repository.

## 8. Auto-start / service commands

Status:

```bash
sudo systemctl status gravoso-voucher
```

Restart:

```bash
sudo systemctl restart gravoso-voucher
```

Stop:

```bash
sudo systemctl stop gravoso-voucher
```

Logs:

```bash
journalctl -u gravoso-voucher -f
```

## 9. Restore after Orange Pi failure

Install Armbian/Debian again, then:

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO
chmod +x install.sh
./install.sh
```

Then reconnect/re-add your thermal printer in CUPS.

## Important printer note

Thermal printers differ. Some work as normal CUPS printers while others are raw ESC/POS printers.

This first version uses CUPS because it is easier to configure and works with many USB/network thermal printers.

If your printer only supports raw ESC/POS, the backend can be changed later to use `python-escpos`.

## Network

The Flask app listens on:

```text
0.0.0.0:5000
```

So devices on the same LAN can open it using:

```text
http://ORANGE_PI_IP:5000
```

Your Orange Pi does not need a monitor after setup.
