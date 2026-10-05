#!/usr/bin/env bash
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(whoami)"

echo "Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-venv python3-pip cups cups-client

echo "Adding $USER_NAME to lpadmin group..."
sudo usermod -aG lpadmin "$USER_NAME" || true

echo "Creating virtual environment..."
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "Creating systemd service..."
sudo tee /etc/systemd/system/gravoso-voucher.service >/dev/null <<EOF
[Unit]
Description=Gravoso Voucher Maker
After=network.target cups.service
Wants=cups.service

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$APP_DIR
Environment=PYTHONUNBUFFERED=1
Environment=SECRET_KEY=change-this-in-production
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable gravoso-voucher
sudo systemctl restart gravoso-voucher

IP="$(hostname -I | awk '{print $1}')"
echo
echo "Done."
echo "Open: http://$IP:5000"
echo
echo "CUPS printer setup: http://$IP:631"
echo "If CUPS web admin is blocked, run:"
echo "  sudo cupsctl --remote-admin --remote-any --share-printers"
echo "  sudo systemctl restart cups"
