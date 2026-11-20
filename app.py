#PDF Local (Flask + PyMuPDF).

from __future__ import annotations

import base64
import glob
import io
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import zipfile
import zlib
from pathlib import Path

import pymupdf
from flask import Flask, Response, abort, g, jsonify, request, send_file, send_from_directory

HOST = "127.0.0.1"
PORT = int(os.environ.get("PDF_TOOLS_PORT", "5050"))
BASE = Path(__file__).resolve().parent
TMP_PREFIX = "pdftools_"

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024  # 1 GB
log = logging.getLogger("pdf-tools")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
# El registro de Werkzeug anota cada archivo que pide el navegador; solo mostramos avisos y errores.
logging.getLogger("werkzeug").setLevel(logging.WARNING)

OFFICE_LOCK = threading.Lock()
WORD_EXT = {".doc", ".docx", ".docm", ".odt", ".rtf", ".txt"}
EXCEL_EXT = {".xls", ".xlsx", ".xlsm", ".ods", ".csv"}
PPT_EXT = {".ppt", ".pptx", ".pptm", ".odp"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}


class UserError(Exception):
    """Error con mensaje legible para la interfaz."""


# Mensajes en inglés (la clave es la plantilla en español).
EN = {
    "No se recibió ningún archivo.": "No file was received.",
    "El archivo es demasiado grande (máximo 1 GB).": "The file is too large (1 GB max).",
    "Error inesperado: {e}": "Unexpected error: {e}",
    "«{name}» no es un PDF válido o está dañado.": "“{name}” is not a valid PDF or is damaged.",
    "«{name}» está protegido con contraseña. Usa «Desproteger PDF» primero.":
        "“{name}” is password-protected. Use “Remove password” first.",
    "«{name}» no tiene páginas.": "“{name}” has no pages.",
    "Indica las páginas o rangos, por ejemplo: 1-3, 5, 8-": "Enter pages or ranges, for example: 1-3, 5, 8-",
    "Rango no válido: «{part}». Usa formatos como 1-3, 5 o 8-": "Invalid range: “{part}”. Use formats like 1-3, 5 or 8-",
    "El rango «{part}» está fuera del documento (1-{n}).": "Range “{part}” is outside the document (1-{n}).",
    "Valor no válido para «{name}».": "Invalid value for “{name}”.",
    "Añade al menos dos PDF para unir.": "Add at least two PDFs to merge.",
    "Selección de páginas no válida.": "Invalid page selection.",
    "Selecciona al menos una página.": "Select at least one page.",
    "Modo de división desconocido.": "Unknown split mode.",
    "Lista de páginas no válida.": "Invalid page list.",
    "El documento resultante no puede quedar sin páginas.": "The resulting document cannot be empty.",
    "«{name}» no es un PDF ni una imagen compatible.": "“{name}” is not a PDF or a supported image.",
    "No hay páginas para insertar.": "There are no pages to insert.",
    "Se insertaron {count} página(s) al principio.": "Inserted {count} page(s) at the beginning.",
    "Se insertaron {count} página(s) después de la página {after}.": "Inserted {count} page(s) after page {after}.",
    "Nivel de compresión desconocido.": "Unknown compression level.",
    "El PDF ya estaba optimizado; se devuelve el original.": "The PDF was already optimized; the original is returned.",
    "El OCR necesita Tesseract instalado localmente (ver README).": "OCR needs Tesseract installed locally (see README).",
    "Tesseract no tiene idiomas instalados (carpeta tessdata vacía).": "Tesseract has no languages installed (empty tessdata folder).",
    "«{name}» no es una imagen válida.": "“{name}” is not a valid image.",
    "«{name}» no es una imagen compatible (JPG, PNG, WEBP, BMP, TIFF, GIF).":
        "“{name}” is not a supported image (JPG, PNG, WEBP, BMP, TIFF, GIF).",
    "Formato de Office no compatible.": "Unsupported Office format.",
    "Microsoft Office no pudo convertir el archivo (¿está protegido con contraseña o dañado?).":
        "Microsoft Office could not convert the file (is it password-protected or damaged?).",
    "LibreOffice tardó demasiado en convertir el archivo.": "LibreOffice took too long to convert the file.",
    "LibreOffice no pudo convertir el archivo.": "LibreOffice could not convert the file.",
    "LibreOffice no generó el PDF (¿archivo protegido o dañado?).": "LibreOffice did not produce the PDF (protected or damaged file?).",
    "Formato no compatible. Usa Word, Excel, PowerPoint u OpenDocument.":
        "Unsupported format. Use Word, Excel, PowerPoint or OpenDocument.",
    "No hay un programa local para esta conversión: instala LibreOffice o Microsoft {needed}.":
        "No local program for this conversion: install LibreOffice or Microsoft {needed}.",
    "Escribe un texto o elige una imagen para la marca de agua.": "Enter a text or choose an image for the watermark.",
    "Escribe una contraseña.": "Enter a password.",
    "Las contraseñas no coinciden.": "The passwords do not match.",
    "Este PDF no está protegido.": "This PDF is not protected.",
    "Escribe la contraseña del PDF.": "Enter the PDF password.",
    "Contraseña incorrecta.": "Wrong password.",
}

