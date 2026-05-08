"""
PyInstaller hook для paddlex.utils.deps.
Отключает проверку зависимостей в frozen-режиме.
"""

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('paddlex.utils.deps')

# Добавляем все возможные зависимости, которые могут проверяться
hiddenimports.extend([
    'paddle',
    'paddleocr',
    'ppocr',
    'cv2',
    'numpy',
    'scipy',
    'PIL',
    'fitz',
    'pptx',
    'yaml',
    'ruamel.yaml',
    'lxml',
    'fontTools',
    'visualdl',
    'colorlog',
    'attr',
    'attrs',
    'shapely',
    'lmdb',
    'imgaug',
    'pyclipper',
    'openpyxl',
    'xlsxwriter',
    'tables',
    'pdf2image',
    'lap',
    'motmetrics',
    'filterpy',
    'scikit-image',
])

print(f"Hook paddlex.utils.deps: loaded {len(hiddenimports)} hidden imports")
