"""
PyInstaller hook для ppocr с поддержкой всех зависимостей.
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Собираем все данные и зависимости из ppocr
datas, binaries, hiddenimports = collect_all('ppocr')

# Явно добавляем все подмодули
hiddenimports += collect_submodules('ppocr.data')
hiddenimports += collect_submodules('ppocr.data.imaug')
hiddenimports += collect_submodules('ppocr.modeling')
hiddenimports += collect_submodules('ppocr.modeling.architectures')
hiddenimports += collect_submodules('ppocr.modeling.backbones')
hiddenimports += collect_submodules('ppocr.modeling.heads')
hiddenimports += collect_submodules('ppocr.modeling.necks')
hiddenimports += collect_submodules('ppocr.postprocess')
hiddenimports += collect_submodules('ppocr.utils')
hiddenimports += collect_submodules('ppocr.utils.logging')
hiddenimports += collect_submodules('ppocr.utils.utility')
hiddenimports += collect_submodules('ppocr.utils.network')

print(f"Hook ppocr: loaded {len(hiddenimports)} hidden imports")