# Sufijos de los archivos descargados.
SUFFIX_EN = {
    "unido": "merged", "paginas": "pages", "dividido": "split", "organizado": "organized",
    "insertado": "inserted", "comprimido": "compressed", "ocr": "ocr", "pagina": "page",
    "imagenes": "images", "marca_agua": "watermark", "numerado": "numbered",
    "protegido": "protected", "desprotegido": "unprotected",
}


def is_en() -> bool:
    try:
        return request.headers.get("X-Lang", "es") == "en"
    except RuntimeError:  # fuera de una petición
        return False


def tr(template: str, **kw) -> str:
    """Devuelve el mensaje en el idioma de la interfaz (cabecera X-Lang)."""
    text = EN.get(template, template) if is_en() else template
    return text.format(**kw) if kw else text


def sfx(word: str) -> str:
    return SUFFIX_EN.get(word, word) if is_en() else word


# --------------------------------------------------------------------------- #
# Seguridad y utilidades
# --------------------------------------------------------------------------- #
ALLOWED_HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}


@app.before_request
def only_local_host():
    # Protección contra DNS rebinding: solo aceptar el host local.
    if request.host not in ALLOWED_HOSTS:
        abort(403)


@app.after_request
def security_headers(resp):
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data: blob:; style-src 'self'; "
        "script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; "
        "form-action 'self'; frame-ancestors 'none'"
    )
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    if request.path.startswith("/static/") and request.args.get("v") and resp.status_code == 200:
        # Archivos de la interfaz con versión en la URL: el navegador los guarda y no los vuelve a pedir.
        resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        resp.headers["Cache-Control"] = "no-store"  # páginas, API y documentos: nunca en caché
    return resp


OPERATIONS = {
    "/api/merge": "Unir PDF", "/api/split": "Dividir PDF", "/api/organize": "Organizar páginas",
    "/api/insert": "Insertar páginas", "/api/compress": "Comprimir", "/api/ocr": "OCR",
    "/api/images-to-pdf": "Imágenes a PDF", "/api/office-to-pdf": "Office a PDF",
    "/api/pdf-to-images": "PDF a imágenes", "/api/pdf-to-word": "PDF a Word",
    "/api/watermark": "Marca de agua", "/api/page-numbers": "Numerar páginas",
    "/api/protect": "Proteger", "/api/unprotect": "Quitar contraseña",
}


@app.before_request
def start_timer():
    g.t0 = time.perf_counter()


@app.after_request
def log_operation(resp):
    """Registra solo las operaciones (no cada archivo que carga el navegador)."""
    op = OPERATIONS.get(request.path)
    if op and request.method == "POST":
        secs = time.perf_counter() - g.get("t0", time.perf_counter())
        if resp.status_code < 400:
            log.info("%-18s OK     %.1f s  %s", op, secs, f"{resp.content_length or 0:,} bytes")
        else:
            log.info("%-18s ERROR  %.1f s  %s", op, secs, (resp.get_json(silent=True) or {}).get("error", resp.status))
    return resp


@app.errorhandler(UserError)
def handle_user_error(e):
    return jsonify(error=str(e)), 400


@app.errorhandler(413)
def handle_too_big(_e):
    return jsonify(error=tr("El archivo es demasiado grande (máximo 1 GB).")), 413


@app.errorhandler(Exception)
def handle_unexpected(e):
    if hasattr(e, "code") and hasattr(e, "description"):  # errores HTTP de Werkzeug
        return jsonify(error=e.description), e.code
    log.exception("Error inesperado")
    return jsonify(error=tr("Error inesperado: {e}", e=e)), 500


def new_tmpdir() -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(prefix=TMP_PREFIX, ignore_cleanup_errors=True)


def cleanup_stale_tmp():
    """Borra carpetas temporales que hayan quedado de una ejecución interrumpida."""
    for d in glob.glob(os.path.join(tempfile.gettempdir(), TMP_PREFIX + "*")):
        shutil.rmtree(d, ignore_errors=True)


def stem_of(filename: str | None, default="documento") -> str:
    name = Path(filename or default).stem
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "_", name).strip(" .")
    return name[:120] or default


def get_file(field="file"):
    f = request.files.get(field)
    if not f or not f.filename:
        raise UserError(tr("No se recibió ningún archivo."))
    return f


def get_files(field="files"):
    files = [f for f in request.files.getlist(field) if f and f.filename]
    if not files:
        raise UserError(tr("No se recibió ningún archivo."))
    return files


def open_pdf(data: bytes, name="archivo", allow_encrypted=False) -> pymupdf.Document:
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception:
        raise UserError(tr("«{name}» no es un PDF válido o está dañado.", name=name))
    if not doc.is_pdf:
        doc.close()
        raise UserError(tr("«{name}» no es un PDF válido o está dañado.", name=name))
    if doc.needs_pass and not allow_encrypted:
        pw = request.form.get("password", "")
        if not pw or not doc.authenticate(pw):
            doc.close()
            raise UserError(tr("«{name}» está protegido con contraseña. Usa «Desproteger PDF» primero.", name=name))
    if doc.page_count == 0:
        raise UserError(tr("«{name}» no tiene páginas.", name=name))
    return doc


