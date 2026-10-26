import os
import sys
import re
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Union
from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse

# 윈도우 기본 콘솔(cp949)에서 이모지/유니코드 출력 시 에러 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from PIL import Image, ImageSequence

# .env 환경변수 로드
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
EMOJI_SIZE = int(os.getenv("EMOJI_SIZE", "128"))
CON_MAX_SIZE = int(os.getenv("CON_MAX_SIZE", "140"))
CON_PREFIX = os.getenv("CON_PREFIX", ";").strip() or ";"
AUTO_ENLARGE_EMOJI = os.getenv("AUTO_ENLARGE_EMOJI", "true").lower() == "true"

# LOCAL_MODE=true 일 때만 커스텀 콘 저장(/콘, /콘등록, 우클릭 콘으로 저장 등) 활성화
# 온라인 초대링크 배포 서버(Render/Koyeb 등)에서는 기본값 false로 동작하여 디스코드 자체 이모지 확대만 수행
LOCAL_MODE = os.getenv("LOCAL_MODE", "false").lower() == "true"

raw_allowed = os.getenv("ALLOWED_USER_IDS", "").strip()
ALLOWED_USER_IDS = {int(x.strip()) for x in raw_allowed.split(",") if x.strip().isdigit()}

CONS_DIR = BASE_DIR / "cons"
CACHE_DIR = BASE_DIR / "cache"
CONS_DB_PATH = BASE_DIR / "cons_db.json"
CONS_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

SUPPORTED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# 디스코드 커스텀 이모지 정규식
SINGLE_EMOJI_PATTERN = re.compile(r"^\s*<(a?):([^:>]+):(\d+)>\s*$")
ANY_EMOJI_PATTERN = re.compile(r"<(a?):([^:>]+):(\d+)>")

