"use strict";
/* PDF Local — interfaz. Sin dependencias externas: todo se envía solo a 127.0.0.1. */

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtSize = (n) => n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(0)} KB` : `${(n / 1048576).toFixed(1)} MB`;
let uid = 0;
const nextId = () => `i${++uid}`;

/* ---------- iconos ---------- */
const P = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="${d}"/></svg>`;
const ICONS = {
  merge: P("M7 3h7l5 5v4h-2V9h-4V5H7v14h5v2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm10 11h2v3h3v2h-3v3h-2v-3h-3v-2h3v-3z"),
  split: P("M7 3h10a2 2 0 0 1 2 2v5h-2V5H7v5H5V5a2 2 0 0 1 2-2zM3 11h18v2H3v-2zm2 3h2v5h10v-5h2v5a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-5z"),
  organize: P("M3 3h8v8H3V3zm2 2v4h4V5H5zm8-2h8v8h-8V3zm2 2v4h4V5h-4zM3 13h8v8H3v-8zm2 2v4h4v-4H5zm11-2h2v3h3v2h-3v3h-2v-3h-3v-2h3v-3z"),
  insert: P("M6 2h8l6 6v6h-2V9h-5V4H6v16h7v2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm12 14h2v3h3v2h-3v3h-2v-3h-3v-2h3v-3z"),
  compress: P("M11 2h2v6l2.6-2.6L17 6.8 12 11.8 7 6.8l1.4-1.4L11 8V2zM4 11h16v2H4v-2zm8 1.2 5 5-1.4 1.4L13 16v6h-2v-6l-2.6 2.6L7 17.2l5-5z"),
  ocr: P("M3 3h5v2H5v3H3V3zm13 0h5v5h-2V5h-3V3zM3 16h2v3h3v2H3v-5zm16 0h2v5h-5v-2h3v-3zM7 8h10v2H7V8zm0 3h10v2H7v-2zm0 3h7v2H7v-2z"),
  image: P("M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2zm0 2v10.6l3.5-3.5 2.5 2.5 4.5-4.5L19 13.6V5H5zm3.5 1A1.5 1.5 0 1 1 8.5 9a1.5 1.5 0 0 1 0-3z"),
  office: P("M6 2h8l6 6v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm7 1.5V9h5.5L13 3.5zM7.2 12l1.3 6h1.4l1.1-4 1.1 4h1.4l1.3-6h-1.4l-.7 3.6-1-3.6h-1.4l-1 3.6-.7-3.6H7.2z"),
  toimg: P("M6 2h8l6 6v4h-2V9h-5V4H6v16h4v2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm7 12h8v8h-8v-8zm2 2v4h4v-4h-4z"),
  word: P("M6 2h8l6 6v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm7 1.5V9h5.5L13 3.5zM7 12h1.5l1 4.2 1.2-4.2h1.3l1.2 4.2 1-4.2h1.5l-1.8 6h-1.4L11.3 14l-1.2 4H8.8L7 12z"),
  watermark: P("M12 2c3 4.2 6 7.8 6 11.5A6 6 0 0 1 6 13.5C6 9.8 9 6.2 12 2zm0 3.6C10 8.5 8 11 8 13.5a4 4 0 0 0 8 0C16 11 14 8.5 12 5.6z"),
  numbers: P("M4 4h16v16H4V4zm2 2v12h12V6H6zm4.5 2H13v8h-2v-6h-1l.5-2zM9 17h6v1H9v-1z"),
  lock: P("M12 2a5 5 0 0 1 5 5v3h1a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h1V7a5 5 0 0 1 5-5zm0 2a3 3 0 0 0-3 3v3h6V7a3 3 0 0 0-3-3zm0 9a2 2 0 0 0-1 3.7V19h2v-2.3A2 2 0 0 0 12 13z"),
  unlock: P("M12 2a5 5 0 0 1 5 5h-2a3 3 0 0 0-6 0v3h9a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h1V7a5 5 0 0 1 5-5zm0 11a2 2 0 0 0-1 3.7V19h2v-2.3A2 2 0 0 0 12 13z"),
};

/* ---------- idioma ---------- */
let LANG = "es";
try { LANG = localStorage.getItem("pdf-idioma") === "en" ? "en" : "es"; } catch (e) { /* sin almacenamiento */ }
const T = (es, en) => (LANG === "en" ? en : es);
const plural = (n, es1, esN, en1, enN) => `${n} ${n === 1 ? T(es1, en1) : T(esN, enN)}`;
const api = (url, opts = {}) => fetch(url, { ...opts, headers: { "X-Lang": LANG } });

// Textos fijos de index.html (atributo data-i18n).
const STATIC = {
  badge: ["100 % local", "100% local"],
  badgeTitle: ["Ningún archivo sale de tu computadora", "No file ever leaves your computer"],
  theme: ["Cambiar tema", "Toggle theme"],
  lang: ["Switch to English", "Cambiar a español"],
  heroTitle: ["Herramientas PDF en tu computadora", "PDF tools on your computer"],
  heroText: ["Une, divide, comprime, convierte y protege tus PDF. LOCAL", "Merge, split, compress, convert and protect your PDFs. LOCAL"],
  back: ["← Todas las herramientas", "← All tools"],
  orDrag: ["o arrástralos aquí", "or drag them here"],
  reset: ["Empezar de nuevo", "Start over"],
  processing: ["Procesando…", "Processing…"],
  footer: ["PyMuPDF · Servidor solo en 127.0.0.1", "PyMuPDF · Server on 127.0.0.1 only"],
};

function applyStatic() {
  document.documentElement.lang = LANG;
  document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = T(...STATIC[n.dataset.i18n]); });
  document.querySelectorAll("[data-i18n-title]").forEach((n) => {
    const txt = T(...STATIC[n.dataset.i18nTitle]);
    n.title = txt; n.setAttribute("aria-label", txt);
  });
  $("#langBtn").textContent = LANG === "en" ? "ES" : "EN";
}

/* ---------- helpers de formulario ---------- */
const field = (label, inner, help = "", cls = "", when = "") =>
  `<label class="field ${cls}"${when ? ` data-when="${when}"` : ""}><span>${label}</span>${inner}${help ? `<small>${help}</small>` : ""}</label>`;
const seg = (name, opts, checked) =>
  `<div class="seg" role="radiogroup">${opts.map(([v, l]) =>
    `<label><input type="radio" name="${name}" value="${v}"${v === checked ? " checked" : ""}><span>${l}</span></label>`).join("")}</div>`;
const segField = (label, name, opts, checked, cls = "wide", when = "") =>
  `<div class="field ${cls}"${when ? ` data-when="${when}"` : ""}><span>${label}</span>${seg(name, opts, checked)}</div>`;