def pdf_bytes(doc: pymupdf.Document, **kw) -> bytes:
    opts = dict(garbage=3, deflate=True)
    opts.update(kw)
    return doc.tobytes(**opts)


def send_bytes(data: bytes, filename: str, mimetype: str, headers: dict | None = None):
    resp = send_file(io.BytesIO(data), mimetype=mimetype, as_attachment=True,
                     download_name=filename, max_age=0)
    resp.headers["X-Filename"] = base64.b64encode(filename.encode()).decode()
    for k, v in (headers or {}).items():
        resp.headers[k] = str(v)
    resp.headers["Access-Control-Expose-Headers"] = "X-Filename, X-Original-Size, X-Result-Size, X-Note"
    return resp


def send_pdf(doc_or_bytes, filename, headers=None):
    data = doc_or_bytes if isinstance(doc_or_bytes, bytes) else pdf_bytes(doc_or_bytes)
    return send_bytes(data, filename, "application/pdf", headers)


def send_zip(entries: list[tuple[str, bytes]], filename: str):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in entries:
            z.writestr(name, data)
    return send_bytes(buf.getvalue(), filename, "application/zip")


def parse_ranges(text: str, n: int) -> list[list[int]]:
    """'1-3, 5, 8-' -> [[0,1,2],[4],[7..n-1]] (índices base 0)."""
    text = (text or "").replace(" ", "").replace(";", ",")
    if not text:
        raise UserError(tr("Indica las páginas o rangos, por ejemplo: 1-3, 5, 8-"))
    out = []
    for part in filter(None, text.split(",")):
        m = re.fullmatch(r"(\d*)-(\d*)|(\d+)", part)
        if not m:
            raise UserError(tr("Rango no válido: «{part}». Usa formatos como 1-3, 5 o 8-", part=part))
        if m.group(3):
            a = b = int(m.group(3))
        else:
            a = int(m.group(1)) if m.group(1) else 1
            b = int(m.group(2)) if m.group(2) else n
        if a < 1 or b > n or a > b:
            raise UserError(tr("El rango «{part}» está fuera del documento (1-{n}).", part=part, n=n))
        out.append(list(range(a - 1, b)))
    return out


def form_int(name, default, lo=None, hi=None):
    try:
        v = int(float(request.form.get(name, default)))
    except ValueError:
        raise UserError(tr("Valor no válido para «{name}».", name=name))
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


def form_bool(name):
    return request.form.get(name, "").lower() in {"1", "true", "on", "si", "sí"}


def hex_color(s: str, default=(0.8, 0.1, 0.1)):
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", s or "")
    if not m:
        return default
    h = m.group(1)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def overlay(page: pymupdf.Page, stamp: pymupdf.Document, pno: int = 0):
    """Superpone la página `stamp[pno]` (con el tamaño visual de `page`) respetando la rotación."""
    rot = page.rotation
    target = page.rect * page.derotation_matrix  # rect visual -> coordenadas sin rotar
    page.show_pdf_page(target.normalize(), stamp, pno, overlay=True, rotate=rot, keep_proportion=False)


# --------------------------------------------------------------------------- #
# Herramientas externas (detección)
# --------------------------------------------------------------------------- #
def find_libreoffice():
    cands = [shutil.which("soffice"), shutil.which("soffice.exe")]
    for pf in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)")):
        if pf:
            cands.append(os.path.join(pf, "LibreOffice", "program", "soffice.exe"))
    return next((c for c in cands if c and os.path.isfile(c)), None)


def find_tesseract():
    cands = [shutil.which("tesseract")]
    for pf in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
               os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
        if pf:
            cands.append(os.path.join(pf, "Tesseract-OCR", "tesseract.exe"))
    exe = next((c for c in cands if c and os.path.isfile(c)), None)
    if not exe:
        return None, None, []
    tessdata = os.environ.get("TESSDATA_PREFIX") or os.path.join(os.path.dirname(exe), "tessdata")
    langs = sorted(Path(p).stem for p in glob.glob(os.path.join(tessdata, "*.traineddata")))
    return exe, tessdata, langs


def office_apps():
    """Qué aplicaciones de Microsoft Office están registradas (COM)."""
    try:
        import winreg
    except ImportError:
        return set()
    found = set()
    for prog in ("Word.Application", "Excel.Application", "PowerPoint.Application"):
        try:
            winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, prog + "\\CLSID"))
            found.add(prog.split(".")[0])
        except OSError:
            pass
    return found


def status_info():
    lo = find_libreoffice()
    tess, tessdata, langs = find_tesseract()
    return {
        "libreoffice": bool(lo),
        "msoffice": sorted(office_apps()),
        "tesseract": bool(tess),
        "tesseract_langs": [l for l in langs if l != "osd"],
    }


# --------------------------------------------------------------------------- #
# Rutas: interfaz
# --------------------------------------------------------------------------- #
def static_version() -> str:
    """Huella de los archivos de la interfaz: cambia en cuanto se edita alguno."""
    files = sorted((BASE / "static").glob("*.*"))
    sig = "|".join(f"{f.name}:{f.stat().st_mtime_ns}:{f.stat().st_size}" for f in files)
    return format(zlib.crc32(sig.encode()), "08x")


