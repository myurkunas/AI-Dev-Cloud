#!/bin/bash
# EC2 user-data bootstrap for the Heinz Admissions Assistant (TM1 prototype).
#
# Paste this into the "User data" field when launching an Amazon Linux 2023
# instance (see deploy/aws-ec2-guide.md). It installs Python, fetches the app
# from GitHub, and runs it as a systemd service on port 80. Runs as root at
# first boot. Progress is logged to /var/log/cloud-init-output.log.
#
# No secrets required: the app runs in stub mode (GENERATION_BACKEND=auto with
# no ANTHROPIC_API_KEY). To enable the Claude backend, add an EnvironmentFile or
# Environment= line to the systemd unit below.

set -euxo pipefail

REPO_URL="https://github.com/myurkunas/AI-Dev-Cloud.git"
APP_DIR="/opt/heinz-assistant"

dnf update -y
dnf install -y python3 python3-pip git

git clone "$REPO_URL" "$APP_DIR"

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

cat > /etc/systemd/system/heinz-assistant.service <<'UNIT'
[Unit]
Description=Heinz Admissions Assistant (TM1 prototype)
After=network.target

[Service]
WorkingDirectory=/opt/heinz-assistant
ExecStart=/opt/heinz-assistant/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 80
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now heinz-assistant.service
