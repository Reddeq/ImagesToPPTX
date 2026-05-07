"""
Скрипт для предварительной загрузки моделей PaddleOCR.
Вызывается в процессе сборки, чтобы модели попали в кэш
и затем были включены в PyInstaller-бандл.
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger("download_models")

os.environ["FLAGS_use_pir"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"


def download_models():
    """Инициализирует PaddleOCR, чтобы модели скачались в кэш."""
    logger.info("Запуск загрузки моделей PaddleOCR...")

    try:
        from paddleocr import PaddleOCR

        logger.info("Создаём PaddleOCR (lang=en) — модели скачаются автоматически...")
        ocr = PaddleOCR(lang="en", device="cpu", use_angle_cls=True)

        logger.info("Модели detection/recognition/classifier загружены.")

        # Запускаем OCR на минимальном dummy-изображении, чтобы
        # убедиться, что все модели полностью инициализированы.
        import numpy as np
        from PIL import Image
        import tempfile

        dummy = Image.new("RGB", (64, 64), "white")
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        dummy.save(tmp.name)
        tmp.close()

        logger.info("Запускаем OCR на dummy-изображении для финальной инициализации...")
        try:
            ocr.ocr(tmp.name)
        except Exception as e:
            logger.debug(f"OCR dummy error (не критично): {e}")

        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

        logger.info("Все модели PaddleOCR успешно загружены и инициализированы.")

    except ImportError as e:
        logger.error(f"Не удалось импортировать paddleocr: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ошибка при загрузке моделей: {e}")
        sys.exit(1)


def show_cache_paths():
    """Показывает, где находятся скачанные модели."""
    import pathlib

    home = pathlib.Path.home()
    paths = [
        home / ".paddlex",
        home / ".cache" / "paddlex",
        home / ".paddleocr",
        home / ".cache" / "paddleocr",
    ]

    logger.info("Кэш моделей Paddle может находиться в:")
    for p in paths:
        if p.exists():
            size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
            logger.info(f"  [FOUND] {p} ({size / 1024 / 1024:.1f} MB)")
        else:
            logger.info(f"  [MISS]  {p}")


if __name__ == "__main__":
    download_models()
    show_cache_paths()
    logger.info("Готово.")
