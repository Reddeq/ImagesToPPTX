import os
import sys
import logging
import tkinter as tk
from gui.app import ConverterApp

# ✅ Отключение экспериментальных флагов для стабильности на Windows
os.environ["FLAGS_use_pir"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"

# Проверка версий перед импортом
def check_versions():
    try:
        import paddle
        import paddleocr
        pv = paddle.__version__
        ov = paddleocr.__version__
        logging.info(f"PaddlePaddle {pv}, PaddleOCR {ov}")
        
        if not pv.startswith(('3.',)):
            logging.warning(f"⚠️ Рекомендуется PaddlePaddle 3.x, найдено {pv}")
        if not ov.startswith(('3.',)):
            logging.warning(f"⚠️ Рекомендуется PaddleOCR 3.x, найдено {ov}")
    except ImportError as e:
        logging.error(f"❌ Не удалось импортировать зависимости: {e}")
        sys.exit(1)

check_versions()


def main():
    root = tk.Tk()
    root.title("PDF/Image → PPTX (PaddleOCR 3.x)")
    ConverterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()