#!/usr/bin/env bash
set -e
sudo systemctl disable --now gravoso-voucher 2>/dev/null || true
sudo rm -f /etc/systemd/system/gravoso-voucher.service
sudo systemctl daemon-reload
echo "Service removed. Project files were not deleted."