@app.get("/")
def index():
    html = (BASE / "static" / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'"(/static/[\w.-]+)"', rf'"\1?v={static_version()}"', html)
    return Response(html, mimetype="text/html")


@app.get("/static/<path:p>")
def static_files(p):
    return send_from_directory(BASE / "static", p)


@app.get("/api/status")
def api_status():
    return jsonify(status_info())


@app.post("/api/thumbs")
def api_thumbs():
    """Devuelve miniaturas (JPEG en base64) generadas en memoria; no se guarda nada."""
    f = get_file()
    width = form_int("width", 180, 60, 400)
    limit = form_int("max", 2000, 1, 5000)
    doc = open_pdf(f.read(), f.filename)
    pages = []
    for i, page in enumerate(doc):
        if i >= limit:
            break
        zoom = width / max(page.rect.width, 1)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
        pages.append({
            "w": round(page.rect.width), "h": round(page.rect.height),
            "img": "data:image/jpeg;base64," + base64.b64encode(pix.tobytes("jpeg", jpg_quality=70)).decode(),
        })
    count = doc.page_count
    doc.close()
    return jsonify(count=count, pages=pages)


# --------------------------------------------------------------------------- #
# Rutas: organizar
# --------------------------------------------------------------------------- #
@app.post("/api/merge")
def api_merge():
    files = get_files()
    if len(files) < 2:
        raise UserError(tr("Añade al menos dos PDF para unir."))
    out = pymupdf.open()
    for f in files:
        src = open_pdf(f.read(), f.filename)
        out.insert_pdf(src)
        src.close()
    return send_pdf(out, f"{stem_of(files[0].filename)}_{sfx('unido')}.pdf")


@app.post("/api/split")
def api_split():
    f = get_file()
    stem = stem_of(f.filename)
    doc = open_pdf(f.read(), f.filename)
    n = doc.page_count
    mode = request.form.get("mode", "ranges")

    if mode == "ranges":
        groups = parse_ranges(request.form.get("ranges", ""), n)
    elif mode == "every":
        k = form_int("every", 1, 1, n)
        groups = [list(range(i, min(i + k, n))) for i in range(0, n, k)]
    elif mode == "select":
        try:
            sel = sorted({int(x) for x in json.loads(request.form.get("pages", "[]"))})
        except (ValueError, TypeError):
            raise UserError(tr("Selección de páginas no válida."))
        if not sel or sel[0] < 0 or sel[-1] >= n:
            raise UserError(tr("Selecciona al menos una página."))
        groups = [[p] for p in sel] if form_bool("separate") else [sel]
    else:
        raise UserError(tr("Modo de división desconocido."))

    def build(pages):
        out = pymupdf.open()
        for p in pages:
            out.insert_pdf(doc, from_page=p, to_page=p)
        return pdf_bytes(out)

    def label(pages):
        return f"{pages[0] + 1}" if len(pages) == 1 else f"{pages[0] + 1}-{pages[-1] + 1}"

    if form_bool("single") and mode != "every":  # todos los rangos en un único PDF
        groups = [[p for g in groups for p in g]]
    if len(groups) == 1:
        return send_pdf(build(groups[0]), f"{stem}_{sfx('paginas')}_{label(groups[0])}.pdf")
    entries = [(f"{stem}_{i + 1:02d}_{sfx('paginas')}_{label(g)}.pdf", build(g)) for i, g in enumerate(groups)]
    return send_zip(entries, f"{stem}_{sfx('dividido')}.zip")


@app.post("/api/organize")
def api_organize():
    """Recibe la lista final de páginas [{i: índice original, r: rotación extra}]."""
    f = get_file()
    doc = open_pdf(f.read(), f.filename)
    try:
        spec = json.loads(request.form.get("pages", "[]"))
        spec = [(int(p["i"]), int(p.get("r", 0)) % 360) for p in spec]
    except (ValueError, TypeError, KeyError):
        raise UserError(tr("Lista de páginas no válida."))
    if not spec:
        raise UserError(tr("El documento resultante no puede quedar sin páginas."))
    out = pymupdf.open()
    for i, rot in spec:
        if not 0 <= i < doc.page_count or rot % 90:
            raise UserError(tr("Lista de páginas no válida."))
        out.insert_pdf(doc, from_page=i, to_page=i)
        pg = out[-1]
        pg.set_rotation((pg.rotation + rot) % 360)
    return send_pdf(out, f"{stem_of(f.filename)}_{sfx('organizado')}.pdf")


