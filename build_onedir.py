"""
Скрипт для создания onedir сборки приложения ImagesToPPTX для Windows.

Использование:
    python build_onedir.py

Требования:
    - PyInstaller 6.20.0+
    - Python 3.11.9+
    - Все зависимости установлены в виртуальное окружение

Результат:
    В папке dist/ будет создана папка ImagesToPPTX/ со всеми файлами приложения.
    
Важно:
    - Модели PaddleOCR НЕ включаются в сборку автоматически
    - Пользователь скачает модели при первом запуске автоматически
    - Модели сохраняются в %USERPROFILE%\\paddleocr
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def main():
    # Пути
    root_dir = Path(__file__).parent.resolve()
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"
    spec_file = root_dir / "ImagesToPPTX.spec"
    
    app_name = "ImagesToPPTX"
    output_dir = dist_dir / app_name
    
    print("=" * 60)
    print(f"Сборка {app_name} (onedir режим для Windows)")
    print("=" * 60)
    
    # Очистка предыдущих сборок
    print("\n[1/5] Очистка предыдущих сборок...")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print(f"  Удалена папка: {dist_dir}")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"  Удалена папка: {build_dir}")
    
    if spec_file.exists():
        spec_file.unlink()
        print(f"  Удалён файл: {spec_file}")
    
    print("\n[2/5] Подготовка параметров сборки...")
    print("  ⚠️ Модели Paddle НЕ включаются в сборку.")
    print("     Пользователь загрузит их при первом запуске автоматически.")
    
    # Формирование команды PyInstaller
    print("\n[3/5] Запуск PyInstaller...")
    
    # Получаем путь к сайпакетам для добавления данных из paddleocr и paddlex
    try:
        import paddleocr
        import paddlex
        import ppocr
        paddleocr_path = Path(paddleocr.__file__).parent
        paddlex_path = Path(paddlex.__file__).parent
        ppocr_path = Path(ppocr.__file__).parent
        print(f"  Путь к paddleocr: {paddleocr_path}")
        print(f"  Путь к paddlex: {paddlex_path}")
        print(f"  Путь к ppocr: {ppocr_path}")
    except ImportError as e:
        print(f"  ⚠️ Не удалось импортировать пакеты: {e}")
        paddleocr_path = None
        paddlex_path = None
        ppocr_path = None
    
    pyinstaller_cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", app_name,
        "--onedir",  # onedir режим
        "--windowed",  # GUI приложение (без консоли)
        "--icon=NONE",  # Без иконки (можно добавить свой .ico)
        # Добавляем исходные файлы модулей
        "--add-data", f"{os.path.join('gui', '*.py')}{os.pathsep}gui",
        "--add-data", f"{os.path.join('ocr_paddle', '*.py')}{os.pathsep}ocr_paddle",
        "--add-data", f"{os.path.join('ocr_to_pptx', '*.py')}{os.pathsep}ocr_to_pptx",
        "--add-data", f"{os.path.join('updater', '*.py')}{os.pathsep}updater",
        # Скрытые импорты для PaddlePaddle и PaddleOCR
        "--hidden-import", "paddle",
        "--hidden-import", "paddleocr",
        "--hidden-import", "paddle.nn",
        "--hidden-import", "paddle.nn.layer",
        "--hidden-import", "paddle.nn.layer.common",
        "--hidden-import", "paddle.nn.layer.activation",
        "--hidden-import", "paddle.nn.layer.conv",
        "--hidden-import", "paddle.nn.layer.pooling",
        "--hidden-import", "paddle.nn.layer.norm",
        "--hidden-import", "paddle.nn.layer.rnn",
        "--hidden-import", "paddle.nn.layer.transformer",
        "--hidden-import", "paddle.optimizer",
        "--hidden-import", "paddle.optimizer.lr",
        "--hidden-import", "paddle.distribution",
        "--hidden-import", "paddle.fluid",
        "--hidden-import", "paddle.inference",
        "--hidden-import", "paddle.base",
        "--hidden-import", "paddle.base.framework",
        "--hidden-import", "paddle.base.core",
        "--hidden-import", "paddle.autograd",
        # Для PaddleOCR
        "--hidden-import", "ppocr",
        "--hidden-import", "ppocr.data",
        "--hidden-import", "ppocr.data.imaug",
        "--hidden-import", "ppocr.modeling",
        "--hidden-import", "ppocr.modeling.architectures",
        "--hidden-import", "ppocr.modeling.backbones",
        "--hidden-import", "ppocr.modeling.heads",
        "--hidden-import", "ppocr.modeling.necks",
        "--hidden-import", "ppocr.postprocess",
        "--hidden-import", "ppocr.utils",
        "--hidden-import", "ppocr.utils.logging",
        "--hidden-import", "ppocr.utils.utility",
        "--hidden-import", "ppocr.utils.network",
        # Collect all для основных пакетов
        "--collect-all", "paddle",
        "--collect-all", "paddleocr",
        "--collect-all", "ppocr",
        "--collect-all", "paddlex",
        # Другие зависимости
        "--hidden-import", "PIL",
        "--hidden-import", "fitz",  # PyMuPDF
        "--hidden-import", "pptx",  # python-pptx
        "--hidden-import", "tkinter",
        "--hidden-import", "cv2",  # OpenCV (используется PaddleOCR)
        "--collect-all", "PIL",
        "--collect-all", "fitz",
        "--collect-all", "pptx",
        "--collect-all", "cv2",
        "--collect-all", "numpy",
        "--collect-all", "scipy",
        # Скрытые импорты для cv2 и его зависимостей
        "--hidden-import", "cv2.gapi.onnx",
        "--hidden-import", "cv2.gapi.onnx.epie_emulator",
        "--hidden-import", "cv2.gapi.ie",
        "--hidden-import", "cv2.gapi.ocv",
        "--hidden-import", "cv2.gapi.pyr",
        "--hidden-import", "cv2.mat_wrapper",
        "--hidden-import", "cv2.misc",
        "--hidden-import", "cv2.utils",
        "--hidden-import", "cv2.error",
        # Для PIL ImageFormat
        "--hidden-import", "PIL.BmpImagePlugin",
        "--hidden-import", "PIL.GifImagePlugin",
        "--hidden-import", "PIL.JpegImagePlugin",
        "--hidden-import", "PIL.PngImagePlugin",
        "--hidden-import", "PIL.TiffImagePlugin",
        "--hidden-import", "PIL.WebPImagePlugin",
        "--hidden-import", "PIL.FtImagePlugin",
        "--hidden-import", "PIL.ImageDraw",
        "--hidden-import", "PIL.ImageFont",
        "--hidden-import", "PIL.ImageOps",
        # Для tkinter
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.constants",
        # Стандартные библиотеки
        "--hidden-import", "logging",
        "--hidden-import", "threading",
        "--hidden-import", "pathlib",
        "--hidden-import", "tempfile",
        "--hidden-import", "shutil",
        "--hidden-import", "json",
        "--hidden-import", "urllib.request",
        "--hidden-import", "urllib.error",
        "--hidden-import", "zipfile",
        "--hidden-import", "subprocess",
        "--hidden-import", "re",
        "--hidden-import", "math",
        "--hidden-import", "typing",
        "--hidden-import", "collections",
        "--hidden-import", "collections.abc",
        "--hidden-import", "functools",
        "--hidden-import", "itertools",
        "--hidden-import", "platform",
        "--hidden-import", "struct",
        "--hidden-import", "codecs",
        "--hidden-import", "encodings",
        "--hidden-import", "xml",
        "--hidden-import", "xml.etree",
        "--hidden-import", "xml.etree.ElementTree",
        "--hidden-import", "html",
        "--hidden-import", "email",
        "--hidden-import", "base64",
        "--hidden-import", "hashlib",
        "--hidden-import", "hmac",
        "--hidden-import", "ssl",
        "--hidden-import", "socket",
        "--hidden-import", "http",
        "--hidden-import", "http.client",
        "--hidden-import", "copy",
        "--hidden-import", "weakref",
        "--hidden-import", "gc",
        "--hidden-import", "io",
        "--hidden-import", "string",
        "--hidden-import", "datetime",
        "--hidden-import", "time",
        "--hidden-import", "calendar",
        "--hidden-import", "operator",
        "--hidden-import", "contextlib",
        "--hidden-import", "abc",
        "--hidden-import", "warnings",
        "--hidden-import", "traceback",
        "--hidden-import", "linecache",
        "--hidden-import", "tokenize",
        "--hidden-import", "keyword",
        "--hidden-import", "dis",
        "--hidden-import", "pickle",
        "--hidden-import", "_pickle",
        "--hidden-import", "pprint",
        "--hidden-import", "reprlib",
        "--hidden-import", "enum",
        "--hidden-import", "graphlib",
        "--hidden-import", "queue",
        "--hidden-import", "select",
        "--hidden-import", "selectors",
        "--hidden-import", "errno",
        "--hidden-import", "ctypes",
        "--hidden-import", "ctypes.util",
        "--hidden-import", "concurrent",
        "--hidden-import", "concurrent.futures",
        "--hidden-import", "multiprocessing",
        "--hidden-import", "multiprocessing.spawn",
        "--hidden-import", "multiprocessing.popen_spawn_win32",
        "--hidden-import", "pkg_resources",
        "--hidden-import", "setuptools",
        "--hidden-import", "distutils",
        "--hidden-import", "importlib",
        "--hidden-import", "importlib.util",
        "--hidden-import", "importlib.machinery",
        "--hidden-import", "importlib.resources",
        "--hidden-import", "importlib.metadata",
        "--hidden-import", "packaging",
        "--hidden-import", "packaging.version",
        "--hidden-import", "packaging.specifiers",
        "--hidden-import", "yaml",
        "--hidden-import", "ruamel",
        "--hidden-import", "ruamel.yaml",
        "--hidden-import", "attr",
        "--hidden-import", "attrs",
        "--hidden-import", "dataclasses",
        "--hidden-import", "visualdl",
        "--hidden-import", "colorlog",
        "--hidden-import", "lxml",
        "--hidden-import", "fontTools",
        "--hidden-import", "docx",
        "--hidden-import", "docx.opc",
        "--hidden-import", "docx.shared",
        "--hidden-import", "docx.enum",
        # Paddlex pipeline config
        "--hidden-import", "paddlex.inference",
        "--hidden-import", "paddlex.inference.pipelines",
        "--hidden-import", "paddlex.inference.pipelines.ocr",
        "--hidden-import", "paddlex.inference.utils",
        "--hidden-import", "paddlex.utils",
        "--hidden-import", "paddlex.ops",
    ]
    
    # Добавляем данные из пакетов paddleocr, paddlex и ppocr если пути найдены
    if paddleocr_path:
        pyinstaller_cmd.extend([
            "--add-data", f"{paddleocr_path}{os.pathsep}paddleocr",
        ])
    if paddlex_path:
        pyinstaller_cmd.extend([
            "--add-data", f"{paddlex_path}{os.pathsep}paddlex",
        ])
    if ppocr_path:
        pyinstaller_cmd.extend([
            "--add-data", f"{ppocr_path}{os.pathsep}ppocr",
        ])
    
    # Основной файл приложения
    pyinstaller_cmd.append(str(root_dir / "main.py"))
    
    print(f"  Выполняется команда PyInstaller...\n")
    
    # Запуск PyInstaller
    try:
        result = subprocess.run(
            pyinstaller_cmd,
            cwd=root_dir,
            check=True,
            capture_output=False,
        )
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Ошибка при выполнении PyInstaller: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n❌ PyInstaller не найден. Установите: pip install pyinstaller")
        sys.exit(1)
    
    # Проверка результата
    print("\n[4/5] Проверка результата...")
    
    if not output_dir.exists():
        print(f"\n❌ Папка сборки не найдена: {output_dir}")
        sys.exit(1)
    
    exe_path = output_dir / f"{app_name}.exe"
    if not exe_path.exists():
        print(f"\n❌ EXE файл не найден: {exe_path}")
        sys.exit(1)
    
    print(f"  ✅ Сборка успешно создана!")
    print(f"  Путь: {output_dir}")
    print(f"  EXE: {exe_path}")
    
    # Информация о размере
    total_size = sum(
        f.stat().st_size 
        for f in output_dir.rglob("*") 
        if f.is_file()
    )
    size_mb = total_size / (1024 * 1024)
    print(f"  Размер сборки: {size_mb:.2f} MB")
    
    # Инструкция
    print("\n[5/5] Инструкция по использованию:")
    print("-" * 60)
    print(f"""
Готовая сборка находится в папке:
  {output_dir}

Для распространения можно:
1. Запаковать папку {app_name}/ в ZIP-архив
2. Или создать установщик с помощью Inno Setup/NSIS

Важно:
- При первом запуске PaddleOCR автоматически загрузит необходимые модели
- Модели будут сохранены в %USERPROFILE%\\paddleocr
- Для работы требуется подключение к интернету при первом запуске
- После загрузки моделей приложение может работать офлайн

Запуск:
  Дважды кликните на {app_name}.exe
  Или из командной строки: {app_name}\\{app_name}.exe
""")
    print("-" * 60)
    print("\n✅ Сборка завершена успешно!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
