"""
PyInstaller hook для paddleocr с поддержкой всех зависимостей.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Собираем все данные и зависимости из paddleocr
datas, binaries, hiddenimports = collect_all('paddleocr')

# Явно добавляем все подмодули ppocr
hiddenimports += collect_submodules('ppocr')
hiddenimports += collect_submodules('ppocr.data')
hiddenimports += collect_submodules('ppocr.data.imaug')
hiddenimports += collect_submodules('ppocr.modeling')
hiddenimports += collect_submodules('ppocr.modeling.architectures')
hiddenimports += collect_submodules('ppocr.modeling.backbones')
hiddenimports += collect_submodules('ppocr.modeling.heads')
hiddenimports += collect_submodules('ppocr.modeling.necks')
hiddenimports += collect_submodules('ppocr.postprocess')
hiddenimports += collect_submodules('ppocr.utils')

print(f"Hook paddleocr: loaded {len(hiddenimports)} hidden imports")
