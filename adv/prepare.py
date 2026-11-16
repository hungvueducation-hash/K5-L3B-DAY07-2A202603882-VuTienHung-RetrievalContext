"""Thử thách nâng cao — bước 1: tải/đọc PDF, trích text từng trang (pypdf) và dựng ảnh từng trang (pypdfium2).
Tài liệu: World Bank, "Viet Nam Rising: Pathways to a High-Income Future" (2025-07-23), CC BY-NC 3.0 IGO,
hdl.handle.net/10986/43481, 248 trang (bản tiếng Anh). PDF KHÔNG nằm trong repo; dùng download.sh để tải lại.
Dùng: python prepare.py <pdf> <out_dir>"""
import json, sys
from pathlib import Path
import pypdfium2 as pdfium
from pypdf import PdfReader

pdf, out = Path(sys.argv[1]), Path(sys.argv[2])
(out / "img").mkdir(parents=True, exist_ok=True)
reader = PdfReader(str(pdf))
doc = pdfium.PdfDocument(str(pdf))
with open(out / "pages.jsonl", "w", encoding="utf8") as f:
    for i in range(len(reader.pages)):
        text = (reader.pages[i].extract_text() or "").strip()
        page = doc[i]
        img = page.render(scale=1.4).to_pil().convert("RGB")
        img.save(out / "img" / f"p{i+1:03d}.jpg", quality=72)
        f.write(json.dumps({"page": i + 1, "text": text, "n_chars": len(text)}, ensure_ascii=False) + "\n")
print("pages", len(reader.pages))
