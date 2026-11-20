"""Prueba cada función con los archivos de tests/samples (ejecuta antes make_samples.py).

Uso:  .venv\\Scripts\\python.exe tests\\test_all.py
Los resultados quedan en tests/output para revisarlos a mano.
"""
import glob
import io
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import app as appmod  # noqa: E402

S = ROOT / "tests" / "samples"
O = ROOT / "tests" / "output"
O.mkdir(exist_ok=True)
client = appmod.app.test_client()
BASE = f"http://127.0.0.1:{appmod.PORT}"
results = []


def post(url, files=None, **form):
    data = dict(form)
    for field, paths in (files or {}).items():
        paths = paths if isinstance(paths, list) else [paths]
        data[field] = [(open(S / p, "rb"), p) for p in paths]
    return client.post(BASE + url, data=data, content_type="multipart/form-data")


def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'OK ' if cond else 'FALLO'}] {name} {detail}")


def pdf_of(resp):
    return pymupdf.open(stream=resp.data, filetype="pdf")


def save(resp, name):
    (O / name).write_bytes(resp.data)


def tmp_left():
    return glob.glob(os.path.join(tempfile.gettempdir(), appmod.TMP_PREFIX + "*"))


# --- seguridad básica
r = client.get("http://evil.example:5050/")
check("rechaza Host externo", r.status_code == 403)
r = client.get(BASE + "/")
check("sirve la interfaz", r.status_code == 200 and b"<html" in r.data.lower())
check("cabecera CSP", "default-src 'self'" in r.headers.get("Content-Security-Policy", ""))
m = __import__("re").search(r'/static/app\.js\?v=(\w+)', r.get_data(as_text=True))
check("la página enlaza la interfaz con versión", bool(m))
r = client.get(BASE + f"/static/app.js?v={m.group(1)}")
check("archivos de la interfaz se guardan en caché", "immutable" in r.headers.get("Cache-Control", ""))
r = client.post(BASE + "/api/merge", data={}, content_type="multipart/form-data")
check("la API nunca se guarda en caché", r.headers.get("Cache-Control") == "no-store")
r = client.post(BASE + "/api/merge", data={}, content_type="multipart/form-data", headers={"X-Lang": "en"})
check("errores en inglés con X-Lang: en", r.get_json()["error"] == "No file was received.", r.get_json()["error"])
st = client.get(BASE + "/api/status").get_json()
print("   estado:", st)

# --- miniaturas
r = post("/api/thumbs", {"file": "texto6.pdf"})
j = r.get_json()
check("miniaturas", r.status_code == 200 and j["count"] == 6 and j["pages"][0]["img"].startswith("data:image/jpeg"))

# --- unir
r = post("/api/merge", {"files": ["texto3.pdf", "texto6.pdf"]})
d = pdf_of(r); save(r, "unido.pdf")
check("unir (orden B luego A)", d.page_count == 9 and "Documento B" in d[0].get_text() and "Documento A" in d[3].get_text())

data = {"files": [(open(S / "texto3.pdf", "rb"), "a.pdf"), (open(S / "texto3.pdf", "rb"), "b.pdf")]}
r = client.post(BASE + "/api/merge", data=data, content_type="multipart/form-data", headers={"X-Lang": "en"})
check("nombre del archivo en inglés", "a_merged.pdf" in r.headers.get("Content-Disposition", ""), r.headers.get("Content-Disposition"))

# --- dividir
r = post("/api/split", {"file": "texto6.pdf"}, mode="ranges", ranges="1-2, 4, 5-")
z = zipfile.ZipFile(io.BytesIO(r.data)); save(r, "dividido.zip")
counts = [pymupdf.open(stream=z.read(n), filetype="pdf").page_count for n in z.namelist()]
check("dividir por rangos -> zip", counts == [2, 1, 2], str(counts))
r = post("/api/split", {"file": "texto6.pdf"}, mode="ranges", ranges="1-2, 6", single="1")
d = pdf_of(r)
check("rangos en un solo PDF", d.page_count == 3 and "página 6" in d[2].get_text())
r = post("/api/split", {"file": "texto6.pdf"}, mode="every", every="4")
z = zipfile.ZipFile(io.BytesIO(r.data))
check("dividir cada 4 páginas", len(z.namelist()) == 2)
r = post("/api/split", {"file": "texto6.pdf"}, mode="select", pages="[4, 0]")
d = pdf_of(r)
check("extraer páginas 1 y 5", d.page_count == 2 and "página 5" in d[1].get_text())
r = post("/api/split", {"file": "texto6.pdf"}, mode="ranges", ranges="3-9")
check("rango fuera de límites -> error", r.status_code == 400, r.get_json()["error"])

