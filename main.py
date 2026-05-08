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