import os
import shutil
import subprocess
from pathlib import Path
from tangerine.config import CONFIG
from tangerine.core.image_worker import ImageWorker
from tangerine.core.pdf_worker import PDFWorker
from tangerine.core.media_worker import MediaWorker
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
    def dispatch(cls, file_paths: list[str], mode: str, target: str) -> list[str]:
        paths = [Path(p) for p in file_paths if os.path.exists(p)]
        if not paths:
            return []

        results: list[str] = []

        # ==========================================
        # 1. SHIFT WHEEL: CONVERT
        # ==========================================
        if mode == "CONVERT":
            target_ext = f".{target.lower()}"

            # Multi-PDF Merge shortcut when dropping PDFs on PDF
            if target == "PDF" and len(paths) > 1 and all(p.suffix.lower() == ".pdf" for p in paths):
                out = cls.get_unique_path(paths[0].parent / f"{paths[0].stem}_merged.pdf")
                PDFWorker.merge_pdfs(paths, out)
                return [out.name]

            # Multi-Image to Single PDF
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
                    if ext in CONFIG.IMAGE_EXTS and target in ("PNG", "JPG", "WEBP", "PDF"):
                        ImageWorker.convert(p, out, target)
                        results.append(out.name)
                    elif ext in CONFIG.MEDIA_EXTS and target in ("MP4", "MP3", "WEBP"):
                        MediaWorker.convert(p, out)
                        results.append(out.name)
                    elif target in ("PDF", "DOCX", "EPUB"):
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
                        if ext in CONFIG.IMAGE_EXTS:
                            out = cls.get_unique_path(p.parent / f"{p.stem}_compressed.jpg")
                            ImageWorker.compress(p, out, quality=60)
                            results.append(out.name)
                        elif ext in CONFIG.MEDIA_EXTS:
                            out = cls.get_unique_path(p.parent / f"{p.stem}_compressed{ext}")
                            MediaWorker.compress_media(p, out)
                            results.append(out.name)

                    elif target == "RESIZE" and ext in CONFIG.IMAGE_EXTS:
                        out = cls.get_unique_path(p.parent / f"{p.stem}_50pct{ext}")
                        ImageWorker.resize_half(p, out)
                        results.append(out.name)

                    elif target == "SPLIT" and ext == ".pdf":
                        created_pages = PDFWorker.split_pdf(p)
                        results.extend(created_pages)

                    elif target == "TRIM" and ext in CONFIG.MEDIA_EXTS:
                        out = cls.get_unique_path(p.parent / f"{p.stem}_trimmed{ext}")
                        MediaWorker.trim_media(p, out, "00:00:00", "00:00:15")
                        results.append(out.name)

                    elif target == "EXTRACT":
                        if ext == ".pdf":
                            out = cls.get_unique_path(p.with_suffix(".txt"))
                            PDFWorker.extract_text(p, out)
                            results.append(out.name)
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

            if target == "MERGE":
                if all(p.suffix.lower() == ".pdf" for p in paths) and len(paths) > 1:
                    out = cls.get_unique_path(paths[0].parent / f"{paths[0].stem}_merged.pdf")
                    PDFWorker.merge_pdfs(paths, out)
                    results.append(out.name)
                elif all(p.suffix.lower() in CONFIG.IMAGE_EXTS for p in paths) and len(paths) > 1:
                    out = cls.get_unique_path(paths[0].parent / f"{paths[0].stem}_merged.pdf")
                    PDFWorker.images_to_pdf(paths, out)
                    results.append(out.name)

        # ==========================================
        # 3. CTRL WHEEL: ACTIONS (Non-GUI-Dialog)
        # ==========================================
        elif mode == "ACTIONS":
            if target == "COPY PATH":
                results.append(ActionWorker.copy_path(file_paths))
            elif target == "TERMINAL":
                results.append(ActionWorker.open_terminal(file_paths[0]))
            elif target == "SHARE":
                out_zip = cls.get_unique_path(paths[0].parent / f"{paths[0].stem}_archive.zip")
                results.append(ActionWorker.zip_for_share(file_paths, out_zip))

        return results