const check = (name, label, on = false, when = "") =>
  `<label class="check"${when ? ` data-when="${when}"` : ""}><input type="checkbox" name="${name}" value="1"${on ? " checked" : ""}> ${label}</label>`;
const range = (name, min, max, val, unit = "") =>
  `<div class="flex items-center gap-2.5"><input type="range" name="${name}" min="${min}" max="${max}" value="${val}" data-out="${name}"><output id="o_${name}" class="min-w-[3.5em]">${val}${unit}</output></div>`;
const opt = (v, label, sel = false) => `<option value="${esc(v)}"${sel ? " selected" : ""}>${label}</option>`;

const OFFICE_EXT = ".doc,.docx,.docm,.odt,.rtf,.txt,.xls,.xlsx,.xlsm,.ods,.csv,.ppt,.pptx,.pptm,.odp";
const IMG_EXT = ".jpg,.jpeg,.png,.webp,.bmp,.tif,.tiff,.gif";

/* ---------- definición de herramientas (se regenera al cambiar de idioma) ---------- */
function buildTools() {
  const G = { org: T("Organizar", "Organize"), opt: T("Optimizar", "Optimize"),
    to: T("Convertir a PDF", "Convert to PDF"), from: T("Convertir desde PDF", "Convert from PDF"),
    edit: T("Editar y seguridad", "Edit & security") };
  return [
    { id: "unir", group: G.org, icon: "merge", title: T("Unir PDF", "Merge PDF"), kind: "files", accept: ".pdf", min: 2,
      desc: T("Combina varios PDF en uno. Arrastra las miniaturas para cambiar el orden.",
        "Combine several PDFs into one. Drag the thumbnails to change the order."),
      endpoint: "/api/merge", button: T("Unir PDF", "Merge PDF") },
    { id: "dividir", group: G.org, icon: "split", title: T("Dividir PDF", "Split PDF"), kind: "pages", mode: "split", accept: ".pdf",
      desc: T("Separa por rangos, cada N páginas o extrae las páginas que elijas.",
        "Split by ranges, every N pages, or extract the pages you choose."),
      endpoint: "/api/split", button: T("Dividir PDF", "Split PDF"),
      options: () =>
        segField(T("Modo", "Mode"), "mode", [["ranges", T("Por rangos", "By ranges")], ["every", T("Cada N páginas", "Every N pages")],
          ["select", T("Elegir páginas", "Pick pages")]], "ranges") +
        field(T("Rangos de páginas", "Page ranges"), `<input type="text" name="ranges" placeholder="${T("Ej.: 1-3, 5, 8-", "E.g.: 1-3, 5, 8-")}">`,
          T("Cada rango genera un PDF. «8-» significa de la 8 al final.", "Each range becomes a PDF. “8-” means from 8 to the end."), "", "mode:ranges") +
        field(T("Páginas por archivo", "Pages per file"), `<input type="number" name="every" min="1" value="1">`, "", "", "mode:every") +
        check("single", T("Juntar todos los rangos en un único PDF", "Put all ranges into a single PDF"), false, "mode:ranges") +
        `<p class="m-0 text-muted" data-when="mode:select">${T("Toca las miniaturas para seleccionarlas.", "Tap the thumbnails to select them.")}</p>` +
        check("separate", T("Guardar cada página seleccionada como PDF aparte", "Save each selected page as a separate PDF"), false, "mode:select") },
    { id: "insertar", group: G.org, icon: "insert", title: T("Insertar páginas", "Insert pages"), kind: "pages", mode: "insert", accept: ".pdf",
      desc: T("Mete páginas de otro PDF (o imágenes) en la posición exacta que elijas.",
        "Add pages from another PDF (or images) at the exact position you choose."),
      endpoint: "/api/insert", button: T("Insertar páginas", "Insert pages"),
      options: () =>
        field(T("Páginas a insertar", "Pages to insert"), `<input type="file" name="insert" accept=".pdf,${IMG_EXT}" multiple>`,
          T("Un PDF o varias imágenes. Se insertan en el orden elegido.", "A PDF or several images, inserted in the order chosen."), "wide") +
        field(T("Insertar después de la página", "Insert after page"), `<input type="number" name="after" value="2" min="0">`,
          T("0 = al principio. También puedes tocar una miniatura.", "0 = at the beginning. You can also tap a thumbnail.")) +
        field(T("Solo estas páginas del PDF a insertar (opcional)", "Only these pages of the inserted PDF (optional)"),
          `<input type="text" name="ranges" placeholder="${T("Todas · ej.: 1-2", "All · e.g.: 1-2")}">`),
      validate: (fd) => {
        if (!fd.getAll("insert").some((f) => f && f.size)) return T("Elige el PDF o las imágenes que quieres insertar.", "Choose the PDF or images you want to insert.");
      } },
    { id: "organizar", group: G.org, icon: "organize", title: T("Organizar páginas", "Organize pages"), kind: "pages", mode: "organize", accept: ".pdf",
      desc: T("Reordena arrastrando, gira o elimina páginas y guarda el resultado.",
        "Reorder by dragging, rotate or delete pages, and save the result."),
      endpoint: "/api/organize", button: T("Guardar cambios", "Save changes") },

    { id: "comprimir", group: G.opt, icon: "compress", title: T("Comprimir PDF", "Compress PDF"), kind: "single", accept: ".pdf",
      desc: T("Reduce el tamaño recomprimiendo imágenes y limpiando el archivo.", "Reduce file size by recompressing images and cleaning up the file."),
      endpoint: "/api/compress", button: T("Comprimir PDF", "Compress PDF"),
      options: () =>
        segField(T("Nivel de compresión", "Compression level"), "level", [["baja", T("Baja · máxima calidad", "Low · best quality")],
          ["media", T("Recomendada", "Recommended")], ["alta", T("Alta · menor tamaño", "High · smallest size")]], "media") +
        check("gray", T("Convertir imágenes a escala de grises", "Convert images to grayscale")) },
    { id: "ocr", group: G.opt, icon: "ocr", title: T("OCR (reconocer texto)", "OCR (recognize text)"), kind: "single", accept: ".pdf", needs: "tesseract",
      desc: T("Convierte un PDF escaneado en un PDF con texto que se puede buscar y copiar.",
        "Turn a scanned PDF into a PDF with searchable, copyable text."),
      endpoint: "/api/ocr", button: T("Aplicar OCR", "Run OCR"),
      options: () =>
        field(T("Idioma del documento", "Document language"), `<select name="lang" id="ocrLang"></select>`) +
        field(T("Resolución", "Resolution"), `<select name="dpi">${opt(200, T("200 ppp (rápido)", "200 dpi (fast)"))}${opt(300, T("300 ppp (recomendado)", "300 dpi (recommended)"), true)}${opt(400, T("400 ppp (texto pequeño)", "400 dpi (small text)"))}</select>`) +
        check("skip_text", T("Saltar páginas que ya tienen texto", "Skip pages that already have text"), true) },

    { id: "imagenes-a-pdf", group: G.to, icon: "image", title: T("Imágenes a PDF", "Images to PDF"), kind: "files", accept: IMG_EXT, images: true,
      desc: T("JPG, PNG, WEBP, TIFF… en un solo PDF, en el orden que elijas.", "JPG, PNG, WEBP, TIFF… into one PDF, in the order you choose."),
      endpoint: "/api/images-to-pdf", button: T("Crear PDF", "Create PDF"),
      options: () =>
        segField(T("Tamaño de página", "Page size"), "size", [["fit", T("Igual a la imagen", "Same as image")], ["a4", "A4"], ["carta", T("Carta", "Letter")]], "a4") +
        segField(T("Orientación", "Orientation"), "orientation", [["auto", T("Automática", "Automatic")], ["vertical", T("Vertical", "Portrait")],
          ["horizontal", T("Horizontal", "Landscape")]], "auto", "", "size:a4,carta") +
        segField(T("Margen", "Margin"), "margin", [["none", T("Sin margen", "No margin")], ["small", T("Pequeño", "Small")], ["large", T("Grande", "Large")]], "small", "") },
    { id: "office-a-pdf", group: G.to, icon: "office", title: T("Word, Excel o PowerPoint a PDF", "Word, Excel or PowerPoint to PDF"), kind: "single",
      accept: OFFICE_EXT, needs: "office", noThumb: true,
      desc: T("Convierte documentos de Office u OpenDocument usando programas instalados en tu equipo.",
        "Convert Office or OpenDocument files using programs installed on your computer."),
      endpoint: "/api/office-to-pdf", button: T("Convertir a PDF", "Convert to PDF"),
      options: () => field(T("Programa para convertir", "Program to convert with"), `<select name="engine" id="officeEngine"></select>`) },

    { id: "pdf-a-imagenes", group: G.from, icon: "toimg", title: T("PDF a imágenes", "PDF to images"), kind: "single", accept: ".pdf",
      desc: T("Exporta cada página como imagen JPG o PNG (en un ZIP si son varias).", "Export each page as a JPG or PNG image (in a ZIP if there are several)."),
      endpoint: "/api/pdf-to-images", button: T("Convertir a imágenes", "Convert to images"),
      options: () =>
        segField(T("Formato", "Format"), "format", [["jpg", "JPG"], ["png", "PNG"]], "jpg", "") +
        field(T("Calidad", "Quality"), `<select name="dpi">${opt(72, T("72 ppp · pantalla", "72 dpi · screen"))}${opt(150, T("150 ppp · normal", "150 dpi · normal"), true)}${opt(300, T("300 ppp · impresión", "300 dpi · print"))}</select>`) +
        field(T("Páginas (opcional)", "Pages (optional)"), `<input type="text" name="ranges" placeholder="${T("Todas · ej.: 1-3, 7", "All · e.g.: 1-3, 7")}">`) },
    { id: "pdf-a-word", group: G.from, icon: "word", title: T("PDF a Word", "PDF to Word"), kind: "single", accept: ".pdf",
      desc: T("Convierte a .docx editable (texto, tablas e imágenes). Funciona mejor con PDF digitales, no escaneados.",
        "Convert to an editable .docx (text, tables and images). Works best with digital PDFs, not scans."),
      endpoint: "/api/pdf-to-word", button: T("Convertir a Word", "Convert to Word") },

    { id: "marca-agua", group: G.edit, icon: "watermark", title: T("Marca de agua", "Watermark"), kind: "single", accept: ".pdf",
      desc: T("Añade un texto o una imagen sobre todas las páginas.", "Add a text or an image over every page."),
      endpoint: "/api/watermark", button: T("Añadir marca de agua", "Add watermark"),
      options: () =>
        segField(T("Tipo", "Type"), "wm_type", [["text", T("Texto", "Text")], ["image", T("Imagen", "Image")]], "text") +
        field(T("Texto", "Text"), `<input type="text" name="text" value="${T("CONFIDENCIAL", "CONFIDENTIAL")}" maxlength="200">`, "", "", "wm_type:text") +
        field(T("Imagen (logo)", "Image (logo)"), `<input type="file" name="image" accept="${IMG_EXT}">`, "", "", "wm_type:image") +
        field(T("Tamaño de letra", "Font size"), range("size", 12, 160, 60), "", "", "wm_type:text") +
        field(T("Tamaño de imagen", "Image size"), range("img_scale", 10, 100, 40, "%"), "", "", "wm_type:image") +
        field(T("Opacidad", "Opacity"), range("opacity", 5, 100, 30, "%")) +
        field(T("Ángulo", "Angle"), range("angle", -90, 90, 45, "°"), "", "", "wm_type:text") +
        field("Color", `<input type="color" name="color" value="#cc2222">`, "", "", "wm_type:text") +
        segField(T("Disposición", "Layout"), "layout", [["center", T("Centrada", "Centered")], ["mosaic", T("Mosaico", "Tiled")]], "center", "") },
    { id: "numerar", group: G.edit, icon: "numbers", title: T("Numerar páginas", "Number pages"), kind: "single", accept: ".pdf",
      desc: T("Añade números de página con el formato y la posición que prefieras.", "Add page numbers with the format and position you prefer."),
      endpoint: "/api/page-numbers", button: T("Numerar páginas", "Number pages"),
      options: () =>
        field(T("Posición", "Position"), `<select name="position">${[
          ["bottom-center", T("Abajo, centro", "Bottom center")], ["bottom-right", T("Abajo, derecha", "Bottom right")],
          ["bottom-left", T("Abajo, izquierda", "Bottom left")], ["top-center", T("Arriba, centro", "Top center")],
          ["top-right", T("Arriba, derecha", "Top right")], ["top-left", T("Arriba, izquierda", "Top left")],
        ].map(([v, l], i) => opt(v, l, i === 0)).join("")}</select>`) +
        field(T("Formato", "Format"), `<select name="format">${opt("{n}", "1")}${opt(T("Página {n}", "Page {n}"), T("Página 1", "Page 1"))}${opt(T("Página {n} de {total}", "Page {n} of {total}"), T("Página 1 de 10", "Page 1 of 10"))}${opt("{n} / {total}", "1 / 10")}${opt("- {n} -", "- 1 -")}</select>`) +
        field(T("Empezar en", "Start at"), `<input type="number" name="start" value="1">`) +
        field(T("Tamaño de letra", "Font size"), `<input type="number" name="size" value="11" min="6" max="48">`) +
        field("Color", `<input type="color" name="color" value="#000000">`) +
        check("skip_first", T("No numerar la primera página (portada)", "Don't number the first page (cover)")) },
    { id: "proteger", group: G.edit, icon: "lock", title: T("Proteger con contraseña", "Protect with password"), kind: "single", accept: ".pdf",
      desc: T("Cifra el PDF con AES-256: hará falta la contraseña para abrirlo.", "Encrypt the PDF with AES-256: the password will be needed to open it."),
      endpoint: "/api/protect", button: T("Proteger PDF", "Protect PDF"),
      options: () =>
        field(T("Contraseña", "Password"), `<input type="password" name="user_pw" autocomplete="new-password" required>`) +
        field(T("Repite la contraseña", "Repeat password"), `<input type="password" name="user_pw2" autocomplete="new-password" required>`) +
        `<div class="field wide"><span>${T("Permisos para quien abra el PDF", "Permissions for whoever opens the PDF")}</span>` +
        check("allow_print", T("Permitir imprimir", "Allow printing"), true) + check("allow_copy", T("Permitir copiar texto", "Allow copying text"), true) +
        check("allow_edit", T("Permitir modificar", "Allow editing"), false) + `</div>`,
      validate: (fd) => {
        if (!fd.get("user_pw")) return T("Escribe una contraseña.", "Enter a password.");
        if (fd.get("user_pw") !== fd.get("user_pw2")) return T("Las contraseñas no coinciden.", "The passwords do not match.");
      } },
    { id: "desproteger", group: G.edit, icon: "unlock", title: T("Quitar contraseña", "Remove password"), kind: "single", accept: ".pdf", noThumb: true,
      desc: T("Elimina la contraseña y las restricciones de un PDF del que conoces la clave.",
        "Remove the password and restrictions from a PDF whose password you know."),
      endpoint: "/api/unprotect", button: T("Desproteger PDF", "Unprotect PDF"),
      options: () => field(T("Contraseña actual", "Current password"), `<input type="password" name="password" autocomplete="current-password">`,
        T("Déjala vacía si el PDF se abre sin clave pero tiene restricciones.", "Leave empty if the PDF opens without a password but has restrictions.")) },
  ];
}
let TOOLS = buildTools();

