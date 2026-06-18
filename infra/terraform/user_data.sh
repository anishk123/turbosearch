#!/usr/bin/env bash
set -euxo pipefail

dnf update -y
dnf install -y git python3.11 python3.11-pip

useradd --system --home-dir /opt/turbosearch --create-home turbosearch || true
cd /opt/turbosearch

git clone https://github.com/anishk123/turbosearch.git app
cd app

python3.11 -m venv .venv
. .venv/bin/activate
pip install -e .

cat >/etc/systemd/system/turbosearch.service <<SERVICE
[Unit]
Description=turbosearch API
After=network-online.target

[Service]
User=turbosearch
WorkingDirectory=/opt/turbosearch/app
Environment=DATABASE_URL=${database_url}
ExecStart=/opt/turbosearch/app/.venv/bin/turbosearch serve --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable turbosearch
systemctl start turbosearch

