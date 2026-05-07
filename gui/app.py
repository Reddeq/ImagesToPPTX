import logging
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from ocr_paddle.processor import PaddleOCRProcessor
from ocr_to_pptx.generator import PPTXGenerator

from updater.updater import (
    is_update_available,
    prepare_update,
    run_update_script,
)
from updater.version import __version__


class GUITextHandler(logging.Handler):
    """
    Потокобезопасный handler для вывода логов в Tkinter Text.

    ВАЖНО:
        Tkinter нельзя безопасно обновлять напрямую из фонового потока.
        Поэтому вставка текста выполняется через root.after(...).
    """

    def __init__(self, root: tk.Tk, text_widget: tk.Text):
        super().__init__()
        self.root = root
        self.text_widget = text_widget

    def emit(self, record):
        try:
            msg = self.format(record)
            self.root.after(0, self._append, msg)
        except Exception:
            pass

    def _append(self, msg: str):
        try:
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", msg + "\n")
            self.text_widget.see("end")
            self.text_widget.configure(state="disabled")
        except tk.TclError:
            pass


class ConverterApp:
    def __init__(self, root: tk.Tk):
        self.root = root

        self.root.title(f"Image/PDF → PPTX Converter v{__version__} - PaddleOCR 3.x")
        self.root.geometry("780x560")
        self.root.minsize(650, 500)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()

        self.lang_map = {
            "English": "en",
            "Русский": "ru",
            "中文 (Chinese)": "ch",
        }

        self.lang_display = tk.StringVar(value="English")

        self.is_converting = False
        self.is_checking_updates = False
        self.is_preparing_update = False

        # PPTXGenerator лёгкий — можно создать один раз.
        self.pptx = PPTXGenerator()

        self._build_ui()
        self._setup_logging()
        self._build_menu()

        self.logger.info(f"Приложение запущено. Версия: {__version__}")

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Input
        ttk.Label(frame, text="Input (PDF / Image):").grid(
            row=0,
            column=0,
            sticky=tk.W,
            pady=5,
        )

        self.entry_input = ttk.Entry(
            frame,
            textvariable=self.input_path,
            width=60,
        )
        self.entry_input.grid(
            row=0,
            column=1,
            padx=5,
            sticky=tk.EW,
        )

        self.btn_browse_input = ttk.Button(
            frame,
            text="Browse",
            command=self._browse_input,
        )
        self.btn_browse_input.grid(row=0, column=2)

        # Output
        ttk.Label(frame, text="Output PPTX:").grid(
            row=1,
            column=0,
            sticky=tk.W,
            pady=5,
        )

        self.entry_output = ttk.Entry(
            frame,
            textvariable=self.output_path,
            width=60,
        )
        self.entry_output.grid(
            row=1,
            column=1,
            padx=5,
            sticky=tk.EW,
        )

        self.btn_browse_output = ttk.Button(
            frame,
            text="Browse",
            command=self._browse_output,
        )
        self.btn_browse_output.grid(row=1, column=2)

        # Language
        ttk.Label(frame, text="OCR Language:").grid(
            row=2,
            column=0,
            sticky=tk.W,
            pady=10,
        )

        self.lang_combo = ttk.Combobox(
            frame,
            textvariable=self.lang_display,
            values=list(self.lang_map.keys()),
            state="readonly",
            width=18,
        )
        self.lang_combo.grid(
            row=2,
            column=1,
            sticky=tk.W,
            padx=5,
        )

        # Convert
        self.btn_convert = ttk.Button(
            frame,
            text="⚡ Convert",
            command=self._start_conversion,
        )
        self.btn_convert.grid(row=2, column=2, padx=10)

        # Log
        ttk.Label(frame, text="Log:").grid(
            row=3,
            column=0,
            sticky=tk.W,
            pady=(5, 0),
        )

        log_frame = ttk.Frame(frame)
        log_frame.grid(
            row=4,
            column=0,
            columnspan=3,
            sticky=tk.NSEW,
            pady=5,
        )

        self.log_text = tk.Text(
            log_frame,
            height=15,
            state="disabled",
            wrap=tk.WORD,
            font=("Consolas", 9),
        )

        scrollbar = ttk.Scrollbar(
            log_frame,
            orient=tk.VERTICAL,
            command=self.log_text.yview,
        )

        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y,
        )

        frame.grid_rowconfigure(4, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def _build_menu(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(
            label="Выход",
            command=self._on_close,
        )

        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(
            label="Проверить обновления",
            command=self._check_updates,
        )
        help_menu.add_separator()
        help_menu.add_command(
            label="О программе",
            command=self._show_about,
        )

        menu_bar.add_cascade(label="Файл", menu=file_menu)
        menu_bar.add_cascade(label="Помощь", menu=help_menu)

        self.root.config(menu=menu_bar)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_logging(self):
        self.logger = logging.getLogger("Converter")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        # Чтобы при пересоздании окна/приложения не плодить handlers.
        self.logger.handlers.clear()

        formatter_gui = logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%H:%M:%S",
        )

        gui_handler = GUITextHandler(self.root, self.log_text)
        gui_handler.setFormatter(formatter_gui)
        self.logger.addHandler(gui_handler)

        formatter_console = logging.Formatter("%(levelname)s: %(message)s")

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter_console)
        self.logger.addHandler(console_handler)

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Выберите PDF или изображение",
            filetypes=[
                ("Supported files", "*.pdf *.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                ("PDF files", "*.pdf"),
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif"),
                ("All files", "*.*"),
            ],
        )

        if not path:
            return

        self.input_path.set(path)

        if not self.output_path.get():
            input_file = Path(path)
            self.output_path.set(str(input_file.with_suffix(".pptx")))

    def _browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Сохранить PPTX как",
            defaultextension=".pptx",
            filetypes=[
                ("PowerPoint", "*.pptx"),
                ("All files", "*.*"),
            ],
        )

        if path:
            self.output_path.set(path)

    def _validate_paths(self, inp: str, out: str) -> bool:
        if not inp or not out:
            messagebox.showwarning(
                "Warning",
                "Укажите входной и выходной файлы.",
                parent=self.root,
            )
            return False

        input_file = Path(inp)

        if not input_file.exists():
            messagebox.showwarning(
                "Warning",
                "Входной файл не найден.",
                parent=self.root,
            )
            return False

        if input_file.is_dir():
            messagebox.showwarning(
                "Warning",
                "В качестве входного файла указана папка.",
                parent=self.root,
            )
            return False

        output_file = Path(out)

        if output_file.suffix.lower() != ".pptx":
            messagebox.showwarning(
                "Warning",
                "Выходной файл должен иметь расширение .pptx.",
                parent=self.root,
            )
            return False

        output_parent = output_file.parent

        if output_parent and not output_parent.exists():
            messagebox.showwarning(
                "Warning",
                "Папка для сохранения PPTX не существует.",
                parent=self.root,
            )
            return False

        return True

    def _start_conversion(self):
        if self.is_converting:
            return

        inp = self.input_path.get().strip()
        out = self.output_path.get().strip()

        if not self._validate_paths(inp, out):
            return

        lang_display = self.lang_display.get()
        lang_code = self.lang_map.get(lang_display, "en")

        self.is_converting = True
        self._set_conversion_controls_enabled(False)

        self.btn_convert.config(
            state="disabled",
            text="⏳ Processing...",
        )

        self.logger.info(f"Выбран входной файл: {inp}")
        self.logger.info(f"Выбран выходной файл: {out}")
        self.logger.info(f"Выбран язык OCR: {lang_display} ({lang_code})")

        worker = threading.Thread(
            target=self._worker,
            args=(inp, out, lang_code),
            daemon=True,
        )
        worker.start()

    def _worker(self, inp: str, out: str, lang: str):
        ocr_processor = None

        try:
            self.logger.info("Инициализация PaddleOCR...")
            ocr_processor = PaddleOCRProcessor(use_gpu=False, lang=lang)

            self.logger.info(f"🔍 Запуск OCR, lang={lang}...")
            ocr_res = ocr_processor.process(inp)

            found = 0
            for page in ocr_res:
                texts = page.get("texts", [])
                found += len(texts)

            self.logger.info(f"✅ OCR завершён. Найдено текстовых блоков: {found}")

            self.logger.info("📝 Генерация PPTX...")
            self.pptx.generate(ocr_res, out)

            self.logger.info("🎉 Конвертация успешно завершена.")
            self.root.after(0, self._finish_conversion, True)

        except Exception as exc:
            self.logger.exception(f"❌ Ошибка конвертации: {exc}")
            self.root.after(0, self._finish_conversion, False)

        finally:
            if ocr_processor is not None:
                try:
                    ocr_processor.cleanup()
                    self.logger.info("Ресурсы OCR освобождены.")
                except Exception as cleanup_exc:
                    self.logger.warning(f"Не удалось корректно очистить OCR: {cleanup_exc}")

    def _finish_conversion(self, success: bool):
        self.is_converting = False
        self._set_conversion_controls_enabled(True)

        self.btn_convert.config(
            state="normal",
            text="⚡ Convert",
        )

        if success:
            messagebox.showinfo(
                "Готово",
                "Файл PPTX создан!",
                parent=self.root,
            )
        else:
            messagebox.showerror(
                "Ошибка",
                "Процесс прерван. Проверьте лог.",
                parent=self.root,
            )

    def _set_conversion_controls_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"

        widgets = [
            self.entry_input,
            self.entry_output,
            self.btn_browse_input,
            self.btn_browse_output,
            self.lang_combo,
        ]

        for widget in widgets:
            try:
                widget.configure(state=state)
            except tk.TclError:
                pass

        # Combobox должен оставаться readonly, а не normal.
        if enabled:
            try:
                self.lang_combo.configure(state="readonly")
            except tk.TclError:
                pass

    def _check_updates(self):
        if self.is_checking_updates or self.is_preparing_update:
            messagebox.showinfo(
                "Обновления",
                "Проверка или подготовка обновления уже выполняется.",
                parent=self.root,
            )
            return

        self.is_checking_updates = True
        self.logger.info("🔄 Проверка обновлений...")

        worker = threading.Thread(
            target=self._check_updates_worker,
            daemon=True,
        )
        worker.start()

    def _check_updates_worker(self):
        try:
            has_update, info = is_update_available()
            self.root.after(
                0,
                lambda: self._handle_update_check_result(has_update, info),
            )

        except Exception as exc:
            self.root.after(
                0,
                lambda: self._handle_update_check_error(exc),
            )

    def _handle_update_check_error(self, exc: Exception):
        self.is_checking_updates = False
        self.logger.error(f"❌ Ошибка проверки обновлений: {exc}")

        messagebox.showerror(
            "Обновления",
            "Произошла ошибка при проверке обновлений.",
            parent=self.root,
        )

    def _handle_update_check_result(self, has_update: bool, info: dict | None):
        self.is_checking_updates = False

        if not getattr(sys, "frozen", False):
            self.logger.info("Проверка обновлений доступна только в собранной версии.")
            messagebox.showinfo(
                "Обновления",
                "Проверка обновлений работает только в собранной версии приложения.",
                parent=self.root,
            )
            return

        if sys.platform != "win32":
            self.logger.info("Автообновление поддерживается только для Windows-сборки.")
            messagebox.showinfo(
                "Обновления",
                "Автообновление сейчас поддерживается только для Windows-сборки.",
                parent=self.root,
            )
            return

        if info is None:
            self.logger.warning("Не удалось получить информацию об обновлениях.")
            messagebox.showinfo(
                "Обновления",
                "Не удалось проверить обновления.",
                parent=self.root,
            )
            return

        if not has_update:
            self.logger.info(f"Обновлений нет. Текущая версия: {__version__}")
            messagebox.showinfo(
                "Обновления",
                f"У вас уже последняя версия: {__version__}",
                parent=self.root,
            )
            return

        latest_version = info.get("version", "unknown")
        notes = info.get("body", "").strip() or "Описание обновления отсутствует."

        self.logger.info(f"Доступно обновление: {latest_version}")

        should_update = messagebox.askyesno(
            "Доступно обновление",
            f"Текущая версия: {__version__}\n"
            f"Новая версия: {latest_version}\n\n"
            f"Что нового:\n{notes[:700]}\n\n"
            f"Скачать и установить обновление?",
            parent=self.root,
        )

        if not should_update:
            self.logger.info("Обновление отменено пользователем.")
            return

        self.is_preparing_update = True
        self.logger.info(f"⬇️ Подготовка обновления {latest_version}...")

        worker = threading.Thread(
            target=self._prepare_update_worker,
            args=(info,),
            daemon=True,
        )
        worker.start()

    def _prepare_update_worker(self, info: dict):
        try:
            ok, result = prepare_update(info)
            self.root.after(
                0,
                lambda: self._handle_prepared_update(ok, result),
            )

        except Exception as exc:
            self.root.after(
                0,
                lambda: self._handle_prepare_update_error(exc),
            )

    def _handle_prepare_update_error(self, exc: Exception):
        self.is_preparing_update = False
        self.logger.error(f"❌ Ошибка подготовки обновления: {exc}")

        messagebox.showerror(
            "Ошибка",
            "Произошла ошибка при подготовке обновления.",
            parent=self.root,
        )

    def _handle_prepared_update(self, ok: bool, result):
        self.is_preparing_update = False

        if not ok:
            self.logger.error(f"❌ Ошибка обновления: {result}")
            messagebox.showwarning(
                "Ошибка",
                str(result),
                parent=self.root,
            )
            return

        script_path = result

        self.logger.info("✅ Обновление загружено и готово к установке.")

        messagebox.showinfo(
            "Обновление загружено",
            "Приложение сейчас закроется, обновится и запустится снова.",
            parent=self.root,
        )

        started = run_update_script(script_path)

        if not started:
            self.logger.error("Не удалось запустить скрипт обновления.")
            messagebox.showerror(
                "Ошибка",
                "Не удалось запустить скрипт обновления.",
                parent=self.root,
            )
            return

        self.root.destroy()

    def _show_about(self):
        messagebox.showinfo(
            "О программе",
            f"Image/PDF → PPTX Converter\n"
            f"Версия: {__version__}\n\n"
            f"OCR: PaddleOCR 3.x\n"
            f"Формат вывода: PPTX",
            parent=self.root,
        )

    def _on_close(self):
        if self.is_converting:
            should_close = messagebox.askyesno(
                "Выход",
                "Конвертация ещё выполняется. Закрыть приложение?",
                parent=self.root,
            )

            if not should_close:
                return

        if self.is_preparing_update:
            should_close = messagebox.askyesno(
                "Выход",
                "Подготовка обновления ещё выполняется. Закрыть приложение?",
                parent=self.root,
            )

            if not should_close:
                return

        self.root.destroy()