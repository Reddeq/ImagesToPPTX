"""
PyInstaller hook для paddlex с поддержкой OCR.
Включает все необходимые зависимости для работы OCR пайплайна.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Собираем все данные и зависимости из paddlex
datas, binaries, hiddenimports = collect_all('paddlex')

# Явно добавляем все подмодули paddlex.inference.pipelines
hiddenimports += collect_submodules('paddlex.inference.pipelines')
hiddenimports += collect_submodules('paddlex.inference.utils')
hiddenimports += collect_submodules('paddlex.ops')
hiddenimports += collect_submodules('paddlex.utils')

# Зависимости для OCR пайплайна
ocr_hiddenimports = [
    # PaddlePaddle
    'paddle',
    'paddle.nn',
    'paddle.nn.layer',
    'paddle.nn.layer.common',
    'paddle.nn.layer.activation',
    'paddle.nn.layer.conv',
    'paddle.nn.layer.pooling',
    'paddle.nn.layer.norm',
    'paddle.nn.layer.rnn',
    'paddle.nn.layer.transformer',
    'paddle.optimizer',
    'paddle.optimizer.lr',
    'paddle.distribution',
    'paddle.fluid',
    'paddle.inference',
    'paddle.base',
    'paddle.base.framework',
    'paddle.base.core',
    'paddle.autograd',
    'paddle.baseline',
    
    # PaddleOCR
    'paddleocr',
    'ppocr',
    'ppocr.data',
    'ppocr.data.imaug',
    'ppocr.modeling',
    'ppocr.modeling.architectures',
    'ppocr.modeling.backbones',
    'ppocr.modeling.heads',
    'ppocr.modeling.necks',
    'ppocr.postprocess',
    'ppocr.utils',
    'ppocr.utils.logging',
    'ppocr.utils.utility',
    'ppocr.utils.network',
    
    # VisualDL и логирование
    'visualdl',
    'colorlog',
    
    # YAML конфигурации
    'yaml',
    'ruamel.yaml',
    'ruamel',
    
    # Атрибуты и dataclasses
    'attr',
    'attrs',
    'dataclasses',
    
    # Обработка XML и файлов
    'lxml',
    'fontTools',
    'fonttools',
    
    # OpenCV
    'cv2',
    'cv2.gapi.onnx',
    'cv2.gapi.onnx.epie_emulator',
    'cv2.gapi.ie',
    'cv2.gapi.ocv',
    'cv2.gapi.pyr',
    'cv2.mat_wrapper',
    'cv2.misc',
    'cv2.utils',
    'cv2.error',
    
    # Научные библиотеки
    'numpy',
    'scipy',
    'scikit-image',
    'skimage',
    
    # Обработка изображений
    'imgaug',
    'lmdb',
    'shapely',
    'pyclipper',
    
    # Таблицы и PDF
    'openpyxl',
    'xlsxwriter',
    'tables',
    'pdf2image',
    'fitz',
    'pypdfium2',
    'pypdfium2_raw',
    
    # Трекинг (для некоторых моделей)
    'lap',
    'motmetrics',
    'filterpy',
    
    # PIL
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageOps',
    'PIL.BmpImagePlugin',
    'PIL.GifImagePlugin',
    'PIL.JpegImagePlugin',
    'PIL.PngImagePlugin',
    'PIL.TiffImagePlugin',
    'PIL.WebPImagePlugin',
    'PIL.FtImagePlugin',
]

hiddenimports.extend(ocr_hiddenimports)

# Добавляем все данные из paddlex
try:
    import paddlex
    from pathlib import Path
    paddlex_path = Path(paddlex.__file__).parent
    
    # Собираем все конфиги пайплайнов
    pipelines_dir = paddlex_path / "inference" / "pipelines"
    if pipelines_dir.exists():
        datas.append((str(pipelines_dir), "paddlex/inference/pipelines"))
    
    # Собираем все модели и конфиги
    for subdir in ["official_models", "hub", "models", "configs"]:
        model_dir = paddlex_path / subdir
        if model_dir.exists():
            datas.append((str(model_dir), f"paddlex/{subdir}"))
            
except ImportError:
    pass

print(f"Hook paddlex: loaded {len(hiddenimports)} hidden imports")
