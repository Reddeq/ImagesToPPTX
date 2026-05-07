# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file для создания portable билда на Windows
Python 3.11 + PaddlePaddle + OpenCV + PaddleOCR
"""
import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files, get_package_paths
from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.compat import is_win

# ============================================================
# 1. Инициализация коллекций
# ============================================================
datas = []
binaries = []
hiddenimports = []

# ============================================================
# 2. Helper функции
# ============================================================
def safe_append_datas(target_list, item):
    """Безопасное добавление в datas с проверкой формата"""
    if isinstance(item, (list, tuple)) and len(item) == 2:
        target_list.append((str(item[0]), str(item[1])))
    else:
        print(f"[SPEC WARN] Skipping invalid datas format: {item}")

def safe_append_binaries(target_list, item):
    """Безопасное добавление в binaries с проверкой формата"""
    if isinstance(item, (list, tuple)) and len(item) == 2:
        target_list.append((str(item[0]), str(item[1])))
    else:
        print(f"[SPEC WARN] Skipping invalid binaries format: {item}")

def collect_package_full(package_name):
    """Полный сбор пакета: данные, бинарники, hiddenimports"""
    global datas, binaries, hiddenimports
    try:
        print(f"[SPEC] Collecting package: {package_name}")
        tmp_ret = collect_all(package_name)
        for item in tmp_ret[0]:
            safe_append_datas(datas, item)
        for item in tmp_ret[1]:
            safe_append_binaries(binaries, item)
        hiddenimports.extend(tmp_ret[2])
        print(f"[SPEC OK] Collected {package_name}")
    except Exception as e:
        print(f"[SPEC WARN] Failed to collect {package_name}: {e}")

# ============================================================
# 3. Сбор основных пакетов
# ============================================================
PACKAGES_TO_COLLECT = [
    'paddle',
    'paddleocr', 
    'paddlex',
    'cv2',
    'fitz',  # PyMuPDF
    'pptx',  # python-pptx
    'PIL',   # Pillow
    'scipy',
    'numpy',
    'pyclipper',
    'shapely',
    'yaml',
    'tqdm',
    'requests',
    'lxml',
]

for pkg in PACKAGES_TO_COLLECT:
    collect_package_full(pkg)

# ============================================================
# 4. Дополнительные hiddenimports для Paddle и OpenCV
# ============================================================
extra_hiddenimports = [
    # PaddlePaddle
    'paddle',
    'paddle.fluid',
    'paddle.inference',
    'paddle.base',
    'paddle.nn',
    'paddle.optimizer',
    'paddle.distribution',
    'paddle.vision',
    'paddle.io',
    'paddle.static',
    'paddle.autograd',
    'paddle.jit',
    'paddle.sysconfig',
    
    # PaddleOCR
    'paddleocr',
    'paddleocr.paddleocr',
    'paddleocr.tools.infer',
    'paddleocr.tools.infer.predict_system',
    'paddleocr.tools.infer.predict_det',
    'paddleocr.tools.infer.predict_rec',
    'paddleocr.tools.infer.predict_cls',
    'paddleocr.ppocr.utility',
    'paddleocr.ppocr.postprocess',
    'paddleocr.ppocr.data',
    
    # PaddleX
    'paddlex',
    'paddlex.cv',
    'paddlex.cv.transforms',
    'paddlex.cv.models',
    'paddlex.det',
    'paddlex.seg',
    
    # OpenCV
    'cv2',
    'cv2.error',
    'cv2.mat_wrapper',
    'cv2.misc',
    'cv2.umatmat',
    'cv2.gapi.cpu',
    'cv2.gapi.ocl',
    'cv2.gapi.onnx',
    'cv2.gapi.streaming',
    'cv2.gapi.wip.draw',
    
    # SciPy
    'scipy',
    'scipy.ndimage',
    'scipy.ndimage.filters',
    'scipy.ndimage.morphology',
    'scipy.ndimage.interpolation',
    'scipy.special',
    'scipy.linalg',
    'scipy.interpolate',
    'scipy.sparse',
    'scipy._lib',
    'scipy._lib.messagestream',
    
    # Другие
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'fitz',
    'pptx',
    'yaml',
    'queue',
    'multiprocessing',
    'concurrent.futures',
    'encoding',
    'encodings.utf_8',
    'encodings.cp1252',
    'encodings.cp437',
]

hiddenimports.extend(extra_hiddenimports)
# Удаляем дубликаты
hiddenimports = list(set(hiddenimports))

# ============================================================
# 5. Сбор бинарных файлов PaddlePaddle (Windows DLL)
# ============================================================
try:
    import paddle
    paddle_pkg_path = os.path.dirname(paddle.__file__)
    print(f"[SPEC] Paddle package path: {paddle_pkg_path}")
    
    # paddle.libs (отдельная папка с DLL)
    paddle_libs_candidates = [
        os.path.join(os.path.dirname(paddle_pkg_path), 'paddle.libs'),
        os.path.join(paddle_pkg_path, 'libs'),
        os.path.join(paddle_pkg_path, 'paddle', 'libs'),
    ]
    
    for libs_dir in paddle_libs_candidates:
        if os.path.isdir(libs_dir):
            print(f"[SPEC] Found paddle libs at: {libs_dir}")
            for f in os.listdir(libs_dir):
                if f.endswith(('.dll', '.pyd', '.so')):
                    full_path = os.path.join(libs_dir, f)
                    binaries.append((full_path, '.'))
    
    # DLL внутри paddle/fluid/
    fluid_paths = [
        os.path.join(paddle_pkg_path, 'fluid'),
        os.path.join(paddle_pkg_path, 'paddle', 'fluid'),
    ]
    for fluid_dir in fluid_paths:
        if os.path.isdir(fluid_dir):
            for root, dirs, files in os.walk(fluid_dir):
                for f in files:
                    if f.endswith(('.dll', '.pyd', '.so')):
                        full_path = os.path.join(root, f)
                        rel_path = os.path.relpath(root, paddle_pkg_path)
                        dest_dir = os.path.join('paddle', rel_path)
                        binaries.append((full_path, dest_dir))
    
    # Все .dll/.pyd внутри paddle
    for root, dirs, files in os.walk(paddle_pkg_path):
        for f in files:
            if f.endswith(('.dll', '.pyd', '.so')):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(root, paddle_pkg_path)
                dest_dir = os.path.join('paddle', rel_path) if rel_path != '.' else 'paddle'
                binaries.append((full_path, dest_dir))
                
    print("[SPEC OK] Collected Paddle binaries")
except ImportError:
    print("[SPEC WARN] Paddle not installed, skipping paddle binaries collection")
except Exception as e:
    print(f"[SPEC WARN] Error collecting paddle binaries: {e}")

# ============================================================
# 6. Сбор бинарных файлов OpenCV (Windows DLL)
# ============================================================
try:
    import cv2
    cv2_pkg_path = os.path.dirname(cv2.__file__)
    print(f"[SPEC] OpenCV package path: {cv2_pkg_path}")
    
    # cv2.libs (отдельная папка с DLL в новых версиях opencv-python)
    cv2_libs_dir = os.path.join(os.path.dirname(cv2_pkg_path), 'cv2.libs')
    if os.path.isdir(cv2_libs_dir):
        print(f"[SPEC] Found cv2.libs at: {cv2_libs_dir}")
        for f in os.listdir(cv2_libs_dir):
            if f.endswith(('.dll', '.pyd', '.so')):
                full_path = os.path.join(cv2_libs_dir, f)
                binaries.append((full_path, '.'))
    
    # DLL внутри самой папки cv2
    for root, dirs, files in os.walk(cv2_pkg_path):
        for f in files:
            if f.endswith(('.dll', '.pyd', '.so')):
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(root, cv2_pkg_path)
                dest_dir = os.path.join('cv2', rel_path) if rel_path != '.' else 'cv2'
                binaries.append((full_path, dest_dir))
    
    # data файлы cv2
    cv2_data_dir = os.path.join(cv2_pkg_path, 'data')
    if os.path.isdir(cv2_data_dir):
        for root, dirs, files in os.walk(cv2_data_dir):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, cv2_pkg_path)
                dest_path = os.path.join('cv2', rel_path)
                datas.append((full_path, dest_path))
    
    print("[SPEC OK] Collected OpenCV binaries")
except ImportError:
    print("[SPEC WARN] OpenCV not installed, skipping cv2 binaries collection")
except Exception as e:
    print(f"[SPEC WARN] Error collecting OpenCV binaries: {e}")

# ============================================================
# 7. Метаданные пакетов (для зависимостей)
# ============================================================
METADATA_PACKAGES = [
    'paddlepaddle', 'paddle', 'paddleocr', 'paddlex',
    'opencv_python', 'opencv-python', 'cv2',
    'PyMuPDF', 'fitz', 'python_pptx', 'python-pptx',
    'Pillow', 'PIL', 'scipy', 'numpy', 'pyclipper', 'shapely'
]

print("[SPEC] Collecting metadata...")
for pkg in METADATA_PACKAGES:
    try:
        meta = copy_metadata(pkg, recursive=False)
        for item in meta:
            safe_append_datas(datas, item)
    except Exception as e:
        pass  # Тихо игнорируем отсутствующие метаданные

# ============================================================
# 8. Модели PaddleOCR / PaddleX (опционально)
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
        # Проверяем размер директории (не добавляем слишком большие)
        total_size = sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
        if total_size < 2 * 1024 * 1024 * 1024:  # Максимум 2GB
            model_dirs_to_bundle.append(str(p))
            print(f"[SPEC] Found model dir: {p} ({total_size / 1024 / 1024:.1f} MB)")
        else:
            print(f"[SPEC SKIP] Model dir too large: {p} ({total_size / 1024 / 1024:.1f} MB)")

for model_dir in model_dirs_to_bundle:
    base_name = os.path.basename(model_dir)
    parent_name = os.path.basename(os.path.dirname(model_dir))
    dest = os.path.join('_models', parent_name, base_name)
    datas.append((model_dir, dest))
    print(f"[SPEC] Bundling models: {model_dir} -> {dest}")

# ============================================================
# 9. Runtime hook для Windows
# ============================================================
runtime_hook_code = r'''
import os
import sys
import pathlib

if getattr(sys, 'frozen', False):
    # Директория запускаемого файла
    exe_dir = os.path.dirname(sys.executable)
    
    # Добавляем exe_dir в PATH для поиска DLL
    os.environ['PATH'] = exe_dir + os.pathsep + os.environ.get('PATH', '')
    
    # Определяем базовую директорию
    if hasattr(sys, '_MEIPASS'):
        base_dir = pathlib.Path(sys._MEIPASS)
    else:
        base_dir = pathlib.Path(exe_dir)
    
    # Проверяем _internal для portable режима
    internal_dir = None
    if os.path.isdir(os.path.join(exe_dir, '_internal')):
        internal_dir = os.path.join(exe_dir, '_internal')
    elif os.path.isdir(os.path.join(exe_dir, 'PdfImageToPptxOCR_files')):
        internal_dir = os.path.join(exe_dir, 'PdfImageToPptxOCR_files')
    
    if internal_dir:
        models_dir = os.path.join(internal_dir, '_models')
    else:
        models_dir = os.path.join(str(base_dir), '_models')
    
    if os.path.isdir(models_dir):
        os.environ['PADDLEX_MODEL_PATH'] = models_dir
        os.environ['PADDLEOCR_MODEL_PATH'] = models_dir
    
    # Переменные окружения для Paddle
    os.environ['FLAGS_use_pir'] = '0'
    os.environ['FLAGS_use_mkldnn'] = '0'
'''

runtime_hook_path = os.path.join(os.getcwd(), '_runtime_hook_paddle.py')
with open(runtime_hook_path, 'w', encoding='utf-8') as f:
    f.write(runtime_hook_code)
print(f"[SPEC] Created runtime hook: {runtime_hook_path}")

# ============================================================
# 10. Исключения (уменьшаем размер билда)
# ============================================================
excludes = [
    'matplotlib', 'pyqt5', 'pyqt6', 'PySide2', 'PySide6',
    'wx', 'gtk', 'gi', 'tkinter.test', 'test', 'unittest',
    'tensorflow', 'torch', 'keras', 'onnx', 'tensorrt',
    'doc', 'docs', 'tests', 'examples', 'demos',
    'distutils', 'setuptools', 'pip',
]

# ============================================================
# 11. UPX исключения (важные DLL не сжимать)
# ============================================================
upx_exclude = [
    'paddle', 'paddle.fluid', 'paddle.libs',
    'cv2', 'cv2.libs',
    'mklml', 'mkldnn', 'cudnn',
    '.dll', '.pyd',
]

# ============================================================
# 12. Analysis
# ============================================================
print(f"[SPEC] Starting Analysis...")
print(f"[SPEC] Total datas: {len(datas)}")
print(f"[SPEC] Total binaries: {len(binaries)}")
print(f"[SPEC] Total hiddenimports: {len(hiddenimports)}")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[runtime_hook_path],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ============================================================
# 13. EXE (портативный однофайловый режим)
# ============================================================
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PdfImageToPptxOCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=upx_exclude,
    console=True,  # True для отладки, можно поставить False для GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Для folder-режима (portable папка) раскомментируйте COLLECT ниже
# и закомментируйте EXE выше (переместив a.binaries, a.datas в COLLECT)

# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=upx_exclude,
#     name='PdfImageToPptxOCR',
# )