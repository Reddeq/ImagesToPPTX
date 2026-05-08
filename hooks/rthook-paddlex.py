"""
Runtime hook для paddlex.
Выполняется при запуске собранного приложения ДО основного кода.
Отключает проверку зависимостей paddlex.utils.deps.require_extra.
"""

import sys

# Проверяем, запущены ли мы в frozen режиме
if getattr(sys, 'frozen', False):
    try:
        import paddlex.utils.deps as deps_module
        
        # Сохраняем оригинальную функцию (на всякий случай)
        if not hasattr(deps_module, '_original_require_extra'):
            deps_module._original_require_extra = deps_module.require_extra
        
        # Создаем заглушку - функция ничего не делает
        def _dummy_require_extra(extra, obj_name=None, alt=None):
            pass
        
        # Подменяем функцию
        deps_module.require_extra = _dummy_require_extra
        
        print("[PADDLEX Runtime Hook] Dependency check disabled successfully")
        
    except ImportError as e:
        print(f"[PADDLEX Runtime Hook] Could not patch: {e}")
    except Exception as e:
        print(f"[PADDLEX Runtime Hook] Error: {e}")
