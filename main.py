import os
import sys
import logging
import tkinter as tk
from gui.app import ConverterApp

# Константы окружения для PaddlePaddle
PADDLE_ENV_VARS = {
    "FLAGS_use_pir": "0",
    "FLAGS_use_mkldnn": "0",
}


def _setup_environment():
    """Настройка переменных окружения для стабильности PaddlePaddle."""
    for key, value in PADDLE_ENV_VARS.items():
        os.environ[key] = value
    
    # В frozen-режиме добавляем пути к пакетам в sys.path
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(sys.executable)
        
        # Добавляем базовую директорию в sys.path для импорта paddleocr, paddlex, ppocr
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
            logging.info(f"Добавлен путь в sys.path: {base_dir}")


def _check_versions():
    """Проверка версий зависимостей перед запуском."""
    try:
        import paddle
        import paddleocr
        
        pv = paddle.__version__
        ov = paddleocr.__version__
        logging.info(f"PaddlePaddle {pv}, PaddleOCR {ov}")
        
        major_version = pv.split('.')[0] if pv else '0'
        if major_version not in ('2', '3'):
            logging.warning(f"⚠️ Рекомендуется PaddlePaddle 2.x или 3.x, найдено {pv}")
            
        major_version = ov.split('.')[0] if ov else '0'
        if major_version not in ('2', '3'):
            logging.warning(f"⚠️ Рекомендуется PaddleOCR 2.x или 3.x, найдено {ov}")
            
    except ImportError as e:
        logging.error(f"❌ Не удалось импортировать зависимости: {e}")
        sys.exit(1)


def main():
    """Точка входа приложения."""
    _setup_environment()
    _check_versions()
    
    root = tk.Tk()
    root.title("PDF/Image → PPTX (PaddleOCR 3.x)")
    ConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()