# --- organizar
spec = [{"i": 5, "r": 0}, {"i": 0, "r": 90}, {"i": 2, "r": 180}]
r = post("/api/organize", {"file": "texto6.pdf"}, pages=json.dumps(spec))
d = pdf_of(r); save(r, "organizado.pdf")
check("reordenar/rotar/eliminar", d.page_count == 3 and "página 6" in d[0].get_text()
      and d[1].rotation == 90 and d[2].rotation == 180, f"rot={[p.rotation for p in d]}")

# --- insertar
r = post("/api/insert", {"file": "texto6.pdf", "insert": "texto3.pdf"}, after="2", ranges="1-2")
d = pdf_of(r); save(r, "insertado.pdf")
txt = [d[i].get_text() for i in range(d.page_count)]
check("insertar 2 páginas después de la 2", d.page_count == 8 and "Documento A · página 2 de" in txt[1]
      and "Documento B · página 1 de" in txt[2] and "Documento B · página 2 de" in txt[3]
      and "Documento A · página 3 de" in txt[4], f"{d.page_count} pág.")
r = post("/api/insert", {"file": "texto3.pdf", "insert": ["imagen1.jpg", "imagen2.png"]}, after="0")
d = pdf_of(r)
check("insertar imágenes al principio", d.page_count == 5 and not d[0].get_text().strip()
      and "Documento B · página 1 de" in d[2].get_text())
r = post("/api/insert", {"file": "texto3.pdf", "insert": "texto6.pdf"}, after="99")
d = pdf_of(r)
check("insertar con posición mayor que el total va al final", d.page_count == 9 and "Documento A" in d[3].get_text())

# --- comprimir
orig = (S / "fotos.pdf").stat().st_size
for lvl in ("baja", "media", "alta"):
    r = post("/api/compress", {"file": "fotos.pdf"}, level=lvl)
    new = int(r.headers["X-Result-Size"])
    save(r, f"comprimido_{lvl}.pdf")
    check(f"comprimir ({lvl})", r.status_code == 200 and new < orig and pdf_of(r).page_count == 3,
          f"{orig:,} -> {new:,} bytes ({100 - new * 100 // orig}% menos)")
r = post("/api/compress", {"file": "texto3.pdf"}, level="media")
check("comprimir PDF ya pequeño no lo agranda", int(r.headers["X-Result-Size"]) <= (S / "texto3.pdf").stat().st_size)

# --- imágenes a PDF
r = post("/api/images-to-pdf", {"files": ["imagen1.jpg", "imagen2.png"]}, size="a4", margin="small")
d = pdf_of(r); save(r, "imagenes.pdf")
check("imágenes a PDF (A4, auto orientación)", d.page_count == 2 and d[0].rect.width > d[0].rect.height
      and d[1].rect.width < d[1].rect.height)
r = post("/api/images-to-pdf", {"files": ["imagen1.jpg"]}, size="fit")
d = pdf_of(r)
check("imagen a PDF (tamaño original)", d.page_count == 1 and abs(d[0].rect.width / d[0].rect.height - 800 / 600) < 0.01)

# --- Office a PDF
for fn, needed in (("documento.docx", "Word"), ("hoja.xlsx", "Excel"), ("presentacion.pptx", "PowerPoint")):
    if not (S / fn).exists():
        continue
    if needed not in st["msoffice"] and not st["libreoffice"]:
        print(f"   (omitido {fn}: no hay Office ni LibreOffice)")
        continue
    r = post("/api/office-to-pdf", {"file": fn})
    ok = r.status_code == 200 and r.data[:4] == b"%PDF"
    if ok:
        save(r, fn + ".pdf")
        d = pdf_of(r)
        detail = f"{d.page_count} pág."
    else:
        detail = str(r.get_json())
    check(f"{needed} a PDF", ok, detail)