@app.post("/api/insert")
def api_insert():
    """Inserta páginas de otros PDF (o imágenes) después de la página `after` del PDF base."""
    f = get_file()
    base = open_pdf(f.read(), f.filename)
    n = base.page_count
    after = form_int("after", n, 0, n)
    extras = get_files("insert")
    rng = request.form.get("ranges", "").strip()

    add = pymupdf.open()
    for x in extras:
        ext = Path(x.filename).suffix.lower()
        if ext == ".pdf":
            src = open_pdf(x.read(), x.filename)
            pages = [p for g in parse_ranges(rng, src.page_count) for p in g] if rng else range(src.page_count)
            for p in pages:
                add.insert_pdf(src, from_page=p, to_page=p)
            src.close()
        elif ext in IMG_EXT:
            data = load_image_bytes(x)
            ref = base[max(after - 1, 0)].rect  # mismo tamaño que la página vecina
            img = pymupdf.open(stream=data)
            ir = img[0].rect
            img.close()
            w, h = ref.width, ref.height
            if (ir.width > ir.height) != (w > h):
                w, h = h, w
            page = add.new_page(width=w, height=h)
            page.insert_image(pymupdf.Rect(20, 20, w - 20, h - 20), stream=data, keep_proportion=True)
        else:
            raise UserError(tr("«{name}» no es un PDF ni una imagen compatible.", name=x.filename))
    if add.page_count == 0:
        raise UserError(tr("No hay páginas para insertar."))
    count = add.page_count
    base.insert_pdf(add, start_at=after)
    if after == 0:
        note = tr("Se insertaron {count} página(s) al principio.", count=count)
    else:
        note = tr("Se insertaron {count} página(s) después de la página {after}.", count=count, after=after)
    return send_pdf(base, f"{stem_of(f.filename)}_{sfx('insertado')}.pdf",
                    {"X-Note": base64.b64encode(note.encode()).decode()})


# --------------------------------------------------------------------------- #
# Rutas: optimizar
# --------------------------------------------------------------------------- #
COMPRESS_LEVELS = {
    "baja": dict(dpi_threshold=300, dpi_target=220, quality=85),
    "media": dict(dpi_threshold=180, dpi_target=150, quality=70),
    "alta": dict(dpi_threshold=110, dpi_target=96, quality=50),
}


@app.post("/api/compress")
def api_compress():
    f = get_file()
    data = f.read()
    level = request.form.get("level", "media")
    if level not in COMPRESS_LEVELS:
        raise UserError(tr("Nivel de compresión desconocido."))
    doc = open_pdf(data, f.filename)
    if form_bool("gray"):
        doc.rewrite_images(**COMPRESS_LEVELS[level], set_to_gray=True)
    else:
        doc.rewrite_images(**COMPRESS_LEVELS[level])
    try:
        doc.subset_fonts()
    except Exception:  # algunas fuentes no se pueden reducir; no es grave
        pass
    result = doc.tobytes(garbage=4, deflate=True, deflate_images=True, deflate_fonts=True,
                         clean=True, use_objstms=1)
    note = ""
    if len(result) >= len(data):
        result, note = data, tr("El PDF ya estaba optimizado; se devuelve el original.")
    return send_pdf(result, f"{stem_of(f.filename)}_{sfx('comprimido')}.pdf",
                    {"X-Original-Size": len(data), "X-Result-Size": len(result),
                     "X-Note": base64.b64encode(note.encode()).decode()})


@app.post("/api/ocr")
def api_ocr():
    exe, tessdata, langs = find_tesseract()
    if not exe:
        raise UserError(tr("El OCR necesita Tesseract instalado localmente (ver README)."))
    f = get_file()
    doc = open_pdf(f.read(), f.filename)
    want = request.form.get("lang", "spa+eng")
    use = [l for l in want.split("+") if l in langs] or [l for l in langs if l != "osd"][:1]
    if not use:
        raise UserError(tr("Tesseract no tiene idiomas instalados (carpeta tessdata vacía)."))
    dpi = form_int("dpi", 300, 150, 400)
    skip_text = form_bool("skip_text")
    os.environ.setdefault("TESSDATA_PREFIX", tessdata)
    out = pymupdf.open()
    for page in doc:
        if skip_text and page.get_text().strip():
            out.insert_pdf(doc, from_page=page.number, to_page=page.number)
            continue
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        ocr = pymupdf.open("pdf", pix.pdfocr_tobytes(compress=True, language="+".join(use), tessdata=tessdata))
        # devolver la página al tamaño original
        ocr_page = ocr[0]
        ocr_page.set_mediabox(pymupdf.Rect(0, 0, ocr_page.rect.width, ocr_page.rect.height))
        tmp = out.new_page(width=page.rect.width, height=page.rect.height)
        tmp.show_pdf_page(tmp.rect, ocr, 0)
        ocr.close()
    return send_pdf(out, f"{stem_of(f.filename)}_ocr.pdf")


# --------------------------------------------------------------------------- #
# Rutas: convertir a PDF
# --------------------------------------------------------------------------- #
PAGE_SIZES = {"a4": pymupdf.paper_rect("a4"), "carta": pymupdf.paper_rect("letter")}


def load_image_bytes(f) -> bytes:
    """Aplica la orientación EXIF (fotos de móvil) solo si hace falta."""
    from PIL import Image, ImageOps
    data = f.read()
    try:
        im = Image.open(io.BytesIO(data))
        orient = im.getexif().get(0x0112, 1)
        fmt = im.format
        if orient not in (1, None) or fmt not in {"JPEG", "PNG"}:
            im = ImageOps.exif_transpose(im)
            if fmt == "GIF" or im.mode in ("P", "LA", "PA"):
                im = im.convert("RGBA")
            buf = io.BytesIO()
            if fmt == "JPEG" and im.mode in ("RGB", "L", "CMYK"):
                im.save(buf, "JPEG", quality=95)
            else:
                im.save(buf, "PNG")
            data = buf.getvalue()
    except Exception:
        raise UserError(tr("«{name}» no es una imagen válida.", name=f.filename))
    return data


