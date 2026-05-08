import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, ImageDraw
import fitz
from paddleocr import PaddleOCR


logger = logging.getLogger(__name__)

# Константы для путей к моделям
PADDLEX_MODEL_DIRS = ("official_models", "hub", "models")
PADDLEX_CACHE_DIRS = (".paddlex", ".cache/paddlex")
PADDLEOCR_CACHE_DIRS = (".paddleocr", ".cache/paddleocr")


def _resolve_model_dir() -> str | None:
    """
    В замороженной сборке ищет модели в _internal/_models.
    
    Returns:
        Путь к директории с моделями или None, если не найдено.
    """
    if not getattr(sys, "frozen", False):
        return None

    exe_dir = os.path.dirname(sys.executable)
    
    # Определяем базовую директорию
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(exe_dir)
    
    # Проверяем _internal для portable режима
    internal_dir = Path(exe_dir) / "_internal"
    if not internal_dir.is_dir():
        internal_dir = base_dir
    
    models_dir = internal_dir / "_models"
    
    if not models_dir.is_dir():
        return None

    # Ищем любую подпапку с моделями paddlex
    for root, dirs, _ in os.walk(models_dir):
        for d in dirs:
            candidate = Path(root) / d
            if candidate.is_dir():
                # Проверяем, есть ли внутри подпапки с моделями
                if any(
                    (candidate / subdir).is_dir() 
                    for subdir in PADDLEX_MODEL_DIRS
                ):
                    return str(candidate)

    return None


def _setup_paddlex_paths():
    """
    В замороженной сборке настраивает пути к конфигурационным файлам PaddleX.
    Это необходимо для корректной работы load_pipeline_config().
    """
    if not getattr(sys, "frozen", False):
        return
    
    # Определяем базовую директорию
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(os.path.dirname(sys.executable))
    
    # Проверяем _internal для portable режима (onedir)
    internal_dir = Path(os.path.dirname(sys.executable)) / "_internal"
    if not internal_dir.is_dir():
        internal_dir = base_dir
    
    logger.info(f"Frozen mode detected. Base dir: {base_dir}, Internal dir: {internal_dir}")
    
    # Пути к пакетам в frozen-режиме
    paddlex_dir = internal_dir / "paddlex"
    paddleocr_dir = internal_dir / "paddleocr"
    ppocr_dir = internal_dir / "ppocr"
    
    # Также проверяем base_dir на случай другой структуры
    if not paddlex_dir.is_dir():
        paddlex_dir = base_dir / "paddlex"
    if not paddleocr_dir.is_dir():
        paddleocr_dir = base_dir / "paddleocr"
    if not ppocr_dir.is_dir():
        ppocr_dir = base_dir / "ppocr"
    
    # Устанавливаем переменные окружения для PaddleX
    if paddlex_dir.is_dir():
        logger.info(f"Found paddlex directory: {paddlex_dir}")
        paddlex_inference_dir = paddlex_dir / "inference"
        if paddlex_inference_dir.is_dir():
            os.environ.setdefault("PADDLEX_INFERENCE_DIR", str(paddlex_inference_dir))
            logger.info(f"Set PADDLEX_INFERENCE_DIR={paddlex_inference_dir}")
        
        # Добавляем путь к paddlex в PYTHONPATH для корректного импорта конфигов
        paddlex_parent = str(paddlex_dir.parent)
        if paddlex_parent not in sys.path:
            sys.path.insert(0, paddlex_parent)
            logger.info(f"Added to sys.path: {paddlex_parent}")
    else:
        logger.warning(f"PaddleX directory not found. Checked: {internal_dir / 'paddlex'}, {base_dir / 'paddlex'}")
    
    if paddleocr_dir.is_dir():
        logger.info(f"Found paddleocr directory: {paddleocr_dir}")
        paddleocr_path = str(paddleocr_dir.parent)
        if paddleocr_path not in sys.path:
            sys.path.insert(0, paddleocr_path)
            logger.info(f"Added to sys.path: {paddleocr_path}")
    else:
        logger.warning(f"PaddleOCR directory not found. Checked: {internal_dir / 'paddleocr'}, {base_dir / 'paddleocr'}")
    
    if ppocr_dir.is_dir():
        logger.info(f"Found ppocr directory: {ppocr_dir}")
        ppocr_path = str(ppocr_dir.parent)
        if ppocr_path not in sys.path:
            sys.path.insert(0, ppocr_path)
            logger.info(f"Added to sys.path: {ppocr_path}")
    else:
        logger.warning(f"PPOCR directory not found. Checked: {internal_dir / 'ppocr'}, {base_dir / 'ppocr'}")