# --- PDF a imágenes
r = post("/api/pdf-to-images", {"file": "texto6.pdf"}, format="png", dpi="100")
z = zipfile.ZipFile(io.BytesIO(r.data)); save(r, "imagenes.zip")
check("PDF a PNG (zip)", len(z.namelist()) == 6 and z.read(z.namelist()[0])[:4] == b"\x89PNG")
r = post("/api/pdf-to-images", {"file": "texto6.pdf"}, format="jpg", dpi="72", ranges="3")
check("PDF a JPG (una página)", r.data[:2] == b"\xff\xd8" and r.mimetype == "image/jpeg")

# --- PDF a Word
r = post("/api/pdf-to-word", {"file": "texto3.pdf"})
save(r, "texto3.docx")
ok = r.status_code == 200
if ok:
    import docx
    txt = "\n".join(p.text for p in docx.Document(io.BytesIO(r.data)).paragraphs)
    ok = "Documento B" in txt
check("PDF a Word", ok)

# --- marca de agua
r = post("/api/watermark", {"file": "texto6.pdf"}, text="CONFIDENCIAL ñ", opacity="30", size="60", angle="45")
d = pdf_of(r); save(r, "marca_agua.pdf")
check("marca de agua (texto)", "CONFIDENCIAL" in d[0].get_text() and "CONFIDENCIAL" in d[1].get_text())
r = post("/api/watermark", {"file": "texto3.pdf", "image": "imagen1.jpg"}, layout="mosaic", opacity="40")
d = pdf_of(r); save(r, "marca_agua_imagen.pdf")
check("marca de agua (imagen, mosaico)", r.status_code == 200 and d.page_count == 3, str(r.status_code))

# --- numerar
r = post("/api/page-numbers", {"file": "texto6.pdf"}, format="Página {n} de {total}", position="bottom-right")
d = pdf_of(r); save(r, "numerado.pdf")
check("numerar páginas", "Página 1 de 6" in d[0].get_text() and "Página 2 de 6" in d[1].get_text())

# --- proteger / desproteger
r = post("/api/protect", {"file": "texto3.pdf"}, user_pw="secreta123", allow_print="1")
(S / "_protegido.pdf").write_bytes(r.data); save(r, "protegido.pdf")
d = pdf_of(r)
check("proteger (AES-256)", d.needs_pass and not d.authenticate("mala") and d.authenticate("secreta123"))
r = post("/api/unprotect", {"file": "_protegido.pdf"}, password="mala")
check("desproteger con clave incorrecta -> error", r.status_code == 400, r.get_json()["error"])
r = post("/api/unprotect", {"file": "_protegido.pdf"}, password="secreta123")
d = pdf_of(r); save(r, "desprotegido.pdf")
check("desproteger", not d.needs_pass and not d.is_encrypted and d.page_count == 3)
r = post("/api/compress", {"file": "_protegido.pdf"})
check("otras herramientas avisan si está protegido", r.status_code == 400, r.get_json()["error"])
(S / "_protegido.pdf").unlink()

# --- OCR
if st["tesseract"]:
    r = post("/api/ocr", {"file": "escaneado.pdf"}, lang="spa+eng")
    d = pdf_of(r); save(r, "ocr.pdf")
    check("OCR", "12345" in d[0].get_text(), d[0].get_text()[:60].replace("\n", " "))
else:
    r = post("/api/ocr", {"file": "escaneado.pdf"})
    check("OCR sin Tesseract avisa", r.status_code == 400, r.get_json()["error"])

# --- errores
r = post("/api/merge", {"files": ["imagen1.jpg", "texto3.pdf"]})
check("archivo no PDF -> error claro", r.status_code == 400, r.get_json()["error"])

check("no quedan temporales", not tmp_left(), str(tmp_left()))

fails = [n for n, ok, _ in results if not ok]
print(f"\n{len(results) - len(fails)}/{len(results)} pruebas correctas")
sys.exit(1 if fails else 0)
