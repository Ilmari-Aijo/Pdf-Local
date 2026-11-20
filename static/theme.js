// Aplica el tema guardado antes de pintar (evita parpadeo).
(function () {
  try {
    var t = localStorage.getItem("pdf-tema");
    if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
  } catch (e) { /* sin almacenamiento: usar el del sistema */ }
})();
