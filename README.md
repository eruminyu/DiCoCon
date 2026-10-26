<div align="center">

<img src="./docs/mascot.png" alt="디코콘 (DiCoCon) 마스코트" width="180" style="border-radius: 24px;" />

# ✨ 디코콘 (DiCoCon)

**네모난 임베드 테두리 없이, 내 프로필 그대로 보내는 디스코드 큰 이모지 & 로컬 커스텀 콘 봇**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.4+-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](./Dockerfile)

[🌐 **공식 소개 & 콘 보관함 웹페이지**](https://dicocon.vercel.app) · [🏠 **내 서버에 봇 초대하기**](https://discord.com/oauth2/authorize?client_id=1564117482393051206&permissions=536879104&integration_type=0&scope=bot+applications.commands) · [👤 **내 계정에 앱 추가하기 (모든 서버·DM용)**](https://discord.com/oauth2/authorize?client_id=1564117482393051206&integration_type=1&scope=applications.commands)

</div>

---

## 💡 소개

PC 디스코드에서 기본 이모지(48px)가 너무 작아서 잘 보이지 않으셨나요?  
기존 봇들처럼 **봇 이름과 봇 프로필 사진 + 네모난 임베드 박스**로 채팅 흐름을 깨뜨리지 않고, 평소처럼 디스코드 이모지를 선택해 보내기만 하면 **내 현재 서버 닉네임과 프로필 사진 그대로 128px 고화질 큰 이모지**로 깔끔하게 전환해 주는 유틸리티 봇입니다.

---

## 🌟 기능 안내 (온라인 초대 모드 vs 로컬 직접 실행 모드)

### 1️⃣ 기본 제공 기능 (초대 링크로 바로 사용 가능)
별도 설치 없이 상단 **[내 서버에 봇 초대하기]** 또는 **[내 계정에 앱 추가하기]** 링크만으로 즉시 사용할 수 있는 기능입니다.

| 입력 / 동작 | 사용 가능 위치 | 작동 내용 |
| :--- | :---: | :--- |
| **마우스로 이모지(😀) 선택 전송** 또는 `:이모지:` 단독 입력 | 디코콘이 초대된 서버 | 작은 원본 이모지를 지우고, 내 닉네임·프사 웹훅으로 테두리 없이 **128px 큰 이모지**로 자동 전환 |
| **`/이모지확대 [이모지] [크기]`** | 모든 서버 · 개인 DM | 봇이 없는 서버나 DM에서도 `80px` / `96px` / `128px` / `160px` / `256px` 원하는 크기로 이모지 확대 |
| **웹 브라우저 콘 보관함** | [공식 웹페이지](https://dicocon.vercel.app) | 내 PC 웹 브라우저 저장소에 자주 쓰는 콘을 모아두고 클릭 한 번으로 복사 또는 웹훅 전송 |

### 2️⃣ 로컬 실행 전용 확장 기능 (`실행.bat` 직접 구동 시 활성화)
내 PC에서 직접 봇을 구동(`LOCAL_MODE=true`)할 때 추가로 활성화되는 개인 전용 무제한 콘 기능입니다.

| 입력 / 동작 | 작동 내용 |
| :--- | :--- |
| **`:콘이름:`** (예: `:바부:`) 또는 **`;콘이름`** | 내 PC `cons/` 폴더에 저장된 무제한 커스텀 콘을 내 닉네임·프사 웹훅으로 즉시 전송 |
| **메시지 우클릭 ➔ `앱` ➔ `콘으로 저장`** | 채팅방의 이미지나 이모지를 클릭 한 번으로 내 로컬 콘 목록에 저장 |
| **`/콘 [이름]`** | 초성 검색(`ㅂㅂ` ➔ `바부`) 및 실시간 자동완성으로 내 로컬 콘 전송 |
| **`/콘등록` · `/콘목록` · `/콘삭제`** | 디스코드 안에서 내 로컬 콘 추가, 목록 조회 및 삭제 관리 |

---

## 🛠️ 로컬에서 직접 실행하기 (전체 확장 기능 사용 시)

내 PC에 직접 콘 이미지들을 저장해 두고 모든 확장 기능을 사용하고 싶을 때의 실행 방법입니다.

### 1. 윈도우 PC에서 실행하기 (`LOCAL_MODE=true` 자동 적용)
* **일반 실행 (최초 1회 토큰 설정 마법사 포함)**: `실행.bat` 더블클릭
* **창 없이 백그라운드 조용히 실행**: `백그라운드_실행.vbs` 더블클릭 (`Win + R` ➔ `shell:startup` 시작프로그램 폴더에 바로가기를 넣으면 부팅 시 자동 실행)
* **백그라운드 종료**: `백그라운드_종료.bat` 더블클릭

### 2. 리눅스 / Docker 서버에서 실행하기
```bash
git clone https://github.com/eruminyu/DiCoCon.git
cd DiCoCon
cp .env.example .env
nano .env   # DISCORD_TOKEN 입력 (로컬 콘 기능도 쓰려면 LOCAL_MODE=true 로 변경)

# 일반 리눅스 (systemd 백그라운드 서비스 자동 등록)
chmod +x install_linux.sh && ./install_linux.sh

# 또는 Docker 사용 시
docker compose up -d --build
```
