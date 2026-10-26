<div align="center">

<img src="./docs/mascot.png" alt="디코콘 (DiCoCon) 마스코트" width="180" style="border-radius: 24px;" />

# ✨ 디코콘 (DiCoCon)

**네모난 임베드 테두리 없이, 내 프로필 그대로 보내는 디스코드 큰 이모지 & 무제한 커스텀 콘 봇**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.4+-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](./Dockerfile)

[🌐 **공식 소개 & 콘 보관함 웹페이지**](https://dicocon.vercel.app) · [🏠 **내 서버에 봇 초대하기**](https://discord.com/oauth2/authorize?client_id=1564117482393051206&permissions=536879104&integration_type=0&scope=bot+applications.commands) · [👤 **내 계정에 앱 추가하기 (모든 서버·DM용)**](https://discord.com/oauth2/authorize?client_id=1564117482393051206&integration_type=1&scope=applications.commands)

</div>

---

## 💡 소개

PC 디스코드에서 기본 이모지(48px)는 너무 작아서 잘 보이지 않고, 서버 스티커는 슬롯 제한(5~60개) 때문에 아쉬우셨나요?  
기존 콘 봇들처럼 **봇 이름과 봇 프로필 사진 + 네모난 임베드 박스**로 채팅 흐름을 깨뜨리지 않고, **내 현재 서버 닉네임과 프로필 사진 그대로** 큼직한 이모지와 무제한 커스텀 콘을 전송해 주는 유틸리티 봇입니다.

---

## 🌟 핵심 기능

| 기능 | 설명 |
| :--- | :--- |
| 🔍 **기본 이모지 자동 확대** | 이모지 선택 창(😀)에서 마우스로 클릭해 보내거나 `:이모지:` 1개를 단독 입력하면, 작은 원본을 지우고 **내 프사 + 내 닉네임 그대로 128px 고화질 이미지**로 자동 전환합니다. |
| 💬 **`:콘이름:` 빠른 호출** | 서버 스티커 슬롯 제한 없이 등록된 커스텀 콘을 `:바부:` (또는 단축 입력 `;바부`) 형태로 입력해 0.1초 만에 전송합니다. |
| 🌐 **모든 서버 & 개인 DM `/콘`** | 내 계정에 앱을 추가(User Install)하면, 봇이 없는 다른 서버나 친구와의 1:1 DM에서도 **초성 검색(`ㅂㅂ` ➔ `바부`) 자동완성**으로 콘과 `/이모지확대`를 사용할 수 있습니다. |
| ⚡ **우클릭 한 번으로 콘 저장** | 채팅방에 올라온 이미지나 이모지를 **`우클릭 ➔ 앱 ➔ 콘으로 저장`**만 누르면 즉시 내 콘 목록에 추가됩니다. |
| 🗂️ **브라우저 콘 보관함 웹 제공** | [공식 웹페이지](https://dicocon.vercel.app)에서 내 브라우저에 콘을 모아두고 클릭 한 번으로 복사하거나 웹훅으로 즉시 전송할 수 있습니다. |

---

## 📖 사용법 요약

| 입력 / 동작 | 사용 가능 위치 | 작동 내용 |
| :--- | :---: | :--- |
| **마우스로 이모지 선택 전송** 또는 `:이모지:` 단독 입력 | 디코콘이 초대된 서버 | 내 닉네임·프사 웹훅으로 테두리 없이 **128px 큰 이모지**로 자동 전환 |
| **`:콘이름:`** (예: `:바부:`) 또는 **`;콘이름`** | 디코콘이 초대된 서버 | 등록된 커스텀 콘을 내 닉네임·프사로 즉시 전송 |
| **`/콘 [이름]`** | 모든 서버 · 개인 DM | 초성 검색(`ㅂㅂ`) 및 실시간 자동완성 목록에서 콘 선택 후 전송 |
| **`/이모지확대 [이모지] [크기]`** | 모든 서버 · 개인 DM | `80px` / `96px` / `128px` / `160px` / `256px` 원하는 크기로 이모지 확대 |
| **메시지 우클릭 ➔ `앱` ➔ `콘으로 저장`** | 모든 서버 · 개인 DM | 채팅방의 이미지, 다른 봇의 임베드 콘, 이모지를 내 콘 목록에 즉시 등록 |
| **`/콘등록` · `/콘목록` · `/콘삭제`** | 모든 서버 · 개인 DM | 디스코드 안에서 새 콘 추가(URL/파일), 목록 조회 및 삭제 관리 |

---

## 🛠️ 직접 봇 실행하기 (Self-Hosting)

공식 초대 링크 대신 본인의 독립된 봇 토큰으로 직접 구동하고 싶을 때의 실행 방법입니다.

### 1. 윈도우 PC에서 실행하기
* **일반 실행 (최초 1회 토큰 설정 마법사 포함)**: `실행.bat` 더블클릭
* **창 없이 백그라운드 조용히 실행**: `백그라운드_실행.vbs` 더블클릭 (`Win + R` ➔ `shell:startup` 시작프로그램 폴더에 바로가기를 넣으면 부팅 시 자동 실행)
* **백그라운드 종료**: `백그라운드_종료.bat` 더블클릭

### 2. 리눅스 / Docker 서버에서 실행하기
```bash
git clone https://github.com/eruminyu/DiCoCon.git
cd DiCoCon
cp .env.example .env
nano .env   # DISCORD_TOKEN 입력 후 저장

# 일반 리눅스 (systemd 백그라운드 서비스 자동 등록)
chmod +x install_linux.sh && ./install_linux.sh

# 또는 Docker 사용 시
docker compose up -d --build
```

---

## 📁 프로젝트 구조

```text
DiCoCon/
├── bot.py                 # 디코콘 메인 봇 코드
├── cons_db.json           # 경량 URL 기반 콘 데이터베이스
├── cons/                  # 기본 제공 로컬 콘 이미지 폴더
├── docs/                  # 공식 소개 & 브라우저 콘 보관함 웹페이지
├── Dockerfile             # Docker 컨테이너 빌드 설정
├── docker-compose.yml     # Docker Compose 설정
├── install_linux.sh       # 리눅스 systemd 서비스 원클릭 설치 스크립트
├── 실행.bat               # 윈도우 일반 실행 스크립트
├── 백그라운드_실행.vbs     # 윈도우 무창 백그라운드 실행 스크립트
└── 백그라운드_종료.bat     # 윈도우 백그라운드 프로세스 종료 스크립트
```
