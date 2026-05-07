import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


try:
    from version import __version__
except Exception:
    __version__ = "0.0.0"


GITHUB_OWNER = "Reddeq"
GITHUB_REPO = "ImagesToPPTX"

# Важно: имя asset-файла в GitHub Releases должно совпадать.
ZIP_ASSET_NAME = "ImagesToPPTX-win64.zip"

APP_NAME = "ImagesToPPTX"
USER_AGENT = f"{APP_NAME}Updater"

API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"


def normalize_version(version: str) -> str:
    """
    Приводит версию к базовому виду.

    Примеры:
        v1.2.3 -> 1.2.3
        V1.2.3 -> 1.2.3
        1.2.3  -> 1.2.3
    """
    if not version:
        return "0.0.0"

    return str(version).lstrip("vV").strip()


def version_tuple(version: str) -> tuple[int, ...]:
    """
    Устойчивое преобразование версии в tuple чисел.

    Примеры:
        1.2.3       -> (1, 2, 3)
        v1.2.3      -> (1, 2, 3)
        1.2.3-beta  -> (1, 2, 3)
        invalid     -> (0,)
    """
    version = normalize_version(version)
    numbers = re.findall(r"\d+", version)

    if not numbers:
        return (0,)

    return tuple(int(part) for part in numbers)


def get_latest_release_info() -> dict | None:
    """
    Получает информацию о последнем GitHub Release.

    Возвращает:
        {
            "version": "1.0.1",
            "tag_name": "v1.0.1",
            "body": "...",
            "asset_url": "https://..."
        }

    Или None, если проверить обновления не удалось.
    """
    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw_data = response.read().decode("utf-8")
            data = json.loads(raw_data)

        tag_name = str(data.get("tag_name", "")).strip()
        body = data.get("body", "") or ""
        assets = data.get("assets", []) or []

        if not tag_name:
            return None

        asset_url = None

        for asset in assets:
            if asset.get("name") == ZIP_ASSET_NAME:
                asset_url = asset.get("browser_download_url")
                break

        return {
            "version": normalize_version(tag_name),
            "tag_name": tag_name,
            "body": body,
            "asset_url": asset_url,
        }

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        json.JSONDecodeError,
        OSError,
    ):
        return None


def is_update_available() -> tuple[bool, dict | None]:
    """
    Проверяет, доступно ли обновление.

    Возвращает:
        (True, info)   если новая версия доступна
        (False, info)  если обновлений нет
        (False, None)  если проверка не удалась
    """
    info = get_latest_release_info()

    if info is None:
        return False, None

    current = version_tuple(__version__)
    latest = version_tuple(info["version"])

    return latest > current, info


def download_zip(asset_url: str) -> str | None:
    """
    Скачивает ZIP-файл обновления во временную папку.
    """
    if not asset_url:
        return None

    zip_path = os.path.join(tempfile.gettempdir(), ZIP_ASSET_NAME)

    request = urllib.request.Request(
        asset_url,
        headers={
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            with open(zip_path, "wb") as file:
                shutil.copyfileobj(response, file)

        if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
            return None

        return zip_path

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError,
    ):
        return None


def safe_extract_zip(zip_path: str, extract_dir: str) -> bool:
    """
    Безопасная распаковка ZIP с защитой от Zip Slip.
    """
    try:
        extract_root = Path(extract_dir).resolve()

        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                member_path = extract_root / member.filename
                resolved_member_path = member_path.resolve()

                if not str(resolved_member_path).startswith(str(extract_root)):
                    return False

            zf.extractall(extract_root)

        return True

    except (zipfile.BadZipFile, OSError):
        return False


def extract_zip(zip_path: str) -> str | None:
    """
    Распаковывает ZIP во временную папку.
    """
    if not zip_path or not os.path.exists(zip_path):
        return None

    extract_dir = os.path.join(tempfile.gettempdir(), f"{APP_NAME}_update")

    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir, ignore_errors=True)

    os.makedirs(extract_dir, exist_ok=True)

    ok = safe_extract_zip(zip_path, extract_dir)

    if not ok:
        return None

    return extract_dir