# 한글 초성 리스트 (초성 검색 지원용)
CHOSUNG_LIST = [
    "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ",
    "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]


def get_chosung(text: str) -> str:
    """문자열에서 한글 초성만 추출하여 반환합니다 (예: '바부' -> 'ㅂㅂ')."""
    result = []
    for char in text:
        code = ord(char) - 0xAC00
        if 0 <= code <= 11171:
            result.append(CHOSUNG_LIST[code // 588])
        else:
            result.append(char.lower())
    return "".join(result)


def optimize_discord_image_url(url: str, max_size: int = CON_MAX_SIZE) -> str:
    """
    디스코드 CDN 이미지 주소를 media.discordapp.net 프록시 주소로 변환해
    서버에 파일을 저장하지 않고도 지정된 크기(max_size)로 리사이징되도록 만듭니다.
    """
    if max_size <= 0:
        return url
    try:
        parsed = urlparse(url)
        if parsed.netloc in ("cdn.discordapp.com", "media.discordapp.net") and "/attachments/" in parsed.path:
            query = dict(parse_qsl(parsed.query))
            query["width"] = str(max_size)
            query["height"] = str(max_size)
            new_parsed = parsed._replace(netloc="media.discordapp.net", query=urlencode(query))
            return urlunparse(new_parsed)
    except Exception:
        pass
    return url


def load_url_db() -> Dict[str, dict]:
    """
    서버 용량을 차지하지 않는 경량 URL 데이터베이스(cons_db.json)를 로드합니다.
    구조:
    {
      "global": { "콘이름": "https://..." },
      "users": { "유저ID": { "콘이름": "https://..." } }
    }
    """
    if not CONS_DB_PATH.exists():
        return {"global": {}, "users": {}}
    try:
        data = json.loads(CONS_DB_PATH.read_text(encoding="utf-8"))
        if "global" not in data:
            data["global"] = {}
        if "users" not in data:
            data["users"] = {}
        return data
    except Exception:
        return {"global": {}, "users": {}}


def save_url_db(data: Dict[str, dict]) -> None:
    CONS_DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def register_url_con(name: str, url: str, user_id: Optional[int] = None, is_global: bool = True) -> None:
    """이미지 파일 대신 URL 텍스트(약 80바이트)만 DB에 저장합니다."""
    db = load_url_db()
    optimized_url = optimize_discord_image_url(url, CON_MAX_SIZE)
    if user_id is not None:
        uid = str(user_id)
        db["users"].setdefault(uid, {})[name] = optimized_url
    if is_global:
        db["global"][name] = optimized_url
    save_url_db(db)


def delete_con_entry(name: str, user_id: Optional[int] = None) -> bool:
    """URL DB(또는 로컬 파일)에서 콘을 삭제합니다."""
    db = load_url_db()
    deleted = False
    if user_id is not None:
        uid = str(user_id)
        if uid in db["users"] and name in db["users"][uid]:
            del db["users"][uid][name]
            deleted = True
    if name in db["global"]:
        del db["global"][name]
        deleted = True
    if deleted:
        save_url_db(db)
    return deleted


def get_available_cons(user_id: Optional[int] = None) -> Dict[str, Union[str, Path]]:
    """
    사용 가능한 모든 콘을 반환합니다.
    - 값(Value)이 str 이면: URL 방식 (서버 디스크 용량 0MB)
    - 값(Value)이 Path 이면: 서버 로컬 cons/ 폴더에 직접 넣어둔 기본 이미지 파일
    우선순위: 내 개인 등록 URL 콘 > 공용 등록 URL 콘 > cons/ 로컬 폴더 기본 파일
    """
    cons: Dict[str, Union[str, Path]] = {}

    # 1. 로컬 cons/ 폴더 내 기본 제공 이미지 스캔
    for file_path in sorted(CONS_DIR.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTS:
            rel_stem = file_path.relative_to(CONS_DIR).with_suffix("").as_posix()
            cons[rel_stem] = file_path
            if "/" in rel_stem and file_path.stem not in cons:
                cons[file_path.stem] = file_path

    # 2. URL DB (공용 및 개인 콘) 병합
    db = load_url_db()
    for k, url in db.get("global", {}).items():
        cons[k] = url
    if user_id is not None:
        user_cons = db.get("users", {}).get(str(user_id), {})
        for k, url in user_cons.items():
            cons[k] = url

    return cons


def get_resized_con_path(src_path: Path, max_size: int = CON_MAX_SIZE) -> Path:
    """로컬 cons/ 폴더의 원본 이미지가 max_size보다 크면 비율을 유지한 채 리사이징합니다."""
    if max_size <= 0:
        return src_path

    stat = src_path.stat()
    cache_key = f"{src_path.name}_{stat.st_mtime_ns}_{max_size}"
    cache_hash = hashlib.md5(cache_key.encode("utf-8")).hexdigest()[:12]
    ext = src_path.suffix.lower()
    cached_path = CACHE_DIR / f"{src_path.stem}_{cache_hash}{ext}"

    if cached_path.exists():
        return cached_path

    try:
        with Image.open(src_path) as im:
            width, height = im.size
            if width <= max_size and height <= max_size:
                return src_path

            ratio = min(max_size / width, max_size / height)
            new_size = (max(1, int(width * ratio)), max(1, int(height * ratio)))

            is_animated = getattr(im, "is_animated", False) and getattr(im, "n_frames", 1) > 1
            if is_animated and ext in {".gif", ".webp"}:
                frames = []
                durations = []
                for frame in ImageSequence.Iterator(im):
                    durations.append(frame.info.get("duration", 50))
                    rgba_frame = frame.convert("RGBA").resize(new_size, Image.Resampling.LANCZOS)
                    frames.append(rgba_frame)

                out_path = cached_path.with_suffix(".webp")
                if out_path.exists():
                    return out_path
                frames[0].save(
                    out_path,
                    format="WEBP",
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=0,
                    lossless=False,
                    quality=90,
                )
                return out_path
            else:
                resized = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB").resize(
                    new_size, Image.Resampling.LANCZOS
                )
                out_ext = ".png" if resized.mode == "RGBA" and ext in {".jpg", ".jpeg"} else ext
                out_path = cached_path.with_suffix(out_ext)
                resized.save(out_path, quality=92)
                return out_path
    except Exception as e:
        print(f"[경고] 이미지 리사이징 실패 ({src_path.name}), 원본을 전송합니다: {e}")
        return src_path


class SaveConModal(discord.ui.Modal, title="디코콘 — 나만의 콘으로 저장"):
    """메시지 우클릭 -> '콘으로 저장' 클릭 시 이미지 URL을 저장"""

    con_name = discord.ui.TextInput(
        label="저장할 콘 이름",
        placeholder="예: 바부 (이후 :바부: 또는 /콘 바부 로 사용 가능)",
        min_length=1,
        max_length=32,
        required=True,
    )

    def __init__(self, image_url: str):
        super().__init__()
        self.image_url = image_url

    async def on_submit(self, interaction: discord.Interaction):
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", self.con_name.value.strip())
        if not safe_name:
            await interaction.response.send_message("❌ 사용할 수 없는 이름입니다.", ephemeral=True)
            return

        register_url_con(safe_name, self.image_url, user_id=interaction.user.id, is_global=True)

        await interaction.response.send_message(
            f"✅ **`{safe_name}`** 콘이 저장되었습니다!\n"
            f"- 서버 채팅창: `:{safe_name}:` (또는 `{CON_PREFIX}{safe_name}`)\n"
            f"- 모든 서버/DM 슬래시 명령어: `/콘 {safe_name}`",
            ephemeral=True,
        )


class ConBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.webhooks = True
        super().__init__(command_prefix="!", intents=intents)
        self.webhook_cache: Dict[int, discord.Webhook] = {}

    async def setup_hook(self):
        if LOCAL_MODE:
            save_con_menu = app_commands.ContextMenu(
                name="콘으로 저장",
                callback=self.context_save_con,
            )
            save_con_menu.allowed_installs = app_commands.AppInstallationType(guild=True, user=True)
            save_con_menu.allowed_contexts = app_commands.AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            )
            self.tree.add_command(save_con_menu)

        await self.tree.sync()
        if LOCAL_MODE:
            print("🔄 [로컬 모드] 전체 슬래시 명령어(/이모지확대, /콘, /콘등록, /콘목록, /콘삭제, 우클릭 '콘으로 저장') 동기화 완료!")
        else:
            print("🔄 [온라인 배포 모드] 디스코드 자체 이모지 확대 전용(/이모지확대) 명령어 동기화 완료!")

    async def on_ready(self):
        app_id = self.application_id or self.user.id
        guild_invite_url = (
            f"https://discord.com/oauth2/authorize?client_id={app_id}"
            f"&permissions=536879104&integration_type=0&scope=bot+applications.commands"
        )
        user_install_url = (
            f"https://discord.com/oauth2/authorize?client_id={app_id}"
            f"&integration_type=1&scope=applications.commands"
        )

        # 프론트 웹페이지(docs/index.html)에도 내 봇의 Application ID를 자동 반영
        index_html = BASE_DIR / "docs" / "index.html"
        if index_html.exists():
            try:
                html_text = index_html.read_text(encoding="utf-8")
                updated_html = re.sub(
                    r"const DEFAULT_CLIENT_ID = localStorage\.getItem\('dicocon_client_id'\) \|\| '[^']*';",
                    f"const DEFAULT_CLIENT_ID = localStorage.getItem('dicocon_client_id') || '{app_id}';",
                    html_text,
                )
                if updated_html != html_text:
                    index_html.write_text(updated_html, encoding="utf-8")
            except Exception:
                pass

        print("=" * 70)
        print(f"✅ 디코콘(DiCoCon) 봇 로그인 완료: {self.user} (ID: {app_id})")
        print(f"⚙️ 실행 모드: {'로컬 전체 기능 모드 (커스텀 콘 저장 활성)' if LOCAL_MODE else '온라인 클라우드 모드 (디스코드 자체 이모지 확대 전용)'}")
        print(f"🔍 기본 이모지 자동 확대: {'켜짐' if AUTO_ENLARGE_EMOJI else '꺼짐'} ({EMOJI_SIZE}px)")
        if LOCAL_MODE:
            cons = get_available_cons()
            print(f"📂 현재 사용 가능한 로컬 콘 개수: {len(cons)}개")
            print(f"💬 채팅창 콘 호출 방법: ':콘이름:' 또는 '{CON_PREFIX}콘이름'")
        print("-" * 70)
        print("🔗 [1] 내 서버에 봇 초대하기 링크 (Ctrl+클릭 또는 복사하여 브라우저에 입력):")
        print(f"   {guild_invite_url}")
        print()
        print("🔗 [2] 내 계정에 앱 추가하기 링크 (모든 서버/DM에서 사용):")
        print(f"   {user_install_url}")
        print("=" * 70)
        print("💡 이 창을 켜두는 동안 봇이 작동합니다. 이제 디스코드에서 이모지를 보내보세요!")

    async def get_or_create_webhook(self, channel: discord.abc.GuildChannel) -> Optional[discord.Webhook]:
        target_channel = channel.parent if isinstance(channel, discord.Thread) else channel
        if not isinstance(target_channel, (discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.ForumChannel)):
            return None

        cached = self.webhook_cache.get(target_channel.id)
        if cached is not None:
            return cached

        try:
            webhooks = await target_channel.webhooks()
            for wh in webhooks:
                if wh.user == self.user or wh.name in ("DiCoCon-Webhook", "ConBot-Webhook"):
                    self.webhook_cache[target_channel.id] = wh
                    return wh

            new_wh = await target_channel.create_webhook(name="DiCoCon-Webhook", reason="디코콘(DiCoCon) 큰 이모지 및 커스텀 콘 전송용 웹훅")
            self.webhook_cache[target_channel.id] = new_wh
            return new_wh
        except discord.Forbidden:
            print(f"[권한 부족] '{target_channel.name}' 채널에 '웹훅 관리(Manage Webhooks)' 권한이 없습니다.")
            return None
        except Exception as e:
            print(f"[오류] 웹훅 가져오기/생성 실패: {e}")
            return None

    async def send_as_user_webhook(
        self,
        message: discord.Message,
        content: Optional[str] = None,
        file_path: Optional[Path] = None,
    ) -> bool:
        if not message.guild:
            return False

        webhook = await self.get_or_create_webhook(message.channel)
        if not webhook:
            return False

        send_kwargs = {
            "username": message.author.display_name,
            "avatar_url": message.author.display_avatar.url,
            "allowed_mentions": discord.AllowedMentions.none(),
        }
        if isinstance(message.channel, discord.Thread):
            send_kwargs["thread"] = message.channel
        if content:
            send_kwargs["content"] = content
        if file_path:
            send_kwargs["file"] = discord.File(file_path)

        try:
            await webhook.send(**send_kwargs)
            return True
        except Exception as e:
            target_id = message.channel.parent.id if isinstance(message.channel, discord.Thread) else message.channel.id
            self.webhook_cache.pop(target_id, None)
            print(f"[경고] 웹훅 전송 재시도 중: {e}")
            webhook = await self.get_or_create_webhook(message.channel)
            if webhook:
                try:
                    if file_path:
                        send_kwargs["file"] = discord.File(file_path)
                    await webhook.send(**send_kwargs)
                    return True
                except Exception as retry_err:
                    print(f"[오류] 웹훅 전송 최종 실패: {retry_err}")
            return False

    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if ALLOWED_USER_IDS and message.author.id not in ALLOWED_USER_IDS:
            return

        text = message.content.strip()

        # 1) [로컬 모드 전용] ':콘이름:' 또는 ';콘이름' 형태의 커스텀 콘 호출 감지
        if LOCAL_MODE:
            query = None
            if text.startswith(":") and text.endswith(":") and len(text) > 2 and " " not in text:
                query = text[1:-1].strip()
            elif text.startswith(CON_PREFIX) and len(text) > len(CON_PREFIX):
                query = text[len(CON_PREFIX):].strip()

            if query:
                cons = get_available_cons(user_id=message.author.id)
                target = cons.get(query)
                if target:
                    try:
                        await message.delete()
                    except discord.Forbidden:
                        print("[권한 부족] 원본 메시지를 삭제할 '메시지 관리(Manage Messages)' 권한이 없습니다.")

                    if isinstance(target, str):
                        await self.send_as_user_webhook(message, content=target)
                    else:
                        resized_path = get_resized_con_path(target, CON_MAX_SIZE)
                        await self.send_as_user_webhook(message, file_path=resized_path)
                    return

        # 2) 디스코드 기본 커스텀 이모지 단독 1개 입력 시 자동 확대
        if AUTO_ENLARGE_EMOJI:
            match = SINGLE_EMOJI_PATTERN.match(text)
            if match:
                is_animated, _, emoji_id = match.groups()
                ext = "gif" if is_animated == "a" else "webp"
                enlarged_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}?size={EMOJI_SIZE}&quality=lossless"
                try:
                    await message.delete()
                except discord.Forbidden:
                    print("[권한 부족] 원본 메시지를 삭제할 '메시지 관리(Manage Messages)' 권한이 없습니다.")
                await self.send_as_user_webhook(message, content=enlarged_url)
                return

    async def context_save_con(self, interaction: discord.Interaction, message: discord.Message):
        """메시지 우클릭 -> 앱 -> '콘으로 저장' 실행 시 이미지 URL만 추출해 저장합니다."""
        image_url = None

        # 1순위: 첨부파일 이미지 확인
        for att in message.attachments:
            if att.content_type and att.content_type.startswith("image/"):
                image_url = att.url
                break

        # 2순위: 임베드 이미지 확인
        if not image_url and message.embeds:
            for emb in message.embeds:
                if emb.image and emb.image.url:
                    image_url = emb.image.url
                    break
                if emb.thumbnail and emb.thumbnail.url:
                    image_url = emb.thumbnail.url
                    break

        # 3순위: 메시지에 포함된 커스텀 이모지 확인
        if not image_url:
            em_match = ANY_EMOJI_PATTERN.search(message.content)
            if em_match:
                is_anim, _, em_id = em_match.groups()
                ext = ".gif" if is_anim == "a" else ".webp"
                image_url = f"https://cdn.discordapp.com/emojis/{em_id}{ext}?size={EMOJI_SIZE}&quality=lossless"

        # 4순위: 스티커 확인
        if not image_url and message.stickers:
            image_url = message.stickers[0].url

        if not image_url:
            await interaction.response.send_message(
                "❌ 이 메시지에서 저장할 수 있는 이미지, 콘, 또는 커스텀 이모지를 찾지 못했습니다.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(SaveConModal(image_url=image_url))


bot = ConBot()


# =====================================================================
# 슬래시 명령어들 (User-Installable + Guild 공용)
# =====================================================================

async def con_name_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    cons = get_available_cons(user_id=interaction.user.id)
    q = current.strip().lower()
    q_chosung = get_chosung(q)

    choices = []
    for name in cons.keys():
        name_lower = name.lower()
        name_chosung = get_chosung(name_lower)
        if not q or (q in name_lower) or (q_chosung in name_chosung):
            choices.append(app_commands.Choice(name=name, value=name))
        if len(choices) >= 25:
            break
    return choices


@bot.tree.command(name="이모지확대", description="디스코드 기본 커스텀 이모지를 임베드 테두리 없이 원하는 크기로 확대해서 보냅니다")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@app_commands.describe(
    이모지="확대할 커스텀 이모지를 입력하세요 (예: :바부:)",
    크기="표시할 이미지 크기 (기본값: 128)",
)
@app_commands.choices(
    크기=[
        app_commands.Choice(name="작게 (80px)", value=80),
        app_commands.Choice(name="보통 (96px)", value=96),
        app_commands.Choice(name="추천 크기 (128px)", value=128),
        app_commands.Choice(name="크게 - 스티커 크기 (160px)", value=160),
        app_commands.Choice(name="특대 (256px)", value=256),
    ]
)
async def slash_enlarge_emoji(
    interaction: discord.Interaction,
    이모지: str,
    크기: int = EMOJI_SIZE,
):
    match = ANY_EMOJI_PATTERN.search(이모지)
    if not match:
        await interaction.response.send_message(
            "❌ 디스코드 커스텀 이모지를 입력해주세요! (기본 유니코드 이모지 😀 등은 확대할 수 없습니다)",
            ephemeral=True,
        )
        return

    is_animated, _, emoji_id = match.groups()
    ext = "gif" if is_animated == "a" else "webp"
    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}?size={크기}&quality=lossless"
    await interaction.response.send_message(content=url)


# =====================================================================
# [로컬 실행 모드 전용] 커스텀 콘 관리 명령어 (LOCAL_MODE=true 일 때만 등록)
# =====================================================================
if LOCAL_MODE:
    @bot.tree.command(name="콘", description="[로컬 전용] 등록된 커스텀 콘을 큰 이미지로 전송합니다 (초성/이름 검색 가능)")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(이름="보낼 콘의 이름을 입력하거나 목록에서 선택하세요")
    @app_commands.autocomplete(이름=con_name_autocomplete)
    async def slash_con(interaction: discord.Interaction, 이름: str):
        cons = get_available_cons(user_id=interaction.user.id)
        target = cons.get(이름)
        if not target:
            await interaction.response.send_message(
                f"❌ `{이름}` 콘을 찾을 수 없습니다. `/콘등록`을 쓰거나 메시지를 우클릭해 `콘으로 저장`을 눌러보세요!",
                ephemeral=True,
            )
            return

        if isinstance(target, str):
            await interaction.response.send_message(content=target)
        else:
            resized_path = get_resized_con_path(target, CON_MAX_SIZE)
            await interaction.response.send_message(file=discord.File(resized_path))

    @bot.tree.command(name="콘등록", description="[로컬 전용] 이미지 주소(URL)나 파일로 새 콘을 등록합니다")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(
        이름="저장할 콘 이름 (예: 바부)",
        이미지주소="등록할 이미지 URL 또는 커스텀 이모지 (선택)",
        파일="또는 내 기기에서 업로드할 이미지 파일 (선택)",
    )
    async def slash_register_con(
        interaction: discord.Interaction,
        이름: str,
        이미지주소: Optional[str] = None,
        파일: Optional[discord.Attachment] = None,
    ):
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", 이름.strip())
        if not safe_name:
            await interaction.response.send_message("❌ 사용할 수 없는 이름입니다.", ephemeral=True)
            return

        target_url = None
        if 파일 is not None:
            ext = Path(파일.filename).suffix.lower() or ".png"
            if ext in SUPPORTED_EXTS:
                save_path = CONS_DIR / f"{safe_name}{ext}"
                await 파일.save(save_path)
                await interaction.response.send_message(
                    f"✅ **`{safe_name}`** 콘이 로컬 `cons/` 폴더에 저장되었습니다!\n"
                    f"- 서버 채팅: `:{safe_name}:` (또는 `{CON_PREFIX}{safe_name}`)\n"
                    f"- 슬래시 명령어: `/콘 {safe_name}`",
                    ephemeral=True,
                )
                return
            target_url = 파일.url
        elif 이미지주소:
            em_match = ANY_EMOJI_PATTERN.search(이미지주소)
            if em_match:
                is_anim, _, em_id = em_match.groups()
                ext = ".gif" if is_anim == "a" else ".webp"
                target_url = f"https://cdn.discordapp.com/emojis/{em_id}{ext}?size={EMOJI_SIZE}&quality=lossless"
            elif 이미지주소.startswith(("http://", "https://")):
                target_url = 이미지주소.strip()

        if not target_url:
            await interaction.response.send_message(
                "❌ `이미지주소`(URL/이모지) 또는 `파일` 중 하나를 반드시 입력해주세요!",
                ephemeral=True,
            )
            return

        register_url_con(safe_name, target_url, user_id=interaction.user.id, is_global=True)
        await interaction.response.send_message(
            f"✅ **`{safe_name}`** 콘이 등록되었습니다!\n"
            f"- 서버 채팅: `:{safe_name}:` (또는 `{CON_PREFIX}{safe_name}`)\n"
            f"- 슬래시 명령어: `/콘 {safe_name}`",
            ephemeral=True,
        )

    @bot.tree.command(name="콘목록", description="[로컬 전용] 현재 등록되어 있는 모든 커스텀 콘 목록을 확인합니다")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def slash_list_cons(interaction: discord.Interaction):
        cons = get_available_cons(user_id=interaction.user.id)
        if not cons:
            await interaction.response.send_message(
                "📂 아직 등록된 콘이 없습니다.\n`cons` 폴더에 이미지를 넣거나 `/콘등록` 명령어를 사용해 보세요!",
                ephemeral=True,
            )
            return

        names = sorted(cons.keys())
        formatted = ", ".join(f"`:{n}:`" for n in names[:100])
        extra = f"\n...(외 {len(names) - 100}개)" if len(names) > 100 else ""
        await interaction.response.send_message(
            f"📂 **등록된 콘 목록 (총 {len(names)}개)**\n"
            f"호출 방법: 채팅창에 `:이름:` (또는 `{CON_PREFIX}이름`) 입력 또는 `/콘 이름`\n\n"
            f"{formatted}{extra}",
            ephemeral=True,
        )

    @bot.tree.command(name="콘삭제", description="[로컬 전용] 등록된 커스텀 콘을 삭제합니다")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.describe(이름="삭제할 콘의 이름을 선택하세요")
    @app_commands.autocomplete(이름=con_name_autocomplete)
    async def slash_delete_con(interaction: discord.Interaction, 이름: str):
        if delete_con_entry(이름, user_id=interaction.user.id):
            await interaction.response.send_message(f"🗑️ **`{이름}`** 콘이 삭제되었습니다.", ephemeral=True)
            return

        if not ALLOWED_USER_IDS or interaction.user.id in ALLOWED_USER_IDS:
            cons = get_available_cons()
            target = cons.get(이름)
            if isinstance(target, Path) and target.exists():
                target.unlink(missing_ok=True)
                await interaction.response.send_message(f"🗑️ 로컬 콘 **`{이름}`** 파일이 삭제되었습니다.", ephemeral=True)
                return

        await interaction.response.send_message(f"❌ `{이름}` 콘을 찾을 수 없거나 삭제 권한이 없습니다.", ephemeral=True)


async def run_bot_with_cloud_server(token: str):
    """
    1) 클라우드 배포(Render/Koyeb 등) 시 디스코드 로그인 전에 HTTP 포트를 가장 먼저 열어
       'No open ports detected' 배포 실패를 방지합니다.
    2) 무료 클라우드 공용 IP에서 발생하는 Discord 429(Rate Limit) 에러 시
       프로세스가 죽어서 재시작 루프에 빠지지 않고 대기 후 안전하게 재시도합니다.
    """
    import asyncio
    import aiohttp
    from aiohttp import web

    port_str = os.getenv("PORT", "").strip()
    if port_str.isdigit():
        async def handle_health(request):
            return web.Response(text="DiCoCon Bot is running!", status=200)

        app = web.Application()
        app.router.add_get("/", handle_health)
        app.router.add_get("/health", handle_health)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", int(port_str))
        await site.start()
        print(f"🌐 클라우드 헬스체크 웹 서버 최우선 가동 완료 (Port: {port_str})")

        external_url = os.getenv("RENDER_EXTERNAL_URL", "").strip()
        if external_url:
            async def keep_alive_loop():
                ping_target = f"{external_url.rstrip('/')}/health"
                while True:
                    await asyncio.sleep(600)
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(ping_target, timeout=10):
                                pass
                    except Exception:
                        pass

            asyncio.create_task(keep_alive_loop())
            print(f"⏰ Render 24시간 자동 절전 방지(Self-Ping) 활성화 완료: {external_url}")

    retry_delay = 25
    while True:
        try:
            # 이전 시도에서 세션이 닫혔다면 초기화하여 재연결 가능하도록 처리
            if getattr(bot.http, "_HTTPClient__session", None) is not None:
                try:
                    await bot.http.close()
                except Exception:
                    pass
                bot.http._HTTPClient__session = None

            await bot.start(token)
            break
        except discord.errors.HTTPException as e:
            if e.status == 429:
                print(
                    f"⚠️ [주의] 현재 클라우드 공용 IP가 디스코드 429(Rate Limit) 제한에 걸려 있습니다. "
                    f"{retry_delay}초 후 자동으로 재접속을 시도합니다..."
                )
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)
            else:
                raise


