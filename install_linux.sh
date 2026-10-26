#!/usr/bin/env bash
set -e

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="discord-conbot"

echo "============================================================"
echo " 🐧 리눅스 서버용 Discord ConBot 자동 설치 및 서비스 등록"
echo " 경로: $APP_DIR"
echo "============================================================"

# 1. Python3 및 venv 확인
if ! command -v python3 &> /dev/null; then
    echo "📦 python3가 설치되어 있지 않아 설치를 시도합니다..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3 python3-pip
    fi
fi

# Ubuntu/Debian에서 python3-venv가 빠진 경우 대비
if ! python3 -m venv "$APP_DIR/.venv_linux" &> /dev/null; then
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3-venv
    fi
    python3 -m venv "$APP_DIR/.venv_linux"
fi

echo "📦 가상환경에 필요한 파이썬 패키지 설치 중..."
"$APP_DIR/.venv_linux/bin/pip" install --upgrade pip
"$APP_DIR/.venv_linux/bin/pip" install -r "$APP_DIR/requirements.txt"

mkdir -p "$APP_DIR/cons" "$APP_DIR/cache"

# 2. systemd 서비스 생성 및 등록 (24시간 상시 구동 & 재부팅 시 자동 시작)
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
CURRENT_USER="$(whoami)"

echo "⚙️ systemd 백그라운드 서비스($SERVICE_NAME) 등록 중..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Discord Big Emoji & Custom Con Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/.venv_linux/bin/python -u ${APP_DIR}/bot.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo "============================================================"
echo "✅ 설치 및 백그라운드 서비스 시작 완료!"
echo ""
echo "📌 유용한 상태 확인 명령어:"
echo "  - 실시간 로그 확인 : sudo journalctl -u ${SERVICE_NAME} -f"
echo "  - 봇 상태 확인     : sudo systemctl status ${SERVICE_NAME}"
echo "  - 봇 재시작        : sudo systemctl restart ${SERVICE_NAME}"
echo "  - 봇 중지          : sudo systemctl stop ${SERVICE_NAME}"
echo "============================================================"
