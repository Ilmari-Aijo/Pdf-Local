"""Genera archivos de ejemplo en tests/samples (PDF, imágenes, Word, Excel, PowerPoint)."""
import io
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "samples"
OUT.mkdir(exist_ok=True)


def text_pdf(name, pages, title):
    doc = pymupdf.open()
    for i in range(pages):
        p = doc.new_page()
        p.insert_text((72, 100), f"{title} — página {i + 1} de {pages}", fontsize=22)
        p.insert_text((72, 140), "Texto de prueba con acentos: áéíóú ñ ¿? ¡!", fontsize=12)
        p.draw_rect(pymupdf.Rect(72, 200, 300, 400), color=(0, 0, 1), fill=(0.8, 0.9, 1))
        p.insert_text((90, 300), f"P{i + 1}", fontsize=60)
    doc[1].set_rotation(90) if pages > 1 else None
    doc.save(OUT / name)


def photo_pdf(name):
    """PDF con imágenes grandes (para probar la compresión)."""
    doc = pymupdf.open()
    for k in range(3):
        im = Image.effect_noise((2400, 3200), 60).convert("RGB")
        d = ImageDraw.Draw(im)
        for j in range(0, 3200, 80):
            d.line([(0, j), (2400, 3200 - j)], fill=(j % 255, 80 * k % 255, 200), width=12)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=95)
        p = doc.new_page()
        p.insert_image(p.rect, stream=buf.getvalue())
    doc.save(OUT / name)


def images():
    for i, (size, col) in enumerate([((800, 600), "tomato"), ((600, 900), "seagreen")]):
        im = Image.new("RGB", size, col)
        ImageDraw.Draw(im).text((40, 40), f"Imagen {i + 1}", fill="white")
        im.save(OUT / f"imagen{i + 1}.{'jpg' if i == 0 else 'png'}")


def scanned_pdf(name):
    """PDF «escaneado»: solo una imagen con texto, sin capa de texto."""
    src = pymupdf.open()
    p = src.new_page()
    p.insert_text((72, 120), "Factura numero 12345", fontsize=28)
    p.insert_text((72, 180), "Cliente: Maria Lopez - Lima Peru", fontsize=20)
    pix = p.get_pixmap(dpi=200)
    doc = pymupdf.open()
    q = doc.new_page()
    q.insert_image(q.rect, stream=pix.tobytes("png"))
    doc.save(OUT / name, deflate=True, garbage=3)


def office():
    try:
        import docx
        d = docx.Document()
        d.add_heading("Documento de prueba", 0)
        d.add_paragraph("Hola desde Word. Acentos: canción, año, pingüino.")
        t = d.add_table(rows=2, cols=2)
        t.cell(0, 0).text, t.cell(1, 1).text = "A1", "B2"
        d.save(OUT / "documento.docx")
    except ImportError:
        print("python-docx no disponible")
    try:
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Producto", "Precio"])
        for i in range(1, 20):
            ws.append([f"Artículo {i}", i * 3.5])
        wb.save(OUT / "hoja.xlsx")
    except ImportError:
        print("openpyxl no disponible")
    try:
        from pptx import Presentation
        pr = Presentation()
        for i in range(2):
            s = pr.slides.add_slide(pr.slide_layouts[1])
            s.shapes.title.text = f"Diapositiva {i + 1}"
            s.placeholders[1].text = "Contenido de prueba"
        pr.save(OUT / "presentacion.pptx")
    except ImportError:
        print("python-pptx no disponible")


if __name__ == "__main__":
    text_pdf("texto6.pdf", 6, "Documento A")
    text_pdf("texto3.pdf", 3, "Documento B")
    photo_pdf("fotos.pdf")
    scanned_pdf("escaneado.pdf")
    images()
    office()
    for f in sorted(OUT.iterdir()):
        print(f"{f.name:22} {f.stat().st_size:>10,} bytes")