if __name__ == "__main__":
    import asyncio

    if not TOKEN or TOKEN == "여기에_디스코드_봇_토큰을_넣어주세요":
        import webbrowser

        print("=" * 65)
        print(" 👋 환영합니다! 디코콘(DiCoCon) 최초 1회 설정 마법사입니다.")
        print("=" * 65)
        print("아직 디스코드 봇 토큰(DISCORD_TOKEN)이 입력되지 않았습니다.\n")
        print("[토큰 발급 방법 - 1분 소요]")
        print(" 1. https://discord.com/developers/applications 접속")
        print(" 2. 우측 상단 [New Application] 클릭 -> 이름(예: 디코콘) 입력 후 생성")
        print(" 3. 좌측 메뉴 [Installation] -> 'User Install'과 'Guild Install' 모두 체크 후 [Save Changes]")
        print(" 4. 좌측 메뉴 [Bot] 클릭:")
        print("    - 아래 'MESSAGE CONTENT INTENT' 스위치 켜기 -> [Save Changes]")
        print("    - 위쪽 [Reset Token] 버튼을 눌러 나온 토큰 복사하기")
        print("-" * 65)

        ans = input("👉 지금 디스코드 개발자 포털 사이트를 브라우저로 열까요? (엔터 또는 y 입력 시 열림): ").strip().lower()
        if ans in ("", "y", "yes", "ㅇ"):
            webbrowser.open("https://discord.com/developers/applications")

        print()
        new_token = input("🔑 복사한 봇 토큰(Token)을 여기에 붙여넣고 엔터를 눌러주세요:\n> ").strip()
        if new_token:
            env_path = BASE_DIR / ".env"
            env_text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
            if "DISCORD_TOKEN=" in env_text:
                env_text = re.sub(r"DISCORD_TOKEN=.*", f"DISCORD_TOKEN={new_token}", env_text)
            else:
                env_text += f"\nDISCORD_TOKEN={new_token}\n"
            env_path.write_text(env_text, encoding="utf-8")
            TOKEN = new_token
            print("\n✅ .env 파일에 토큰이 자동으로 저장되었습니다! 봇을 시작합니다...\n")
            asyncio.run(run_bot_with_cloud_server(TOKEN))
        else:
            print("\n❌ 토큰이 입력되지 않아 종료합니다. 다시 실행.bat을 켜서 입력해주세요.")
    else:
        asyncio.run(run_bot_with_cloud_server(TOKEN))