def find_update_source_dir(extracted_dir: str) -> Path:
    """
    Определяет папку, которую нужно копировать в директорию приложения.

    Поддерживает оба варианта архива:

    1. Файлы лежат прямо в корне:
        extracted/
            ImagesToPPTX.exe
            python311.dll
            ...

    2. Файлы лежат во вложенной папке:
        extracted/
            ImagesToPPTX/
                ImagesToPPTX.exe
                python311.dll
                ...
    """
    root = Path(extracted_dir).resolve()

    if not root.exists():
        return root

    children = list(root.iterdir())
    files = [p for p in children if p.is_file()]
    dirs = [p for p in children if p.is_dir()]

    if files:
        return root

    if len(dirs) == 1:
        return dirs[0].resolve()

    return root


def get_current_app_dir() -> Path:
    """
    Возвращает папку текущего приложения.

    В frozen-сборке:
        папка рядом с exe

    В dev-режиме:
        папка текущего файла updater.py
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def create_update_script(source_dir: Path, target_dir: Path, exe_name: str) -> Path:
    """
    Создаёт BAT-скрипт, который:
    - ждёт закрытия текущего приложения;
    - копирует новые файлы поверх старых;
    - запускает приложение снова.
    """
    script_path = Path(tempfile.gettempdir()) / f"{APP_NAME}_apply_update.bat"

    source_dir = source_dir.resolve()
    target_dir = target_dir.resolve()
    exe_path = target_dir / exe_name

    script = f"""@echo off
chcp 65001 >nul
echo Applying update...

timeout /t 2 /nobreak >nul

robocopy "{source_dir}" "{target_dir}" /E /R:3 /W:1 /NFL /NDL /NJH /NJS /NP

if exist "{exe_path}" (
    start "" "{exe_path}"
)

exit
"""

    script_path.write_text(script, encoding="utf-8")
    return script_path


def run_update_script(script_path: Path) -> bool:
    """
    Запускает BAT-скрипт обновления.
    """
    if os.name != "nt":
        return False

    if not script_path or not Path(script_path).exists():
        return False

    try:
        subprocess.Popen(
            ["cmd", "/c", str(script_path)],
            creationflags=subprocess.CREATE_NO_WINDOW,
            close_fds=True,
        )
        return True

    except OSError:
        return False


def prepare_update(info: dict) -> tuple[bool, str | Path]:
    """
    Подготавливает обновление:
    - скачивает ZIP;
    - распаковывает;
    - создаёт BAT-скрипт.

    ВАЖНО:
        Эта функция НЕ показывает окна.
        Её можно безопасно запускать в фоновом потоке.

    Возвращает:
        (True, script_path)
        или
        (False, error_message)
    """
    if os.name != "nt":
        return False, "Автообновление поддерживается только для Windows-сборки."

    if not getattr(sys, "frozen", False):
        return False, "Проверка обновлений работает только в собранной версии приложения."

    if not info:
        return False, "Нет информации об обновлении."

    asset_url = info.get("asset_url")

    if not asset_url:
        return False, f"В последнем релизе не найден файл {ZIP_ASSET_NAME}."

    zip_path = download_zip(asset_url)

    if not zip_path:
        return False, "Не удалось скачать обновление."

    extracted_dir = extract_zip(zip_path)

    if not extracted_dir:
        return False, "Не удалось распаковать обновление."

    update_source_dir = find_update_source_dir(extracted_dir)

    if not update_source_dir.exists():
        return False, "Не найдена папка с файлами обновления."

    current_app_dir = get_current_app_dir()
    exe_name = Path(sys.executable).name

    script_path = create_update_script(
        source_dir=update_source_dir,
        target_dir=current_app_dir,
        exe_name=exe_name,
    )

    if not script_path.exists():
        return False, "Не удалось создать скрипт обновления."

    return True, script_path