/* ---------- estado ---------- */
const S = { tool: null, items: [], pages: [], file: null, status: null, resultUrl: null };
const el = {
  home: $("#home"), tool: $("#tool"), groups: $("#toolGroups"), icon: $("#toolIcon"), title: $("#toolTitle"),
  desc: $("#toolDesc"), notice: $("#toolNotice"), drop: $("#dropzone"), input: $("#fileInput"), dropLabel: $("#dropLabel"),
  work: $("#workArea"), toolbar: $("#workToolbar"), items: $("#items"), options: $("#options"),
  run: $("#runBtn"), reset: $("#resetBtn"), result: $("#result"), busy: $("#busy"), busyText: $("#busyText"),
};

/* ---------- tema e idioma ---------- */
$("#themeBtn").addEventListener("click", () => {
  const cur = document.documentElement.getAttribute("data-theme") ||
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const next = cur === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  try { localStorage.setItem("pdf-tema", next); } catch (e) { /* sin almacenamiento */ }
});

$("#langBtn").addEventListener("click", () => {
  LANG = LANG === "en" ? "es" : "en";
  try { localStorage.setItem("pdf-idioma", LANG); } catch (e) { /* sin almacenamiento */ }
  TOOLS = buildTools();
  applyStatic();
  renderHome();
  if (S.tool) refreshTool();
});