class PaddleOCRProcessor:
    def __init__(
        self,
        use_gpu: bool = False,
        lang: str = "en",
        dpi: int = 200,
        ocr_padding_px: int = 32,
        apply_exif_transpose: bool = True,
    ) -> None:
        """
        Args:
            use_gpu: Использовать GPU для PaddleOCR.
            lang: Язык PaddleOCR.
            dpi: DPI для рендера PDF в изображения.
            ocr_padding_px: Белый padding вокруг изображения перед OCR.
                            Помогает находить текст у самых краёв.
            apply_exif_transpose: Нормализовать EXIF orientation для обычных изображений.
        """
        device = "gpu" if use_gpu else "cpu"

        # В frozen-режиме настраиваем пути к PaddleX/PaddleOCR
        _setup_paddlex_paths()

        # В frozen-режиме указываем путь к bundled-моделям
        model_dir = _resolve_model_dir()
        if model_dir:
            logger.info(f"Используются bundled модели из: {model_dir}")
            os.environ["PADDLEOCR_MODEL_DIR"] = model_dir
            os.environ["PADDLEX_MODEL_DIR"] = model_dir

        self.ocr = PaddleOCR(
            lang=lang,
            device=device,
            use_angle_cls=True,
        )

        logging.getLogger("paddleocr").setLevel(logging.WARNING)

        self.lang = lang
        self.dpi = dpi
        self.ocr_padding_px = max(0, int(ocr_padding_px))
        self.apply_exif_transpose = apply_exif_transpose

        self._temp_dir: str | None = None

    def _ensure_temp_dir(self) -> str:
        if not self._temp_dir:
            self._temp_dir = tempfile.mkdtemp(prefix="pptx_ocr_")
        return self._temp_dir

    def _pdf_to_images(self, pdf_path: str) -> list[str]:
        """
        Конвертирует PDF в PNG-страницы.
        Эти изображения потом вставляются в PPTX.
        """
        temp_dir = self._ensure_temp_dir()

        paths: list[str] = []
        doc = fitz.open(pdf_path)

        try:
            for i, page in enumerate(doc):
                pix = page.get_pixmap(dpi=self.dpi)

                img_path = os.path.join(temp_dir, f"page_{i + 1}.png")
                pix.save(img_path)

                paths.append(img_path)
        finally:
            doc.close()

        return paths

    def _prepare_image_if_needed(self, input_path: str) -> str:
        """
        Для обычных изображений нормализует EXIF orientation.

        Важно: возвращаемый файл — это изображение, которое будет вставлено в PPTX.
        OCR будет делаться уже по его padded-копии.
        """
        if not self.apply_exif_transpose:
            return input_path

        suffix = Path(input_path).suffix.lower()

        if suffix not in {".jpg", ".jpeg", ".tif", ".tiff", ".webp"}:
            return input_path

        temp_dir = self._ensure_temp_dir()

        try:
            with Image.open(input_path) as img:
                transposed = ImageOps.exif_transpose(img)

                out_path = os.path.join(
                    temp_dir,
                    f"normalized_{Path(input_path).stem}.png",
                )

                transposed.save(out_path)
                return out_path

        except Exception as exc:
            logger.warning(
                "⚠️ Не удалось применить EXIF transpose к изображению %s: %s",
                input_path,
                exc,
            )
            return input_path

    def _get_image_size(self, img_path: str) -> tuple[int, int]:
        try:
            with Image.open(img_path) as img:
                return img.size
        except Exception as exc:
            logger.warning(
                "⚠️ Не удалось прочитать размер изображения %s: %s",
                img_path,
                exc,
            )
            return 0, 0

    def _make_padded_image(self, img_path: str, padding_px: int) -> tuple[str, int, int]:
        """
        Создаёт временную картинку с белыми полями для OCR.

        Возвращает:
            padded_img_path, pad_x, pad_y

        Координаты PaddleOCR будут относиться к padded_img_path.
        Поэтому после OCR из x/y нужно вычесть pad_x/pad_y.
        """
        if padding_px <= 0:
            return img_path, 0, 0

        temp_dir = self._ensure_temp_dir()

        try:
            with Image.open(img_path) as img:
                src = img.convert("RGB")

                padded_w = src.width + padding_px * 2
                padded_h = src.height + padding_px * 2

                padded = Image.new("RGB", (padded_w, padded_h), "white")
                padded.paste(src, (padding_px, padding_px))

                out_path = os.path.join(
                    temp_dir,
                    f"padded_{Path(img_path).stem}.png",
                )

                padded.save(out_path)

                return out_path, padding_px, padding_px

        except Exception as exc:
            logger.warning(
                "⚠️ Не удалось создать padded image для %s: %s",
                img_path,
                exc,
            )
            return img_path, 0, 0

    def _normalize_poly(self, box: Any) -> list[tuple[float, float]]:
        """
        Приводит polygon/bbox к списку точек [(x, y), ...].
        """
        try:
            if not isinstance(box, (list, tuple)) or len(box) == 0:
                return []

            points: list[tuple[float, float]] = []

            if isinstance(box[0], (list, tuple)):
                for point in box:
                    if len(point) >= 2:
                        points.append((float(point[0]), float(point[1])))
            else:
                usable_len = len(box) - (len(box) % 2)

                for i in range(0, usable_len, 2):
                    points.append((float(box[i]), float(box[i + 1])))

            return points

        except Exception as exc:
            logger.debug("⚠️ Не удалось нормализовать polygon=%r: %s", box, exc)
            return []

    def _shift_and_clip_poly(
        self,
        poly: Any,
        shift_x: float,
        shift_y: float,
        img_w: int,
        img_h: int,
    ) -> list[tuple[float, float]]:
        """
        Переводит координаты из padded image обратно в координаты исходного изображения.

        shift_x/shift_y обычно отрицательные:
            x_original = x_padded - padding
            y_original = y_padded - padding
        """
        points = self._normalize_poly(poly)

        if not points:
            return []

        shifted: list[tuple[float, float]] = []

        for x, y in points:
            sx = x + shift_x
            sy = y + shift_y

            # Мягко ограничиваем координаты границами исходного изображения.
            sx = max(0.0, min(float(img_w), sx))
            sy = max(0.0, min(float(img_h), sy))

            shifted.append((sx, sy))

        return shifted

    def _extract_data(
        self,
        res_item: Any,
        shift_x: float = 0.0,
        shift_y: float = 0.0,
        img_w: int = 0,
        img_h: int = 0,
    ) -> list[dict]:
        """
        Безопасный парсинг Result объекта PaddleOCR 3.x.

        Если OCR делался по padded image, shift_x/shift_y должны вернуть
        координаты к исходной картинке.
        """
        texts: list[dict] = []

        try:
            json_data = getattr(res_item, "json", None)

            if not isinstance(json_data, dict):
                logger.debug(
                    "⚠️ У OCR result отсутствует json dict: %r",
                    type(res_item),
                )
                return texts

            data = json_data.get("res", {})

            polys = data.get("dt_polys", []) or []
            rec_texts = data.get("rec_texts", []) or []
            rec_scores = data.get("rec_scores", []) or []

            if not (len(polys) == len(rec_texts) == len(rec_scores)):
                logger.warning(
                    "⚠️ Разная длина OCR-массивов: dt_polys=%d, rec_texts=%d, rec_scores=%d",
                    len(polys),
                    len(rec_texts),
                    len(rec_scores),
                )

            for poly, txt, score in zip(polys, rec_texts, rec_scores):
                txt_str = str(txt).strip()

                if not txt_str:
                    continue

                adjusted_poly = self._shift_and_clip_poly(
                    poly=poly,
                    shift_x=shift_x,
                    shift_y=shift_y,
                    img_w=img_w,
                    img_h=img_h,
                )

                if not adjusted_poly:
                    continue

                try:
                    confidence = float(score)
                except Exception:
                    confidence = 0.0

                texts.append(
                    {
                        "text": txt_str,
                        "box": adjusted_poly,
                        "confidence": confidence,
                    }
                )

        except Exception as exc:
            logger.warning("⚠️ Не удалось распарсить результат OCR: %s", exc)

        return texts

    def process(self, input_path: str) -> list[dict]:
        input_file = Path(input_path)

        if not input_file.exists():
            raise FileNotFoundError(f"Файл не найден: {input_path}")

        is_pdf = input_file.suffix.lower() == ".pdf"

        if is_pdf:
            display_img_paths = self._pdf_to_images(str(input_file))
        else:
            display_img_paths = [self._prepare_image_if_needed(str(input_file))]

        results: list[dict] = []

        for idx, display_img_path in enumerate(display_img_paths):
            logger.debug("OCR: %s", Path(display_img_path).name)

            img_w, img_h = self._get_image_size(display_img_path)

            page_data = {
                "page": idx + 1,
                "texts": [],
                "img_size": (img_w, img_h),
                # В PPTX вставляем именно исходное/нормализованное изображение,
                # НЕ padded image.
                "img_path": display_img_path,
            }

            if img_w <= 1 or img_h <= 1:
                logger.warning(
                    "⚠️ Страница #%d пропущена OCR: некорректный размер изображения %s",
                    idx + 1,
                    (img_w, img_h),
                )
                results.append(page_data)
                continue

            # Для OCR используем копию с белым padding.
            ocr_img_path, pad_x, pad_y = self._make_padded_image(
                display_img_path,
                self.ocr_padding_px,
            )

            try:
                ocr_res = self.ocr.ocr(ocr_img_path)
            except Exception as exc:
                logger.warning(
                    "⚠️ OCR ошибка на странице #%d: %s",
                    idx + 1,
                    exc,
                )
                results.append(page_data)
                continue

            if not ocr_res:
                results.append(page_data)
                continue

            # Координаты PaddleOCR относятся к padded image.
            # Возвращаем их назад к исходному изображению.
            shift_x = -float(pad_x)
            shift_y = -float(pad_y)

            for res_item in ocr_res:
                page_data["texts"].extend(
                    self._extract_data(
                        res_item=res_item,
                        shift_x=shift_x,
                        shift_y=shift_y,
                        img_w=img_w,
                        img_h=img_h,
                    )
                )

            results.append(page_data)

        logger.info("✅ OCR завершён. Страниц: %d", len(results))
        return results

    def save_debug_overlay(self, page_data: dict, output_path: str) -> None:
        """
        Рисует OCR-полигоны поверх изображения, которое пойдёт в PPTX.

        Если тут боксы совпадают, значит проблема уже в PPTXGenerator.
        Если тут боксы смещены, значит проблема на этапе OCR/координат.
        """
        img_path = page_data.get("img_path")
        texts = page_data.get("texts") or []

        if not img_path:
            logger.warning("⚠️ Нельзя создать debug overlay: отсутствует img_path")
            return

        try:
            with Image.open(img_path) as img:
                debug_img = img.convert("RGB")
        except Exception as exc:
            logger.warning(
                "⚠️ Не удалось открыть изображение для debug overlay: %s",
                exc,
            )
            return

        draw = ImageDraw.Draw(debug_img)

        for item in texts:
            box = item.get("box")
            text = str(item.get("text") or "")

            points = self._normalize_poly(box)

            if len(points) < 2:
                continue

            draw.line(points + [points[0]], fill=(255, 0, 0), width=2)

            x, y = points[0]
            draw.text(
                (x, max(0, y - 14)),
                text[:40],
                fill=(0, 0, 255),
            )

        output = Path(output_path)

        if output.parent and not output.parent.exists():
            output.parent.mkdir(parents=True, exist_ok=True)

        debug_img.save(str(output))
        logger.info("✅ Debug overlay сохранён: %s", output)

    def cleanup(self) -> None:
        """
        Очистка временных файлов после генерации PPTX.

        Важно вызывать cleanup только после сохранения PPTX,
        потому что для PDF изображения страниц лежат во временной папке.
        """
        if self._temp_dir and os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            logger.debug("🗑️ Временные изображения удалены")

        self._temp_dir = None
