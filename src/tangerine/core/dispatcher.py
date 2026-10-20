import os
import shutil
import subprocess
from pathlib import Path
from typing import Any
from tangerine.config import CONFIG
from tangerine.core.image_worker import ImageWorker
from tangerine.core.pdf_worker import PDFWorker
from tangerine.core.media_worker import MediaWorker
from tangerine.core.doc_worker import DocWorker
from tangerine.core.action_worker import ActionWorker


class ConversionDispatcher:
    @staticmethod
    def get_unique_path(path: Path) -> Path:
        if not path.exists():
            return path
        counter = 1
        while True:
            candidate = path.parent / f"{path.stem}_{counter}{path.suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    @classmethod
    def dispatch(
        cls,
        file_paths: list[str],
        mode: str,
        target: str,
        options: dict[str, Any] | None = None
    ) -> list[str]:
        opts = options or {}
        paths = [Path(p) for p in file_paths if os.path.exists(p)]
        if not paths:
            return []

        results: list[str] = []

        # ==========================================
        # 1. SHIFT WHEEL: CONVERT
        # ==========================================
        if mode == "CONVERT":
            target_ext = f".{target.lower()}"

            if target == "PDF" and len(paths) > 1 and all(p.suffix.lower() == ".pdf" for p in paths):
                out = cls.get_unique_path(paths[0].parent / f"{paths[0].stem}_merged.pdf")
                PDFWorker.merge_pdfs(paths, out)
                return [out.name]

            if target == "PDF" and len(paths) > 1 and all(p.suffix.lower() in CONFIG.IMAGE_EXTS for p in paths):
                out = cls.get_unique_path(paths[0].parent / f"{paths[0].stem}_combined.pdf")
                PDFWorker.images_to_pdf(paths, out)
                return [out.name]

            for p in paths:
                ext = p.suffix.lower()
                if ext == target_ext:
                    continue
                out = cls.get_unique_path(p.with_suffix(target_ext))
                try:
                    if ext == ".svg" and target in ("PNG", "PDF"):
                        DocWorker.render_svg(p, out, target)
                        results.append(out.name)
                    elif ext in CONFIG.SUBTITLE_EXTS and target in ("SRT", "VTT", "TXT"):
                        DocWorker.convert_subtitle(p, out, target)
                        results.append(out.name)
                    elif ext in CONFIG.DATA_EXTS and target in ("CSV", "JSON"):
                        DocWorker.convert_data(p, out, target)
                        results.append(out.name)
                    elif ext == ".pdf" and target == "TXT":
                        results.extend(PDFWorker.extract_text_and_images(p, out))
                    elif ext in CONFIG.IMAGE_EXTS and target in ("PNG", "JPG", "WEBP", "PDF", "AVIF"):
                        ImageWorker.convert(p, out, target)
                        results.append(out.name)
                    elif ext in CONFIG.MEDIA_EXTS:
                        MediaWorker.convert(p, out)
                        results.append(out.name)
                    elif target in ("PDF", "DOCX", "EPUB", "TXT"):
                        if shutil.which("pandoc"):
                            subprocess.run(["pandoc", str(p), "-o", str(out)], check=True)
                            results.append(out.name)
                        elif shutil.which("libreoffice"):
                            subprocess.run(
                                ["libreoffice", "--headless", "--convert-to", target.lower(), str(p), "--outdir", str(p.parent)],
                                check=True
                            )
                            results.append(out.name)
                except Exception as e:
                    print(f"[Convert Error] {p.name} -> {target}: {e}")

        # ==========================================
        # 2. ALT WHEEL: TOOLS
        # ==========================================
        elif mode == "TOOLS":
            for p in paths:
                ext = p.suffix.lower()
                try:
                    if target == "COMPRESS":
                        quality = opts.get("quality", 65)
                        if ext in CONFIG.IMAGE_EXTS:
                            out = cls.get_unique_path(p.parent / f"{p.stem}_q{quality}.jpg")
                            ImageWorker.compress(p, out, quality=quality)
                            results.append(out.name)
                        elif ext in CONFIG.MEDIA_EXTS:
                            out = cls.get_unique_path(p.parent / f"{p.stem}_compressed{ext}")
                            MediaWorker.compress_media(p, out)
                            results.append(out.name)

                    elif target == "RESIZE" and ext in CONFIG.IMAGE_EXTS:
                        scale = opts.get("scale", 50)
                        rotate = opts.get("rotate", 0)
                        out = cls.get_unique_path(p.parent / f"{p.stem}_{scale}pct{ext}")
                        ImageWorker.transform(p, out, scale_pct=scale, rotate_deg=rotate)
                        results.append(out.name)

                    elif target == "CLEAN EXIF" and ext in CONFIG.IMAGE_EXTS:
                        out = cls.get_unique_path(p.parent / f"{p.stem}_clean{ext}")
                        ImageWorker.strip_exif(p, out)
                        results.append(out.name)

                    elif target == "SPLIT" and ext == ".pdf":
                        results.extend(PDFWorker.split_pdf(p))

                    elif target == "TRIM" and ext in CONFIG.MEDIA_EXTS:
                        start_t = opts.get("start", "00:00:00")
                        dur_t = opts.get("duration", "00:00:15")
                        out = cls.get_unique_path(p.parent / f"{p.stem}_trimmed{ext}")
                        MediaWorker.trim_media(p, out, start_t, dur_t)
                        results.append(out.name)

                    elif target == "EXTRACT":
                        if ext == ".pdf":
                            out = cls.get_unique_path(p.with_suffix(".txt"))
                            results.extend(PDFWorker.extract_text_and_images(p, out))
                        elif ext in CONFIG.MEDIA_EXTS:
                            out = cls.get_unique_path(p.with_suffix(".mp3"))
                            MediaWorker.extract_audio(p, out)
                            results.append(out.name)
                        elif ext == ".zip":
                            out_dir = cls.get_unique_path(p.parent / p.stem)
                            shutil.unpack_archive(str(p), str(out_dir))
                            results.append(out_dir.name)
                except Exception as e:
                    print(f"[Tools Error] {p.name} ({target}): {e}")

            if target == "MERGE" and len(paths) > 1:
                if all(p.suffix.lower() == ".pdf" for p in paths):
                    out = cls.get_unique_path(paths[0].parent / f"{paths[0].stem}_merged.pdf")
                    PDFWorker.merge_pdfs(paths, out)
                    results.append(out.name)
                elif all(p.suffix.lower() in CONFIG.IMAGE_EXTS for p in paths):
                    out = cls.get_unique_path(paths[0].parent / f"{paths[0].stem}_merged.pdf")
                    PDFWorker.images_to_pdf(paths, out)
                    results.append(out.name)

        # ==========================================
        # 3. CTRL WHEEL: ACTIONS
        # ==========================================
        elif mode == "ACTIONS":
            if target == "COPY PATH":
                results.append(ActionWorker.copy_path(file_paths))
            elif target == "SHA256":
                results.append(ActionWorker.copy_sha256(file_paths))
            elif target == "TERMINAL":
                results.append(ActionWorker.open_terminal(file_paths[0]))
            elif target == "SHARE":
                out_zip = cls.get_unique_path(paths[0].parent / f"{paths[0].stem}_archive.zip")
                results.append(ActionWorker.zip_for_share(file_paths, out_zip))

        return results