"""
Runtime hook для PaddlePaddle/PaddleOCR в frozen-сборке.

Настройки:
- Добавляет директорию exe в PATH для поиска DLL
- Указывает пути к моделям через переменные окружения
- Отключает экспериментальные флаги PaddlePaddle
"""
import os
import sys
from pathlib import Path


def setup_runtime_environment():
    """Настройка окружения для frozen-сборки."""
    if not getattr(sys, "frozen", False):
        return
    
    # Директория executable
    exe_dir = os.path.dirname(sys.executable)
    
    # Добавляем exe_dir в PATH для поиска DLL
    os.environ["PATH"] = exe_dir + os.pathsep + os.environ.get("PATH", "")
    
    # Определяем базовую директорию
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(exe_dir)
    
    # Проверяем _internal для portable режима
    internal_dir = Path(exe_dir) / "_internal"
    if not internal_dir.is_dir():
        internal_dir = base_dir
    
    # Пути к моделям
    models_dir = internal_dir / "_models"
    if models_dir.is_dir():
        os.environ["PADDLEX_MODEL_PATH"] = str(models_dir)
        os.environ["PADDLEOCR_MODEL_PATH"] = str(models_dir)
    
    # Переменные окружения для стабильности Paddle
    os.environ["FLAGS_use_pir"] = "0"
    os.environ["FLAGS_use_mkldnn"] = "0"


setup_runtime_environment()