/* Vuelve a pintar la herramienta abierta en el nuevo idioma sin perder archivos ni opciones. */
function refreshTool() {
  S.tool = TOOLS.find((t) => t.id === S.tool.id);
  const saved = [...el.options.elements].filter((i) => i.name && i.type !== "file")
    .map((i) => [i.name, i.type, i.value, i.checked]);
  const files = [...el.options.querySelectorAll("input[type=file]")].map((i) => [i.name, i.files]);
  renderToolHeader();
  el.options.innerHTML = S.tool.options ? S.tool.options() : "";
  for (const [name, type, value, checked] of saved) {
    const inputs = [...el.options.querySelectorAll(`[name="${name}"]`)];
    if (type === "radio" || type === "checkbox") inputs.forEach((i) => { if (i.value === value) i.checked = checked; });
    else if (!inputs[0] || name === "format") continue; // el formato de numeración cambia con el idioma
    else if (name === "text" && ["CONFIDENCIAL", "CONFIDENTIAL"].includes(value)) continue; // texto por defecto traducido
    else inputs[0].value = value;
  }
  for (const [name, list] of files) { const i = el.options.querySelector(`[name="${name}"]`); if (i && list) i.files = list; }
  setupOptions();
  el.options.querySelectorAll("input[type=range]").forEach((r) => r.dispatchEvent(new Event("input")));
  renderNotice();
  el.result.hidden = true;
  if (S.tool.kind === "files" && S.items.length) renderFiles();
  else if (S.tool.kind === "pages" && S.pages.length) renderPages();
  else if (S.file) renderSingle();
}

/* ---------- inicio ---------- */
function renderHome() {
  const groups = [...new Set(TOOLS.map((t) => t.group))];
  el.groups.innerHTML = groups.map((g) => `<h2>${g}</h2><div class="tool-grid">${TOOLS.filter((t) => t.group === g).map((t) =>
    `<a class="tool-card" href="#${t.id}"><span class="tool-icon">${ICONS[t.icon]}</span>
      <span><strong>${t.title}${t.needs ? `<span class="tag-ext" data-needs="${t.needs}" hidden></span>` : ""}</strong>
      <span class="d">${t.desc}</span></span></a>`).join("")}</div>`).join("");
  updateNeedsTags();
}

function updateNeedsTags() {
  if (!S.status) return;
  document.querySelectorAll("[data-needs]").forEach((tag) => {
    const missing = tag.dataset.needs === "tesseract" ? !S.status.tesseract
      : !S.status.libreoffice && S.status.msoffice.length === 0;
    tag.textContent = tag.dataset.needs === "tesseract" ? T("requiere Tesseract", "needs Tesseract") : T("requiere Office/LibreOffice", "needs Office/LibreOffice");
    tag.hidden = !missing;
  });
}

