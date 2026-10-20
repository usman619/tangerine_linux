from pathlib import Path
from PIL import Image
from pypdf import PdfReader, PdfWriter


class PDFWorker:
    @staticmethod
    def merge_pdfs(paths: list[Path], out_path: Path) -> Path:
        writer = PdfWriter()
        for p in paths:
            writer.append(str(p))
        with open(out_path, "wb") as f:
            writer.write(f)
        return out_path

    @staticmethod
    def split_pdf(src: Path) -> list[str]:
        reader = PdfReader(str(src))
        created: list[str] = []
        for idx, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)
            out_file = src.parent / f"{src.stem}_page_{idx}.pdf"
            with open(out_file, "wb") as f:
                writer.write(f)
            created.append(out_file.name)
        return created

    @staticmethod
    def extract_text_and_images(src: Path, out_txt: Path) -> list[str]:
        reader = PdfReader(str(src))
        outputs: list[str] = []
        text_chunks = [page.extract_text() or "" for page in reader.pages]
        if any(text_chunks):
            out_txt.write_text("\n\n--- Page Break ---\n\n".join(text_chunks), encoding="utf-8")
            outputs.append(out_txt.name)

        # Also extract embedded images from PDF pages
        img_count = 0
        for p_idx, page in enumerate(reader.pages, start=1):
            for image_file_object in page.images:
                img_count += 1
                img_out = src.parent / f"{src.stem}_p{p_idx}_img{img_count}_{image_file_object.name}"
                img_out.write_bytes(image_file_object.data)
                outputs.append(img_out.name)
        return outputs

    @staticmethod
    def images_to_pdf(paths: list[Path], out_path: Path) -> Path:
        images = []
        for p in paths:
            img = Image.open(p)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            images.append(img)
        if images:
            images[0].save(out_path, save_all=True, append_images=images[1:])
        return out_path