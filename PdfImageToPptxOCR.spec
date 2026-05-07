# -*- mode: python ; coding: utf-8 -*-
import os
import glob as glob_module
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files
from PyInstaller.utils.hooks import copy_metadata

# ============================================================
# 1. Сборка основных ресурсов и метаданных (Улучшенный и безопасный)
# ============================================================
datas = []
binaries = []
hiddenimports = [
    'scipy._cyutility', 'scipy', 'scipy.ndimage', 'scipy.ndimage.filters',
    'scipy.ndimage.morphology', 'scipy.ndimage.interpolation', 'numpy', 
    # OpenCV и другие библиотеки, которые должны быть в hiddenimports
]

PACKAGES_TO_COLLECT = [
    'paddlepaddle', 'pyclipper', 'shapely', 'scipy',
    'paddleocr', 'paddlex', 'PyMuPDF', 'python-pptx', 'Pillow'
]

# Функция для безопасного добавления ресурсов в datas/binaries
def safe_append(target_list, item):
    if isinstance(item, tuple) and len(item) == 2:
        target_list.append(item)
    else:
        print(f"[SPEC WARN] Skipping invalid resource format: {item}")

# Метаданные пакетов (Осторожно с copy_metadata!)
print("[SPEC] Collecting metadata for core packages...")
for pkg in PACKAGES_TO_COLLECT:
    try:
        meta = copy_metadata(pkg, recursive=True)
        datas.extend([tuple(item) for item in meta]) # Приводим всё к формату tuple (source, dest)
    except Exception as e:
        print(f"[SPEC WARN] Could not collect metadata for {pkg}: {e}")

# Общий сбор всех модулей и бинарников (Сборка должна быть в формате 2-элементного кортежа)
for pkg in ['paddle', 'paddleocr', 'paddlex']:
    try:
        tmp_ret = collect_all(pkg)
        # Убеждаемся, что каждый элемент — это tuple из двух элементов (path, dest)
        for item in tmp_ret[0]: safe_append(datas, item) 
        for item in tmp_ret[1]: safe_append(binaries, item)
        hiddenimports.extend(tmp_ret[2])
    except Exception as e:
        print(f"[SPEC WARN] Failed to collect submodules for {pkg}: {e}")

# ============================================================
# 2. PaddlePaddle DLLs (Сохранена логика, но улучшена безопасность)
# ============================================================
try:
    import paddle
    paddle_pkg_path = os.path.dirname(paddle.__file__)
    print("[SPEC] Collecting native paddle libraries...")

    # Вариант 1: папка paddle.libs рядом с paddle (Добавляем в binaries)
    paddle_libs_dir = os.path.join(os.path.dirname(paddle_pkg_path), 'paddle.libs')
    if os.path.isdir(paddle_libs_dir):
        for f in os.listdir(paddle_libs_dir):
            full = os.path.join(paddle_libs_dir, f)
            binaries.append((full, '.'))

    # Вариант 2: libs внутри paddle/fluid/ (Добавляем в binaries)
    fluid_libs = os.path.join(paddle_pkg_path, 'fluid', 'libs')
    if os.path.isdir(fluid_libs):
        for f in os.listdir(fluid_libs):
            full = os.path.join(fluid_libs, f)
            binaries.append((full, 'paddle/fluid/libs'))

    # Вариант 3: все .dll / .pyd из директории paddle (Добавляем в binaries)
    for root, dirs, files in os.walk(paddle_pkg_path):
        for f in files:
            if f.endswith(('.dll', '.pyd')):
                rel = os.path.relpath(root, paddle_pkg_path)
                dest = os.path.join('paddle', rel) if rel != '.' else 'paddle'
                binaries.append((os.path.join(root, f), dest))

except Exception as e:
    print(f"[SPEC WARN] Could not collect native paddle binaries: {e}")


# ============================================================
# 3. OpenCV (cv2) binaries
# ============================================================
try:
    tmp_ret = collect_all('cv2')
    datas.extend([tuple(item) for item in tmp_ret[0]]) # Используем safe_append для данных
    binaries.extend([tuple(item) for item in tmp_ret[1]]) # Используем safe_append для бинарников
    hiddenimports.extend(tmp_ret[2])
except Exception as e:
    print(f"[SPEC WARN] Could not collect CV2 modules/binaries: {e}")


# ============================================================
# 4. Модели PaddleOCR / PaddleX (скачанные заранее) - Логика остается
# ============================================================
import pathlib

model_dirs_to_bundle = []
home = pathlib.Path.home()

possible_model_paths = [
    home / '.paddlex' / 'official_models',
    home / '.paddlex' / 'hub',
    home / '.paddlex' / 'models',
    home / '.cache' / 'paddlex',
    home / '.paddleocr',
    home / '.cache' / 'paddleocr',
]

print("[SPEC] Searching for model directories to bundle...")
for p in possible_model_paths:
    if p.exists() and p.is_dir():
        model_dirs_to_bundle.append(str(p))

# Сборка моделей (Логика остается, так как это не влияет на формат кортежей)
for model_dir in model_dirs_to_bundle:
    base_name = os.path.basename(model_dir)
    parent_name = os.path.basename(os.path.dirname(model_dir))
    dest = os.path.join('_models', parent_name, base_name)
    datas.append((model_dir, dest))
    print(f"[SPEC] Bundling models from: {model_dir} -> {dest}")

# ============================================================
# 5. Runtime hook: PATH для DLL и путь к моделям (Оставлено без изменений)
# ============================================================
runtime_hook_code = r'''
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
'''

runtime_hook_path = os.path.join(os.getcwd(), '_runtime_hook_paddle.py')
with open(runtime_hook_path, 'w', encoding='utf-8') as f:
    f.write(runtime_hook_code)

# ============================================================
# 6. Analysis (Это ядро PyInstaller)
# ============================================================
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas, # Теперь datas гарантированно содержит только кортежи (source, dest)
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[runtime_hook_path],
    excludes=['matplotlib', 'pyqt5', 'pyqt6', 'pyside2', 'pyside6', 'wx', 'gtk', 'tensorflow', 'torch'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PdfImageToPptxOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PdfImageToPptxOCR',
)