async function loadStatus() {
  try {
    S.status = await (await api("/api/status")).json();
  } catch (e) {
    S.status = { libreoffice: false, msoffice: [], tesseract: false, tesseract_langs: [] };
  }
  updateNeedsTags();
  if (S.tool) renderNotice();
}

/* ---------- navegación ---------- */
function route() {
  const id = location.hash.slice(1);
  const tool = TOOLS.find((t) => t.id === id);
  if (!tool) {
    S.tool = null; resetWork();
    el.tool.hidden = true; el.home.hidden = false;
    document.title = "PDF Local";
    return;
  }
  S.tool = tool;
  el.home.hidden = true; el.tool.hidden = false;
  renderToolHeader();
  resetWork();
  renderNotice();
  scrollTo(0, 0);
}
addEventListener("hashchange", route);

function renderToolHeader() {
  const tool = S.tool;
  document.title = `${tool.title} · PDF Local`;
  el.icon.innerHTML = ICONS[tool.icon];
  el.title.textContent = tool.title;
  el.desc.textContent = tool.desc;
  el.input.accept = tool.accept;
  el.input.multiple = tool.kind === "files";
  el.dropLabel.textContent = tool.kind === "files" ? (tool.images ? T("Elige imágenes", "Choose images") : T("Elige archivos PDF", "Choose PDF files"))
    : tool.accept === ".pdf" ? T("Elige un archivo PDF", "Choose a PDF file") : T("Elige un documento", "Choose a document");
  el.run.textContent = tool.button;
}

function renderNotice() {
  const t = S.tool, st = S.status;
  let html = "";
  if (t.needs === "tesseract" && st) {
    html = st.tesseract
      ? `<div class="notice info">${T("Se usará Tesseract instalado en tu equipo. Idiomas disponibles:", "Tesseract installed on your computer will be used. Available languages:")} ${esc(st.tesseract_langs.join(", ") || T("ninguno", "none"))}.</div>`
      : `<div class="notice warn">${T(
        "<strong>Tesseract no está instalado.</strong> El OCR se hace en local con Tesseract (gratuito, sin internet una vez instalado). Instálalo con <code>winget install UB-Mannheim.TesseractOCR</code> y marca el idioma español durante la instalación; luego reinicia la app.",
        "<strong>Tesseract is not installed.</strong> OCR runs locally with Tesseract (free, no internet once installed). Install it with <code>winget install UB-Mannheim.TesseractOCR</code>, selecting the languages you need, then restart the app.")}</div>`;
  }
  if (t.needs === "office" && st) {
    const ms = st.msoffice;
    const progs = [ms.length ? `Microsoft Office (${esc(ms.join(", "))})` : "", st.libreoffice ? "LibreOffice" : ""].filter(Boolean).join(T(" o ", " or "));
    html = progs
      ? `<div class="notice info">${T(`Se convertirá con ${progs}, instalado en tu equipo. El archivo no sale de tu computadora.`,
        `It will be converted with ${progs}, installed on your computer. The file never leaves your computer.`)}</div>`
      : `<div class="notice warn">${T(
        "<strong>No hay Office ni LibreOffice.</strong> Instala LibreOffice (gratuito) con <code>winget install TheDocumentFoundation.LibreOffice</code> y reinicia la app.",
        "<strong>Neither Office nor LibreOffice is installed.</strong> Install LibreOffice (free) with <code>winget install TheDocumentFoundation.LibreOffice</code> and restart the app.")}</div>`;
  }
  el.notice.innerHTML = html;
}

/* ---------- área de trabajo ---------- */
function resetWork() {
  S.items.forEach((i) => i.objUrl && URL.revokeObjectURL(i.objUrl));
  S.items = []; S.pages = []; S.deleted = []; S.file = null;
  if (S.resultUrl) { URL.revokeObjectURL(S.resultUrl); S.resultUrl = null; }
  el.work.hidden = true; el.drop.hidden = false; el.drop.classList.remove("compact");
  el.items.innerHTML = ""; el.toolbar.innerHTML = ""; el.result.hidden = true; el.result.innerHTML = "";
  el.options.innerHTML = S.tool && S.tool.options ? S.tool.options() : "";
  el.input.value = "";
  if (S.tool) setupOptions();
}
el.reset.addEventListener("click", () => resetWork());

function setupOptions() {
  const t = S.tool;
  if (t.id === "ocr") {
    const sel = $("#ocrLang"), langs = (S.status && S.status.tesseract_langs) || [], prev = sel.value;
    const names = { spa: T("Español", "Spanish"), eng: T("Inglés", "English"), por: T("Portugués", "Portuguese"),
      fra: T("Francés", "French"), deu: T("Alemán", "German"), ita: T("Italiano", "Italian") };
    const opts = [];
    const both = T("Español + inglés", "Spanish + English");
    if (langs.includes("spa") && langs.includes("eng")) opts.push(["spa+eng", both]);
    langs.forEach((l) => opts.push([l, names[l] || l]));
    if (!opts.length) opts.push(["spa+eng", both]);
    sel.innerHTML = opts.map(([v, l]) => opt(v, esc(l), v === prev)).join("");
  }
  if (t.id === "office-a-pdf") {
    const st = S.status || { msoffice: [], libreoffice: false }, sel = $("#officeEngine"), prev = sel.value;
    const o = [["auto", T("Automático", "Automatic")]];
    if (st.msoffice.length) o.push(["msoffice", "Microsoft Office"]);
    if (st.libreoffice) o.push(["libreoffice", "LibreOffice"]);
    sel.innerHTML = o.map(([v, l]) => opt(v, l, v === prev)).join("");
  }
  el.options.querySelectorAll("input[type=range]").forEach((r) => {
    if (r.dataset.bound) return;
    r.dataset.bound = "1";
    const out = $(`#o_${r.dataset.out}`), unit = out.textContent.replace(/[-\d]/g, "");
    r.addEventListener("input", () => { out.textContent = r.value + unit; });
  });
  updateWhen();
}
el.options.addEventListener("change", () => { updateWhen(); if (S.tool && ["split", "insert"].includes(S.tool.mode) && S.pages.length) renderPages(); });
el.options.addEventListener("input", (e) => {
  if (e.target.name === "ranges" && S.tool.mode === "split") markRanges();
  if (e.target.name === "after" && S.pages.length) renderPages();
});
el.options.addEventListener("submit", (e) => e.preventDefault());

function updateWhen() {
  const fd = new FormData(el.options);
  el.options.querySelectorAll("[data-when]").forEach((n) => {
    const [k, vals] = n.dataset.when.split(":");
    n.hidden = !vals.split(",").includes(fd.get(k));
  });
}