@app.post("/api/images-to-pdf")
def api_images_to_pdf():
    files = get_files()
    size = request.form.get("size", "fit")
    orient = request.form.get("orientation", "auto")
    margin = {"none": 0, "small": 20, "large": 50}.get(request.form.get("margin", "none"), 0)
    out = pymupdf.open()
    for f in files:
        if Path(f.filename).suffix.lower() not in IMG_EXT:
            raise UserError(tr("«{name}» no es una imagen compatible (JPG, PNG, WEBP, BMP, TIFF, GIF).", name=f.filename))
        data = load_image_bytes(f)
        img = pymupdf.open(stream=data)
        r = img[0].rect
        img.close()
        if size in PAGE_SIZES:
            pr = PAGE_SIZES[size]
            w, h = pr.width, pr.height
            landscape = (orient == "horizontal") or (orient == "auto" and r.width > r.height)
            if landscape:
                w, h = h, w
        else:
            w, h = r.width + 2 * margin, r.height + 2 * margin
        page = out.new_page(width=w, height=h)
        page.insert_image(pymupdf.Rect(margin, margin, w - margin, h - margin), stream=data, keep_proportion=True)
    return send_pdf(out, f"{stem_of(files[0].filename)}.pdf")


def convert_with_msoffice(src: Path, outdir: Path) -> Path:
    import pythoncom
    import win32com.client

    ext = src.suffix.lower()
    out = outdir / (src.stem + ".pdf")
    with OFFICE_LOCK:
        pythoncom.CoInitialize()
        app_ = None
        try:
            if ext in WORD_EXT:
                app_ = win32com.client.DispatchEx("Word.Application")
                app_.Visible = False
                app_.DisplayAlerts = 0
                app_.AutomationSecurity = 3  # deshabilitar macros
                d = app_.Documents.Open(str(src), ConfirmConversions=False, ReadOnly=True,
                                        AddToRecentFiles=False, PasswordDocument="__sin_clave__",
                                        Visible=False)
                try:
                    d.ExportAsFixedFormat(str(out), 17)  # wdExportFormatPDF
                finally:
                    d.Close(0)
            elif ext in EXCEL_EXT:
                app_ = win32com.client.DispatchEx("Excel.Application")
                app_.Visible = False
                app_.DisplayAlerts = False
                app_.AutomationSecurity = 3
                wb = app_.Workbooks.Open(str(src), UpdateLinks=0, ReadOnly=True,
                                         Password="__sin_clave__", AddToMru=False)
                try:
                    wb.ExportAsFixedFormat(0, str(out))  # xlTypePDF
                finally:
                    wb.Close(False)
            elif ext in PPT_EXT:
                app_ = win32com.client.DispatchEx("PowerPoint.Application")
                app_.AutomationSecurity = 3
                pres = app_.Presentations.Open(str(src), ReadOnly=True, Untitled=False, WithWindow=False)
                try:
                    pres.SaveAs(str(out), 32)  # ppSaveAsPDF
                finally:
                    pres.Close()
            else:
                raise UserError(tr("Formato de Office no compatible."))
        except UserError:
            raise
        except Exception as e:
            log.warning("Fallo de Office: %s", e)
            raise UserError(tr("Microsoft Office no pudo convertir el archivo (¿está protegido con contraseña o dañado?)."))
        finally:
            if app_ is not None:
                try:
                    app_.Quit()
                except Exception:
                    pass
            app_ = None
            pythoncom.CoUninitialize()
    return out


def convert_with_libreoffice(soffice: str, src: Path, outdir: Path) -> Path:
    profile = (outdir / "lo_profile").as_uri()
    try:
        subprocess.run([soffice, f"-env:UserInstallation={profile}", "--headless", "--norestore",
                        "--convert-to", "pdf", "--outdir", str(outdir), str(src)],
                       check=True, timeout=300, capture_output=True)
    except subprocess.TimeoutExpired:
        raise UserError(tr("LibreOffice tardó demasiado en convertir el archivo."))
    except subprocess.CalledProcessError:
        raise UserError(tr("LibreOffice no pudo convertir el archivo."))
    out = outdir / (src.stem + ".pdf")
    if not out.exists():
        raise UserError(tr("LibreOffice no generó el PDF (¿archivo protegido o dañado?)."))
    return out


@app.post("/api/office-to-pdf")
def api_office_to_pdf():
    f = get_file()
    ext = Path(f.filename).suffix.lower()
    if ext not in WORD_EXT | EXCEL_EXT | PPT_EXT:
        raise UserError(tr("Formato no compatible. Usa Word, Excel, PowerPoint u OpenDocument."))
    engine = request.form.get("engine", "auto")
    apps = office_apps()
    needed = "Word" if ext in WORD_EXT else "Excel" if ext in EXCEL_EXT else "PowerPoint"
    soffice = find_libreoffice()
    use_ms = needed in apps and engine in ("auto", "msoffice")
    use_lo = soffice and engine in ("auto", "libreoffice") and not use_ms
    if not (use_ms or use_lo):
        raise UserError(tr("No hay un programa local para esta conversión: instala LibreOffice o Microsoft {needed}.",
                           needed=needed))
    with new_tmpdir() as td:
        td = Path(td)
        src = td / ("entrada" + ext)
        f.save(src)
        out = convert_with_msoffice(src, td) if use_ms else convert_with_libreoffice(soffice, src, td)
        data = out.read_bytes()
    return send_pdf(data, f"{stem_of(f.filename)}.pdf")


