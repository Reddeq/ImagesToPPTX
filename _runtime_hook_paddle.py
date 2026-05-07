
import os
import sys
import pathlib # Импортируем pathlib, чтобы быть уверенными в его доступности

# Добавляем директорию exe в PATH для поиска DLL
exe_dir = os.path.dirname(sys.executable)
if getattr(sys, 'frozen', False):
    os.environ['PATH'] = exe_dir + os.pathsep + os.environ.get('PATH', '')

    # Указываем PaddleX / PaddleOCR где искать модели
    base_dir = pathlib.Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else pathlib.Path(exe_dir)
    internal_dir = os.path.join(exe_dir, '_internal') if os.path.isdir(os.path.join(exe_dir, '_internal')) else str(base_dir)

    models_dir = os.path.join(internal_dir, '_models')
    if os.path.isdir(models_dir):
        # Для paddlex — устанавливаем PADDLEX_MODEL_PATH
        os.environ['PADDLEX_MODEL_PATH'] = models_dir
        # Для paddleocr — устанавливаем PaddleOCR model path
        os.environ['PADDLEOCR_MODEL_PATH'] = models_dir