/* ---------- carga de archivos ---------- */
el.input.addEventListener("change", () => { addFiles([...el.input.files]); el.input.value = ""; });
["dragenter", "dragover"].forEach((ev) => el.drop.addEventListener(ev, (e) => { e.preventDefault(); el.drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => el.drop.addEventListener(ev, () => el.drop.classList.remove("over")));
el.drop.addEventListener("drop", (e) => { e.preventDefault(); addFiles([...e.dataTransfer.files]); });
// Evitar que soltar un archivo fuera de la zona abra el archivo en el navegador.
addEventListener("dragover", (e) => e.preventDefault());
addEventListener("drop", (e) => e.preventDefault());

function accepts(file) {
  const ext = "." + file.name.split(".").pop().toLowerCase();
  return S.tool.accept.split(",").includes(ext);
}

async function addFiles(files) {
  const t = S.tool;
  const ok = files.filter(accepts), bad = files.filter((f) => !accepts(f));
  if (bad.length) showError(`${T("Formato no compatible:", "Unsupported format:")} ${bad.map((f) => f.name).join(", ")}`);
  if (!ok.length) return;
  el.result.hidden = true;
  if (t.kind === "files") {
    for (const f of ok) S.items.push({ id: nextId(), file: f, thumb: null, count: null });
    showWork();
    renderFiles();
    for (const it of S.items.filter((i) => !i.thumb && !i.failed)) {
      if (t.images) { it.objUrl = URL.createObjectURL(it.file); it.thumb = it.objUrl; renderFiles(); continue; }
      try {
        const j = await thumbs(it.file, 1, 160);
        it.thumb = j.pages[0].img; it.count = j.count;
      } catch (e) { it.failed = e.message; }
      renderFiles();
    }
    return;
  }
  // un solo archivo
  S.file = ok[0];
  showWork();
  if (t.kind === "pages") {
    busy(true, T("Generando miniaturas…", "Generating thumbnails…"));
    try {
      const j = await thumbs(S.file, 5000, 180);
      S.pages = j.pages.map((p, i) => ({ id: nextId(), i, r: 0, img: p.img, w: p.w, h: p.h, sel: false }));
    } catch (e) { busy(false); showError(e.message); resetWork(); return; }
    busy(false);
    renderPages();
  } else {
    renderSingle();
    if (!t.noThumb) {
      try { const j = await thumbs(S.file, 1, 120); S.file.thumb = j.pages[0].img; S.file.count = j.count; }
      catch (e) { S.file.err = e.message; }
      renderSingle();
    }
  }
}

function showWork() {
  el.work.hidden = false;
  if (S.tool.kind === "files") { el.drop.classList.add("compact"); }
  else { el.drop.hidden = true; }
}

async function thumbs(file, max, width) {
  const fd = new FormData();
  fd.append("file", file); fd.append("max", max); fd.append("width", width);
  const r = await api("/api/thumbs", { method: "POST", body: fd });
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || T("No se pudo leer el PDF.", "Could not read the PDF."));
  return j;
}

/* ---------- vistas de elementos ---------- */
// Clases de Tailwind para mostrar la miniatura girada (sin estilos en línea).
const ROT_CLASS = { 0: "", 90: "rotate-90 max-h-[96px] sm:max-h-[124px]", 180: "rotate-180", 270: "-rotate-90 max-h-[96px] sm:max-h-[124px]" };
function renderFiles() {
  el.items.className = "items";
  const n = S.items.length;
  el.toolbar.innerHTML = `<span class="info">${plural(n, "archivo", "archivos", "file", "files")} · ${T("arrastra para ordenar", "drag to reorder")}</span>
    <button type="button" class="btn ghost small" data-act="sort-name">${T("Ordenar por nombre", "Sort by name")}</button>`;
  el.items.innerHTML = S.items.map((it, k) => `<div class="card" data-id="${it.id}">
      <div class="thumb">${it.thumb ? `<img src="${it.thumb}" alt="">` : it.failed ? `<span class="p-2 text-center text-xs text-muted">${esc(it.failed)}</span>` : `<span class="spinner"></span>`}</div>
      <div class="meta"><span class="name" title="${esc(it.file.name)}">${k + 1}. ${esc(it.file.name)}</span>
      <button type="button" class="mini" data-act="remove" aria-label="${T("Quitar", "Remove")}">✕</button></div>
      <div class="text-xs text-muted">${fmtSize(it.file.size)}${it.count ? ` · ${it.count} ${T("pág.", "p.")}` : ""}</div></div>`).join("");
  el.run.disabled = n < (S.tool.min || 1) || S.items.some((i) => i.failed);
  if (n === 0) resetWork();
}

function renderSingle() {
  const f = S.file;
  el.items.className = "items single";
  el.toolbar.innerHTML = "";
  el.items.innerHTML = `<div class="card static">
    <div class="thumb">${f.thumb ? `<img src="${f.thumb}" alt="">` : S.tool.noThumb ? ICONS[S.tool.icon] : f.err ? "⚠" : `<span class="spinner"></span>`}</div>
    <div class="min-w-0"><strong class="break-all">${esc(f.name)}</strong>
    <div class="text-sm text-muted">${fmtSize(f.size)}${f.count ? ` · ${plural(f.count, "página", "páginas", "page", "pages")}` : ""}</div>
    ${f.err ? `<div class="text-sm text-err">${esc(f.err)}</div>` : ""}</div></div>`;
  el.run.disabled = !!f.err;
}

function splitMode() { return new FormData(el.options).get("mode"); }

function renderPages() {
  const t = S.tool, selMode = t.mode === "split" && splitMode() === "select";
  const nPages = plural(S.pages.length, "página", "páginas", "page", "pages");
  el.items.className = "items";
  if (t.mode === "organize") {
    el.toolbar.innerHTML = `<span class="info">${nPages} · ${T("arrastra para reordenar", "drag to reorder")}</span>
      <button type="button" class="btn ghost small" data-act="rot-all-l">⟲ ${T("Girar todas", "Rotate all")}</button>
      <button type="button" class="btn ghost small" data-act="rot-all-r">⟳ ${T("Girar todas", "Rotate all")}</button>
      <button type="button" class="btn ghost small" data-act="reverse">${T("Invertir orden", "Reverse order")}</button>
      <button type="button" class="btn ghost small" data-act="restore">${T("Restaurar", "Reset")}</button>`;
  } else if (t.mode === "insert") {
    const a = insertAfter();
    const where = a === 0 ? T("al principio", "at the beginning") : T(`después de la página ${a}`, `after page ${a}`);
    el.toolbar.innerHTML = `<span class="info">${esc(S.file.name)} · ${nPages} · ${T("las nuevas irán", "new pages go")} ${where}</span>
      <button type="button" class="btn ghost small" data-act="ins-start">${T("Al principio", "At the beginning")}</button>
      <button type="button" class="btn ghost small" data-act="ins-end">${T("Al final", "At the end")}</button>`;
  } else {
    const nsel = S.pages.filter((p) => p.sel).length;
    el.toolbar.innerHTML = `<span class="info">${esc(S.file.name)} · ${nPages}${selMode ? ` · ${plural(nsel, "seleccionada", "seleccionadas", "selected", "selected")}` : ""}</span>` +
      (selMode ? `<button type="button" class="btn ghost small" data-act="sel-all">${T("Todas", "All")}</button>
                  <button type="button" class="btn ghost small" data-act="sel-none">${T("Ninguna", "None")}</button>` : "");
  }
  el.items.innerHTML = S.pages.map((p) => `<div class="card${t.mode !== "organize" ? " static-order" : ""}${selMode || t.mode === "insert" ? " selectable" : ""}${selMode && p.sel ? " selected" : ""}" data-id="${p.id}">
      <div class="thumb"><img src="${p.img}" alt="${T("Página", "Page")} ${p.i + 1}" class="${ROT_CLASS[p.r]}"></div>
      <div class="meta"><span class="num">${p.i + 1}</span>
      ${t.mode === "organize" ? `<button type="button" class="mini" data-act="rot-l" aria-label="${T("Girar a la izquierda", "Rotate left")}" title="${T("Girar a la izquierda", "Rotate left")}">⟲</button>
      <button type="button" class="mini" data-act="rot-r" aria-label="${T("Girar a la derecha", "Rotate right")}" title="${T("Girar a la derecha", "Rotate right")}">⟳</button>
      <button type="button" class="mini" data-act="del" aria-label="${T("Eliminar página", "Delete page")}" title="${T("Eliminar", "Delete")}">✕</button>` : ""}</div></div>`).join("");
  if (t.mode === "split") markRanges();
  if (t.mode === "insert") {
    const a = insertAfter(), mark = document.createElement("div");
    mark.className = "insert-mark";
    mark.innerHTML = `<span>＋</span>${T("Nuevas páginas aquí", "New pages here")}`;
    el.items.insertBefore(mark, el.items.children[a] || null);
  }
  el.run.disabled = S.pages.length === 0;
}

function insertAfter() {
  const v = parseInt(el.options.elements.after?.value, 10);
  return Math.min(Math.max(isNaN(v) ? S.pages.length : v, 0), S.pages.length);
}

function parseRangesClient(txt, n) {
  const set = new Set();
  for (const part of txt.replace(/\s|;/g, ",").split(",").filter(Boolean)) {
    const m = part.match(/^(\d*)-(\d*)$|^(\d+)$/);
    if (!m) continue;
    let a, b;
    if (m[3]) a = b = +m[3]; else { a = m[1] ? +m[1] : 1; b = m[2] ? +m[2] : n; }
    for (let k = Math.max(1, a); k <= Math.min(n, b); k++) set.add(k - 1);
  }
  return set;
}

function markRanges() {
  if (splitMode() !== "ranges") return;
  const set = parseRangesClient(el.options.elements.ranges.value, S.pages.length);
  [...el.items.children].forEach((c, k) => c.classList.toggle("selected", set.has(k)));
}

/* ---------- acciones sobre tarjetas ---------- */
el.toolbar.addEventListener("click", (e) => {
  const act = e.target.closest("[data-act]")?.dataset.act;
  if (!act) return;
  if (act === "sort-name") { S.items.sort((a, b) => a.file.name.localeCompare(b.file.name, LANG, { numeric: true })); renderFiles(); }
  if (act === "rot-all-l" || act === "rot-all-r") { S.pages.forEach((p) => p.r = (p.r + (act === "rot-all-r" ? 90 : 270)) % 360); renderPages(); }
  if (act === "reverse") { S.pages.reverse(); renderPages(); }
  if (act === "restore") { S.pages.forEach((p) => p.r = 0); S.pages.push(...(S.deleted || [])); S.deleted = []; S.pages.sort((a, b) => a.i - b.i); renderPages(); }
  if (act === "ins-start" || act === "ins-end") { el.options.elements.after.value = act === "ins-start" ? 0 : S.pages.length; renderPages(); }
  if (act === "sel-all" || act === "sel-none") { S.pages.forEach((p) => p.sel = act === "sel-all"); renderPages(); }
});

el.items.addEventListener("click", (e) => {
  if (Date.now() - lastDragEnd < 250) return; // ignorar el clic que sigue a un arrastre
  const card = e.target.closest(".card");
  if (!card) return;
  const act = e.target.closest("[data-act]")?.dataset.act;
  const id = card.dataset.id;
  if (S.tool.kind === "files" && act === "remove") {
    const it = S.items.find((i) => i.id === id);
    if (it && it.objUrl) URL.revokeObjectURL(it.objUrl);
    S.items = S.items.filter((i) => i.id !== id); renderFiles(); return;
  }
  if (S.tool.kind !== "pages") return;
  const p = S.pages.find((x) => x.id === id);
  if (act === "rot-l") p.r = (p.r + 270) % 360;
  else if (act === "rot-r") p.r = (p.r + 90) % 360;
  else if (act === "del") {
    if (S.pages.length === 1) { showError(T("El documento debe conservar al menos una página.", "The document must keep at least one page.")); return; }
    S.deleted = S.deleted || []; S.deleted.push(p);
    S.pages = S.pages.filter((x) => x !== p);
  } else if (S.tool.mode === "split" && splitMode() === "select") p.sel = !p.sel;
  else if (S.tool.mode === "insert") el.options.elements.after.value = S.pages.indexOf(p) + 1;
  else return;
  renderPages();
});

/* ---------- ordenar arrastrando (ratón y táctil) ---------- */
let drag = null, lastDragEnd = 0;
el.items.addEventListener("pointerdown", (e) => {
  const card = e.target.closest(".card");
  if (!card || card.classList.contains("static") || card.classList.contains("static-order") || e.target.closest("button")) return;
  if (e.button !== 0) return;
  drag = { card, x: e.clientX, y: e.clientY, started: false, pointerId: e.pointerId, touch: e.pointerType !== "mouse" };
  if (drag.touch) drag.timer = setTimeout(() => startDrag(drag.x, drag.y), 320); // pulsación larga en móvil
});
addEventListener("pointermove", (e) => {
  if (!drag) return;
  const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
  if (!drag.started) {
    if (drag.touch) { if (Math.hypot(dx, dy) > 10) { clearTimeout(drag.timer); drag = null; } return; }
    if (Math.hypot(dx, dy) > 6) startDrag(e.clientX, e.clientY); else return;
  }
  moveDrag(e.clientX, e.clientY);
});
addEventListener("pointerup", endDrag);
addEventListener("pointercancel", endDrag);
document.addEventListener("touchmove", (e) => { if (drag && drag.started) e.preventDefault(); }, { passive: false });

function startDrag(x, y) {
  if (!drag) return;
  const r = drag.card.getBoundingClientRect();
  drag.started = true; drag.offX = x - r.left; drag.offY = y - r.top;
  drag.ghost = drag.card.cloneNode(true);
  drag.ghost.classList.add("ghost");
  Object.assign(drag.ghost.style, { width: r.width + "px", height: r.height + "px" });
  document.body.appendChild(drag.ghost);
  drag.card.classList.add("placeholder");
  if (navigator.vibrate && drag.touch) navigator.vibrate(15);
  moveDrag(x, y);
}

function moveDrag(x, y) {
  drag.ghost.style.left = x - drag.offX + "px";
  drag.ghost.style.top = y - drag.offY + "px";
  const over = document.elementFromPoint(x, y)?.closest(".card");
  if (over && over !== drag.card && over.parentNode === el.items) {
    const r = over.getBoundingClientRect();
    const after = (y > r.bottom - r.height * 0.15) || (x > r.left + r.width / 2 && y > r.top);
    el.items.insertBefore(drag.card, after ? over.nextSibling : over);
  }
  if (y < 60) scrollBy(0, -12); else if (y > innerHeight - 60) scrollBy(0, 12);
}

function endDrag() {
  if (!drag) return;
  clearTimeout(drag.timer);
  if (drag.started) {
    drag.ghost.remove(); drag.card.classList.remove("placeholder");
    const order = [...el.items.children].map((c) => c.dataset.id);
    const byId = (arr) => order.map((id) => arr.find((x) => x.id === id));
    if (S.tool.kind === "files") { S.items = byId(S.items); renderFiles(); }
    else { S.pages = byId(S.pages); renderPages(); }
    lastDragEnd = Date.now();
  }
  drag = null;
}

/* ---------- ejecutar ---------- */
el.run.addEventListener("click", run);

async function run() {
  const t = S.tool;
  const fd = new FormData(el.options);
  if (t.id === "marca-agua") {
    if (fd.get("wm_type") === "text") fd.delete("image"); else fd.delete("text");
    if (fd.get("wm_type") === "image" && !(fd.get("image") && fd.get("image").size)) return showError(T("Elige una imagen para la marca de agua.", "Choose an image for the watermark."));
  }
  const err = t.validate && t.validate(fd);
  if (err) return showError(err);
  if (t.kind === "files") S.items.forEach((it) => fd.append("files", it.file, it.file.name));
  else fd.append("file", S.file, S.file.name);
  if (t.mode === "organize") fd.append("pages", JSON.stringify(S.pages.map((p) => ({ i: p.i, r: p.r }))));
  if (t.mode === "split" && fd.get("mode") === "select") {
    const sel = S.pages.filter((p) => p.sel).map((p) => p.i);
    if (!sel.length) return showError(T("Selecciona al menos una página.", "Select at least one page."));
    fd.append("pages", JSON.stringify(sel));
  }
  if (t.mode === "split" && fd.get("mode") === "ranges" && !String(fd.get("ranges")).trim())
    return showError(T("Escribe los rangos, por ejemplo: 1-3, 5, 8-", "Enter the ranges, for example: 1-3, 5, 8-"));

  busy(true, t.id === "ocr" ? T("Reconociendo texto… (puede tardar)", "Recognizing text… (this may take a while)")
    : t.id === "office-a-pdf" ? T("Convirtiendo con Office…", "Converting with Office…") : T("Procesando…", "Processing…"));
  try {
    const r = await api(t.endpoint, { method: "POST", body: fd });
    if (!r.ok) {
      let msg = `Error ${r.status}`;
      try { msg = (await r.json()).error || msg; } catch (e) { /* sin JSON */ }
      throw new Error(msg);
    }
    const blob = await r.blob();
    const name = decodeName(r.headers.get("X-Filename")) || T("resultado", "result");
    if (S.resultUrl) URL.revokeObjectURL(S.resultUrl);
    S.resultUrl = URL.createObjectURL(blob);
    let extra = "";
    const note = decodeName(r.headers.get("X-Note"));
    if (note) extra = ` ${esc(note)}`;
    else if (r.headers.get("X-Result-Size")) {
      const a = +r.headers.get("X-Original-Size"), b = +r.headers.get("X-Result-Size");
      extra = ` ${T("De", "From")} ${fmtSize(a)} ${T("a", "to")} ${fmtSize(b)} (<strong>${Math.round(100 - b * 100 / a)} % ${T("menos", "smaller")}</strong>).`;
    }
    el.result.innerHTML = `<div class="res ok"><span class="txt"><strong>${T("¡Listo!", "Done!")}</strong> ${esc(name)} · ${fmtSize(blob.size)}.${extra}</span>
      <a class="btn primary small" href="${S.resultUrl}" download="${esc(name)}">${T("Descargar", "Download")}</a></div>`;
    el.result.hidden = false;
    el.result.querySelector("a").click();
    el.result.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch (e) {
    showError(e.message === "Failed to fetch"
      ? T("No se pudo conectar con el servidor local. ¿Sigue abierta la ventana de la app?", "Could not reach the local server. Is the app window still open?")
      : e.message);
  } finally {
    busy(false);
  }
}

function decodeName(b64) {
  if (!b64) return "";
  try { return new TextDecoder().decode(Uint8Array.from(atob(b64), (c) => c.charCodeAt(0))); } catch (e) { return ""; }
}

function showError(msg) {
  el.work.hidden = el.work.hidden && !S.file && !S.items.length;
  const box = el.work.hidden ? el.notice : el.result;
  const html = `<div class="res err"><span class="txt">${esc(msg)}</span></div>`;
  if (box === el.notice) { renderNotice(); el.notice.insertAdjacentHTML("beforeend", html); setTimeout(renderNotice, 6000); }
  else { el.result.innerHTML = html; el.result.hidden = false; el.result.scrollIntoView({ behavior: "smooth", block: "nearest" }); }
}

function busy(on, text) {
  el.busy.hidden = !on;
  if (text) el.busyText.textContent = text;
  el.run.disabled = on;
}

applyStatic();
renderHome();
route();
loadStatus().then(() => { if (S.tool) setupOptions(); });
