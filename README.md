# PDF Local

An iLovePDF-style PDF toolkit that runs **100% on your own computer**. No file ever leaves your machine:

- The Flask server listens only on `127.0.0.1:5050` and rejects requests with any other `Host` header (DNS-rebinding protection).
- The interface loads nothing from the internet (no CDN). The `Content-Security-Policy` header only allows connections to the app itself.
- Almost everything is processed in memory. Office, LibreOffice and PDF→Word conversions use a temporary `pdftools_*` folder that is deleted when each operation finishes; leftovers from an abrupt shutdown are also removed at startup.

## Getting started

Requires Python 3.11+ on Windows (Office conversion uses Windows COM; everything else is cross-platform).

Double-click `start.bat`, or in PowerShell:

```powershell
cd path\to\pdf-tools
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Then open <http://127.0.0.1:5050>. To stop it, press `Ctrl+C` in the console window.

`start.bat` creates `.venv` and installs `requirements.txt` the first time it runs.

After changing the code, close the console window and start the app again.

- **Language:** the `EN` / `ES` button in the top bar switches the interface, error messages and downloaded file names between English and Spanish. The choice is remembered.
- **Console:** shows one line per operation (for example `Unir PDF  OK  0.3 s`) plus errors, not every file the browser requests.
- **Styles (Tailwind CSS v4):** written in `styles/input.css` and compiled to `static/app.css` with `build-css.bat` (use `build-css.bat --watch` while editing). See [Building the styles](#building-the-styles).
- **Caching:** the browser caches the interface's styles, scripts and icon; the page links them with a version (`?v=…`) that changes whenever they are edited. Your documents and API responses are never cached.

## Features

| Tool | Engine | External program? |
|---|---|---|
| Merge PDFs (drag to reorder) | PyMuPDF | No |
| Split: by ranges, every N pages, or selected pages | PyMuPDF | No |
| Organize: reorder, rotate and delete pages with thumbnails | PyMuPDF | No |
| Insert pages from another PDF or images at any position | PyMuPDF | No |
| Compress (3 levels, optional grayscale) | PyMuPDF | No |
| Images (JPG, PNG, WEBP, BMP, TIFF, GIF) to PDF | PyMuPDF + Pillow | No |
| PDF to images (JPG/PNG, 72–300 dpi) | PyMuPDF | No |
| PDF to Word (.docx) | pdf2docx | No |
| Watermark (text or image, centered or tiled) | PyMuPDF | No |
| Page numbers | PyMuPDF | No |
| Password protection (AES-256, permissions) | PyMuPDF | No |
| Remove password or restrictions | PyMuPDF | No |
| Word / Excel / PowerPoint / OpenDocument to PDF | Microsoft Office (COM) or LibreOffice | **Yes**: installed Office (auto-detected) or LibreOffice |
| OCR (scanned PDF → searchable PDF) | Tesseract via PyMuPDF | **Yes**: Tesseract |

### Installing the external programs (optional)

```powershell
winget install UB-Mannheim.TesseractOCR
```

During the Tesseract installation, select the languages you need under "Additional language data" (for example **Spanish**). Restart the app afterwards.

```powershell
winget install TheDocumentFoundation.LibreOffice
```

LibreOffice is only needed if Microsoft Office is not installed. With Office, conversion uses a hidden instance of Word, Excel or PowerPoint with macros disabled, and closes it when done.

## Building the styles

The app only needs the compiled `static/app.css`, which is included in the repository. You only need to rebuild it if you change the styles.

1. Download the official Tailwind CLI `tailwindcss-windows-x64.exe` v4.3.5 from the [Tailwind releases page](https://github.com/tailwindlabs/tailwindcss/releases/tag/v4.3.5). It is a standalone program, so Node.js is not needed.
2. Save it as `tools/tailwind/tailwindcss.exe`. The `tools/` folder is git-ignored because the binary is over 100 MB.
3. Run `build-css.bat` (or `build-css.bat --watch`).

Colors come from CSS variables exposed as Tailwind colors (`bg-surface`, `text-muted`, `border-line`…), so they switch automatically in dark mode.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe tests\make_samples.py
.\.venv\Scripts\python.exe tests\test_all.py
```

`make_samples.py` creates sample PDFs, images and Office files in `tests/samples`. `test_all.py` exercises every feature and writes the results to `tests/output`.

## License

This project depends on [PyMuPDF](https://pymupdf.readthedocs.io/), which is licensed under the GNU AGPL v3 (or a commercial license from Artifex). If you distribute this project, its license must be compatible with the AGPL.
