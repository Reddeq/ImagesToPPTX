import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import logging
import sys
from ocr_paddle.processor import PaddleOCRProcessor
from ocr_to_pptx.generator import PPTXGenerator

class GUITextHandler(logging.Handler):
    """Перенаправляет логи в текстовое поле Tkinter"""
    def __init__(self, text_widget: tk.Text):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.configure(state='normal')
        self.text_widget.insert('end', msg + '\n')
        self.text_widget.see('end')
        self.text_widget.configure(state='disabled')

class ConverterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Image/PDF → PPTX Converter (PaddleOCR 3.x)")
        self.root.geometry("780x560")
        self.root.minsize(650, 500)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        
        # ✅ Маппинг удобных названий -> коды PaddleOCR
        self.lang_map = {
            "English": "en",
            "Русский": "ru",
            "中文 (Chinese)": "ch"
        }
        self.lang_display = tk.StringVar(value="English")
        
        # PPTX генератор лёгкий, создаём один раз
        self.pptx = PPTXGenerator()

        self._build_ui()
        self._setup_logging()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Input
        ttk.Label(frame, text="Input (PDF / Image):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.input_path, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=self._browse_input).grid(row=0, column=2)

        # Output
        ttk.Label(frame, text="Output PPTX:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.output_path, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=self._browse_output).grid(row=1, column=2)

        # Language & Convert
        ttk.Label(frame, text="OCR Language:").grid(row=2, column=0, sticky=tk.W, pady=10)
        lang_combo = ttk.Combobox(frame, textvariable=self.lang_display,
                                  values=list(self.lang_map.keys()), state="readonly", width=16)
        lang_combo.grid(row=2, column=1, sticky=tk.W, padx=5)

        self.btn_convert = ttk.Button(frame, text="⚡ Convert", command=self._start_conversion)
        self.btn_convert.grid(row=2, column=2, padx=10)

        # Log Area
        ttk.Label(frame, text="Log:").grid(row=3, column=0, sticky=tk.W, pady=(5,0))
        self.log_text = tk.Text(frame, height=15, state='disabled', wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.grid(row=4, column=0, columnspan=3, sticky=tk.NSEW, pady=5)

        frame.grid_rowconfigure(4, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def _setup_logging(self):
        self.logger = logging.getLogger("Converter")
        self.logger.setLevel(logging.INFO)

        gui_handler = GUITextHandler(self.log_text)
        gui_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s"))
        self.logger.addHandler(gui_handler)

        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger.addHandler(console)

    def _browse_input(self):
        p = filedialog.askopenfilename(filetypes=[("Supported", "*.pdf *.png *.jpg *.jpeg *.bmp *.tiff")])
        if p:
            self.input_path.set(p)
            if not self.output_path.get():
                self.output_path.set(p.rsplit('.', 1)[0] + ".pptx")

    def _browse_output(self):
        p = filedialog.asksaveasfilename(defaultextension=".pptx", filetypes=[("PowerPoint", "*.pptx")])
        if p: self.output_path.set(p)

    def _start_conversion(self):
        inp = self.input_path.get()
        out = self.output_path.get()
        if not inp or not out:
            messagebox.showwarning("Warning", "Укажите входной и выходной файлы.")
            return

        self.btn_convert.config(state='disabled', text="⏳ Loading Model & Processing...")
        # ✅ Передаём выбранный язык в воркер
        lang_code = self.lang_map[self.lang_display.get()]
        threading.Thread(target=self._worker, args=(inp, out, lang_code), daemon=True).start()

    def _worker(self, inp: str, out: str, lang: str):
        try:
            # ✅ Инициализируем OCR с выбранным языком прямо в фоне
            # PaddleOCR закэширует модели после первой загрузки (~20-40 сек)
            ocr_processor = PaddleOCRProcessor(use_gpu=False, lang=lang)
            self.logger.info(f"🔍 Запуск OCR (lang={lang})...")
            
            ocr_res = ocr_processor.process(inp)
            found = sum(len(p['texts']) for p in ocr_res)
            self.logger.info(f"✅ OCR завершён. Найдено {found} текстовых блоков.")
            
            self.logger.info("📝 Генерация PPTX...")
            self.pptx.generate(ocr_res, out)
            ocr_processor.cleanup()
            
            self.logger.info("🎉 Конвертация успешно завершена!")
            self.root.after(0, self._finish, True)
            
        except Exception as e:
            # Безопасная очистка даже при крахе инициализации
            try: 
                ocr_processor.cleanup()
            except:
                pass
            self.logger.error(f"❌ Ошибка: {str(e)}")
            self.root.after(0, self._finish, False)

    def _finish(self, success: bool):
        self.btn_convert.config(state='normal', text="⚡ Convert")
        if success:
            messagebox.showinfo("Готово", "Файл PPTX создан!")
        else:
            messagebox.showerror("Ошибка", "Процесс прерван. Проверьте лог.")