# --------------------------------------------------------------------------- #
# Rutas: convertir desde PDF
# --------------------------------------------------------------------------- #
@app.post("/api/pdf-to-images")
def api_pdf_to_images():
    f = get_file()
    stem = stem_of(f.filename)
    doc = open_pdf(f.read(), f.filename)
    fmt = "jpg" if request.form.get("format") == "jpg" else "png"
    dpi = form_int("dpi", 150, 36, 600)
    rng = request.form.get("ranges", "").strip()
    pages = [p for g in parse_ranges(rng, doc.page_count) for p in g] if rng else range(doc.page_count)
    entries = []
    for p in pages:
        pix = doc[p].get_pixmap(dpi=dpi, alpha=False)
        data = pix.tobytes("jpeg", jpg_quality=90) if fmt == "jpg" else pix.tobytes("png")
        entries.append((f"{stem}_{sfx('pagina')}_{p + 1:03d}.{fmt}", data))
    if len(entries) == 1:
        return send_bytes(entries[0][1], entries[0][0], "image/jpeg" if fmt == "jpg" else "image/png")
    return send_zip(entries, f"{stem}_{sfx('imagenes')}.zip")


@app.post("/api/pdf-to-word")
def api_pdf_to_word():
    from pdf2docx import Converter

    f = get_file()
    data = f.read()
    open_pdf(data, f.filename).close()  # valida (y rechaza PDFs protegidos)
    with new_tmpdir() as td:
        src, dst = Path(td) / "entrada.pdf", Path(td) / "salida.docx"
        src.write_bytes(data)
        cv = Converter(str(src))
        try:
            cv.convert(str(dst))
        finally:
            cv.close()
        out = dst.read_bytes()
    return send_bytes(out, f"{stem_of(f.filename)}.docx",
                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# --------------------------------------------------------------------------- #
# Rutas: editar
# --------------------------------------------------------------------------- #
@app.post("/api/watermark")
def api_watermark():
    f = get_file()
    doc = open_pdf(f.read(), f.filename)
    text = request.form.get("text", "").strip()
    img_file = request.files.get("image")
    has_img = bool(img_file and img_file.filename)
    if not text and not has_img:
        raise UserError(tr("Escribe un texto o elige una imagen para la marca de agua."))
    opacity = form_int("opacity", 30, 5, 100) / 100
    size = form_int("size", 60, 8, 300)
    angle = form_int("angle", 45, -180, 180)
    color = hex_color(request.form.get("color", "#cc2222"))
    mosaic = request.form.get("layout", "center") == "mosaic"
    img_data = load_image_bytes(img_file) if has_img else None
    scale_img = form_int("img_scale", 40, 5, 100) / 100

    cache: dict[tuple, pymupdf.Document] = {}

    def make_stamp(w, h):
        key = (round(w), round(h))
        if key in cache:
            return cache[key]
        sd = pymupdf.open()
        sp = sd.new_page(width=w, height=h)
        centers = [(w / 2, h / 2)]
        if mosaic:
            step_x, step_y = max(w / 3, size * 4), max(h / 4, size * 3)
            centers = [(x, y) for y in frange(step_y / 2, h, step_y) for x in frange(step_x / 2, w, step_x)]
        for cx, cy in centers:
            if img_data:
                im = pymupdf.open(stream=img_data)
                ir = im[0].rect
                im.close()
                k = min(w * scale_img / ir.width, h * scale_img / ir.height)
                if mosaic:
                    k /= 2.5
                iw, ih = ir.width * k, ir.height * k
                sp.insert_image(pymupdf.Rect(cx - iw / 2, cy - ih / 2, cx + iw / 2, cy + ih / 2),
                                stream=img_data, rotate=0, overlay=True)
            else:
                fs = size * (0.6 if mosaic else 1)
                tw = pymupdf.get_text_length(text, fontname="helv", fontsize=fs)
                sp.insert_text((cx - tw / 2, cy + fs * 0.35), text, fontsize=fs, fontname="helv",
                               color=color, fill_opacity=opacity,
                               morph=(pymupdf.Point(cx, cy), pymupdf.Matrix(angle)))
        if img_data and opacity < 1:
            # aplicar transparencia a las imágenes mediante un estado gráfico
            set_page_opacity(sd, sp, opacity)
        cache[key] = sd
        return sd

    for page in doc:
        overlay(page, make_stamp(page.rect.width, page.rect.height))
    return send_pdf(doc, f"{stem_of(f.filename)}_{sfx('marca_agua')}.pdf")


def frange(start, stop, step):
    v = start
    while v < stop:
        yield v
        v += step


def set_page_opacity(doc, page, alpha):
    """Envuelve el contenido de la página en un ExtGState con opacidad."""
    page.clean_contents()
    xref = page.get_contents()[0]
    content = doc.xref_stream(xref)
    gs = doc.get_new_xref()
    doc.update_object(gs, f"<</Type/ExtGState/ca {alpha:.3f}/CA {alpha:.3f}>>")
    res = doc.xref_get_key(page.xref, "Resources")
    if res[0] == "xref":
        rxref = int(res[1].split()[0])
        doc.xref_set_key(rxref, "ExtGState/GSwm", f"{gs} 0 R")
    else:
        doc.xref_set_key(page.xref, "Resources/ExtGState/GSwm", f"{gs} 0 R")
    doc.update_stream(xref, b"q /GSwm gs\n" + content + b"\nQ")


POSITIONS = {
    "bottom-center": ("b", "c"), "bottom-right": ("b", "r"), "bottom-left": ("b", "l"),
    "top-center": ("t", "c"), "top-right": ("t", "r"), "top-left": ("t", "l"),
}


@app.post("/api/page-numbers")
def api_page_numbers():
    f = get_file()
    doc = open_pdf(f.read(), f.filename)
    pos = POSITIONS.get(request.form.get("position", "bottom-center"), ("b", "c"))
    fmt = request.form.get("format", "{n}") or "{n}"
    if "{n}" not in fmt:
        fmt = fmt + " {n}"
    start = form_int("start", 1, -9999, 99999)
    fs = form_int("size", 11, 6, 48)
    margin = form_int("margin", 28, 5, 150)
    skip_first = form_bool("skip_first")
    color = hex_color(request.form.get("color", "#000000"), (0, 0, 0))
    numbered = [p for p in range(doc.page_count) if not (skip_first and p == 0)]
    total = len(numbered)
    for idx, pno in enumerate(numbered):
        page = doc[pno]
        w, h = page.rect.width, page.rect.height
        label = fmt.replace("{n}", str(start + idx)).replace("{total}", str(start + total - 1))
        tw = pymupdf.get_text_length(label, fontname="helv", fontsize=fs)
        x = {"l": margin, "c": (w - tw) / 2, "r": w - margin - tw}[pos[1]]
        y = margin + fs if pos[0] == "t" else h - margin
        sd = pymupdf.open()
        sp = sd.new_page(width=w, height=h)
        sp.insert_text((x, y), label, fontsize=fs, fontname="helv", color=color)
        overlay(page, sd)
        sd.close()
    return send_pdf(doc, f"{stem_of(f.filename)}_{sfx('numerado')}.pdf")


@app.post("/api/protect")
def api_protect():
    f = get_file()
    doc = open_pdf(f.read(), f.filename)
    pw = request.form.get("user_pw", "")
    if len(pw) < 1:
        raise UserError(tr("Escribe una contraseña."))
    if pw != request.form.get("user_pw2", pw):
        raise UserError(tr("Las contraseñas no coinciden."))
    owner = request.form.get("owner_pw", "") or base64.urlsafe_b64encode(os.urandom(18)).decode()
    perm = pymupdf.PDF_PERM_ACCESSIBILITY
    if form_bool("allow_print"):
        perm |= pymupdf.PDF_PERM_PRINT | pymupdf.PDF_PERM_PRINT_HQ
    if form_bool("allow_copy"):
        perm |= pymupdf.PDF_PERM_COPY
    if form_bool("allow_edit"):
        perm |= pymupdf.PDF_PERM_MODIFY | pymupdf.PDF_PERM_ANNOTATE | pymupdf.PDF_PERM_FORM | pymupdf.PDF_PERM_ASSEMBLE
    data = pdf_bytes(doc, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw=pw, owner_pw=owner,
                     permissions=perm)
    return send_pdf(data, f"{stem_of(f.filename)}_{sfx('protegido')}.pdf")


@app.post("/api/unprotect")
def api_unprotect():
    f = get_file()
    doc = open_pdf(f.read(), f.filename, allow_encrypted=True)
    if not doc.is_encrypted and not doc.needs_pass:
        raise UserError(tr("Este PDF no está protegido."))
    if doc.needs_pass:
        pw = request.form.get("password", "")
        if not pw:
            raise UserError(tr("Escribe la contraseña del PDF."))
        if not doc.authenticate(pw):
            raise UserError(tr("Contraseña incorrecta."))
    data = pdf_bytes(doc, encryption=pymupdf.PDF_ENCRYPT_NONE)
    return send_pdf(data, f"{stem_of(f.filename)}_{sfx('desprotegido')}.pdf")


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    cleanup_stale_tmp()
    st = status_info()
    log.info("Programas locales -> LibreOffice: %s | Microsoft Office: %s | Tesseract: %s %s",
             "sí" if st["libreoffice"] else "no", ", ".join(st["msoffice"]) or "no",
             "sí" if st["tesseract"] else "no", st["tesseract_langs"])
    print(f"\n  PDF Local listo en  http://{HOST}:{PORT}\n  (Ctrl+C para detener)\n")
    from werkzeug.serving import run_simple
    run_simple(HOST, PORT, app, threaded=True, use_reloader=False)
