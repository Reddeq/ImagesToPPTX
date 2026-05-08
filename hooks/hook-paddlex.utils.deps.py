"""
PyInstaller hook для paddlex.utils.deps.
Отключает проверку зависимостей в frozen-режиме путем подмены функции require_extra.
Этот хук выполняется ВО ВРЕМЯ РАБОТЫ собранного приложения (runtime).
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
    'pypdfium2',
    'pypdfium2_raw',
])

print(f"Hook paddlex.utils.deps: loaded {len(hiddenimports)} hidden imports")

# Runtime hook - код который будет выполнен в собранном приложении
def _patch_paddlex_deps_at_runtime():
    """
    Подменяет функцию require_extra в paddlex.utils.deps на заглушку.
    Это позволяет избежать ошибки DependencyError в собранном приложении.
    """
    import sys
    
    # Проверяем, запущены ли мы в frozen режиме
    if not getattr(sys, 'frozen', False):
        return
    
    try:
        import paddlex.utils.deps as deps_module
        
        # Сохраняем оригинальную функцию (на всякий случай)
        if not hasattr(deps_module, '_original_require_extra'):
            deps_module._original_require_extra = deps_module.require_extra
        
        # Создаем заглушку
        def _dummy_require_extra(extra, obj_name=None, alt=None):
            # Просто возвращаем ничего, не проверяя зависимости
            pass
        
        # Подменяем функцию
        deps_module.require_extra = _dummy_require_extra
        
        print("Runtime hook: PADDLEX dependency check disabled")
        
    except ImportError as e:
        print(f"Runtime hook: could not patch paddlex.utils.deps: {e}")
    except Exception as e:
        print(f"Runtime hook: error patching paddlex.utils.deps: {e}")

# Выполняем патчинг при импорте этого модуля в runtime
_patch_paddlex_deps_at_runtime()
