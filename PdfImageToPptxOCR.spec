# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file для создания portable onefolder билда на Windows
Python 3.11 + PaddlePaddle + OpenCV + PaddleOCR
"""
import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files, get_package_paths
from PyInstaller.utils.hooks import copy_metadata
from PyInstaller.compat import is_win
from PyInstaller.building.build_main import Analysis, PYZ, COLLECT

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

def collect_package_safe(package_name):
    """Сбор пакета с обработкой ошибок импорта"""
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
    'fitz',
    'pptx',
    'PIL',
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
    collect_package_safe(pkg)

# ============================================================
# 4. Дополнительные hiddenimports для Paddle и OpenCV
# ============================================================
extra_hiddenimports = [
    # PaddlePaddle core
    'paddle',
    'paddle.fluid',
    'paddle.inference',
    'paddle.base',
    'paddle.base.libpaddle',
    'paddle.nn',
    'paddle.optimizer',
    'paddle.distribution',
    'paddle.vision',
    'paddle.io',
    'paddle.static',
    'paddle.autograd',
    'paddle.jit',
    'paddle.sysconfig',
    'paddle.utils',
    'paddle.utils.cpp_extension',
    'paddle_amp',
    'paddle_batch_norm',
    'paddle_conv',
    'paddle_nn',
    'paddle_pooling',
    'paddle_rnn',
    
    # PaddleOCR - основные модули
    'paddleocr',
    'paddleocr.paddleocr',
    'paddleocr.tools',
    'paddleocr.tools.infer',
    'paddleocr.tools.infer.predict_system',
    'paddleocr.tools.infer.predict_det',
    'paddleocr.tools.infer.predict_rec',
    'paddleocr.tools.infer.predict_cls',
    'paddleocr.ppocr',
    'paddleocr.ppocr.utility',
    'paddleocr.ppocr.postprocess',
    'paddleocr.ppocr.data',
    'paddleocr.ppocr.utils',
    'paddleocr.ppocr.utils.logging',
    'paddleocr.ppocr.utils.utility',
    'paddleocr.ppocr.utils.i18n',
    'paddleocr.ppocr.utils.network',
    'paddleocr.ppocr.utils.visual',
    'paddleocr.ppocr.utils.dict90',
    'paddleocr.ppocr.utils.en_dict',
    'paddleocr.ppocr.utils.ic15_dict',
    'paddleocr.ppocr.utils.ka_dict',
    'paddleocr.ppocr.utils.korean_dict',
    'paddleocr.ppocr.utils.lang_dict',
    'paddleocr.ppocr.utils.ocriqa_dict',
    'paddleocr.ppocr.utils.ru_dict',
    'paddleocr.ppocr.utils.table_dict',
    'paddleocr.ppocr.utils.text_detector',
    'paddleocr.ppocr.utils.text_recognizer',
    'paddleocr.ppocr.utils.utility',
    
    # PaddleX
    'paddlex',
    'paddlex.cv',
    'paddlex.cv.transforms',
    'paddlex.cv.models',
    'paddlex.det',
    'paddlex.seg',
    'paddlex.cls',
    'paddlex.rec',
    'paddlex.inference',
    'paddlex.inference.models',
    'paddlex.inference.models.base',
    'paddlex.inference.models.classifier',
    'paddlex.inference.models.detector',
    'paddlex.inference.models.segmentor',
    'paddlex.utils',
    'paddlex.utils.deps',
    'paddlex.utils.logger',
    'paddlex.utils.version',
    
    # OpenCV
    'cv2',
    'cv2.error',
    'cv2.mat_wrapper',
    'cv2.misc',
    'cv2.umatmat',
    'cv2.gapi',
    'cv2.gapi.cpu',
    'cv2.gapi.ocl',
    'cv2.gapi.onnx',
    'cv2.gapi.streaming',
    'cv2.gapi.wip.draw',
    'cv2.gapi.core',
    'cv2.gapi.imgproc',
    'cv2.gapi.fluid',
    'cv2.gapi.own',
    'cv2.gapi.render',
    'cv2.gapi.video',
    'cv2.dnn',
    'cv2.ml',
    'cv2.ogl',
    'cv2.cuda',
    
    # SciPy - исправленные импорты
    'scipy',
    'scipy.ndimage',
    'scipy.ndimage._filters',
    'scipy.ndimage._morphology',
    'scipy.ndimage._interpolation',
    'scipy.ndimage._measurements',
    'scipy.special',
    'scipy.linalg',
    'scipy.interpolate',
    'scipy.sparse',
    'scipy._lib',
    'scipy._lib.messagestream',
    'scipy._lib._util',
    'scipy._lib._ccallback',
    'scipy._lib._ccallback_c',
    'scipy._lib.decorator',
    'scipy.spatial',
    'scipy.spatial.transform',
    'scipy.integrate',
    'scipy.optimize',
    'scipy.stats',
    
    # PIL/Pillow
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL._imaging',
    'PIL._imagingft',
    'PIL._typing',
    'PIL.features',
    'PIL._deprecate',
    
    # PyMuPDF
    'fitz',
    'fitz.fitz',
    'fitz.utils',
    
    # python-pptx
    'pptx',
    'pptx.opc',
    'pptx.oxml',
    'pptx.util',
    'pptx.exc',
    'pptx.enum',
    'pptx.parts',
    'pptx.shapes',
    'pptx.slide',
    'pptx.text',
    'pptx.chart',
    'pptx.table',
    
    # YAML
    'yaml',
    'yaml.loader',
    'yaml.dumper',
    'yaml.resolver',
    'yaml.representer',
    'yaml.constructor',
    'yaml.reader',
    'yaml.scanner',
    'yaml.parser',
    'yaml.composer',
    'yaml.serializer',
    'yaml.emitter',
    
    # Стандартные библиотеки
    'queue',
    'multiprocessing',
    'multiprocessing.pool',
    'multiprocessing.dummy',
    'concurrent.futures',
    'concurrent.futures.thread',
    'concurrent.futures.process',
    'threading',
    'subprocess',
    'tempfile',
    'shutil',
    'platform',
    'ctypes',
    'ctypes.util',
    'logging',
    'logging.config',
    'json',
    'pickle',
    'copy',
    'io',
    'os',
    'sys',
    'pathlib',
    're',
    'collections',
    'collections.abc',
    'functools',
    'itertools',
    'operator',
    'warnings',
    'traceback',
    'struct',
    'array',
    'mmap',
    'select',
    'socket',
    'ssl',
    'http',
    'http.client',
    'urllib',
    'urllib.request',
    'urllib.parse',
    'email',
    'email.mime',
    'email.mime.text',
    'email.mime.multipart',
    'email.mime.image',
    'base64',
    'hashlib',
    'hmac',
    'secrets',
    'uuid',
    'datetime',
    'time',
    'calendar',
    'locale',
    'gettext',
    'getpass',
    'curses',
    'unicodedata',
    'stringprep',
    'rlcompleter',
    'csv',
    'configparser',
    'argparse',
    'optparse',
    'textwrap',
    'difflib',
    'pprint',
    'reprlib',
    'enum',
    'graphlib',
    'contextlib',
    'abc',
    'atexit',
    'weakref',
    'gc',
    'inspect',
    'dis',
    'ast',
    'token',
    'keyword',
    'tokenize',
    'tabnanny',
    'pyclbr',
    'compileall',
    'py_compile',
    'formatter',
    'pdb',
    'profile',
    'timeit',
    'trace',
    'tracemalloc',
    'distutils',
    'ensurepip',
    'venv',
    'zipapp',
    'zipfile',
    'tarfile',
    'gzip',
    'bz2',
    'lzma',
    'zlib',
    'codecs',
    'encodings',
    'encodings.utf_8',
    'encodings.cp1251',
    'encodings.cp1252',
    'encodings.cp437',
    'encodings.latin_1',
    'encodings.ascii',
    'encodings.mbcs',
    'encodings.charmap',
]

hiddenimports.extend(extra_hiddenimports)
# Удаляем дубликаты
hiddenimports = list(dict.fromkeys(hiddenimports))

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
# Runtime hook теперь хранится в отдельном файле _runtime_hook_paddle.py
# Используем sys.argv[0] или os.getcwd() вместо __file__, т.к. __file__ не определен в spec
import sys
if getattr(sys, 'frozen', False):
    # Запущен как скомпилированный exe
    script_dir = os.path.dirname(sys.executable)
else:
    # Запущен как скрипт
    script_dir = os.getcwd()

runtime_hook_path = os.path.join(script_dir, '_runtime_hook_paddle.py')
print(f"[SPEC] Using runtime hook: {runtime_hook_path}")

# Добавляем hookspath для кастомных хуков
hookspath = [script_dir]

# Путь к директории проекта для pathex
pathex = [script_dir]

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
    pathex=pathex,
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=hookspath,
    hooksconfig={},
    runtime_hooks=[runtime_hook_path],
    excludes=excludes,
    # noarchive=True для onedir сбилда - распаковывает все файлы в _internal
    noarchive=True,
    optimize=0,
)

pyz = PYZ(a.pure)

# ============================================================
# 13. COLLECT (портативный onedir режим - папка с exe и _internal)
# ============================================================
coll = COLLECT(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    strip=False,
    upx=True,
    upx_exclude=upx_exclude,
    name='PdfImageToPptxOCR',
    # onedir=True создаёт структуру: PdfImageToPptxOCR/PdfImageToPptxOCR.exe + _internal/
    onedir=True,
)