/* Interacción de Grano y Taza: selector en 2 pasos de la portada y barra "Ver precio" en móvil.
   Sin JS todo sigue funcionando: las opciones del selector son enlaces a las guías y la barra no aparece. */
(function () {
  var reduce = matchMedia("(prefers-reduced-motion: reduce)");

  /* ---------- Selector en 2 pasos ---------- */
  var quiz = document.querySelector("[data-quiz]");
  if (quiz) {
    var live = quiz.querySelector("[data-live]");
    var show = function (name) {
      var next = quiz.querySelector('[data-panel="' + name + '"]');
      if (!next) return;
      quiz.querySelectorAll(".pk-panel").forEach(function (p) { p.hidden = p !== next; });
      if (!reduce.matches) {
        next.classList.remove("pk-in");
        void next.offsetWidth; // reinicia la animación de entrada
        next.classList.add("pk-in");
      }
      var h = next.querySelector("h2");
      if (h) { h.focus({ preventScroll: true }); if (live) live.textContent = h.textContent; }
      var top = quiz.getBoundingClientRect().top;
      if (top < 0) quiz.scrollIntoView({ behavior: reduce.matches ? "auto" : "smooth", block: "start" });
    };
    quiz.addEventListener("click", function (e) {
      var typeLink = e.target.closest("a[data-type]");
      if (typeLink) { e.preventDefault(); show(typeLink.dataset.type); return; }
      var opt = e.target.closest("button[data-key]");
      if (opt) { show(opt.dataset.key); return; }
      var back = e.target.closest("[data-to]");
      if (back) show(back.dataset.to);
    });
  }

  /* ---------- Barra "Ver precio" en reseñas y guías (móvil) ---------- */
  var bar = document.querySelector("[data-sticky]");
  if (!bar || !("IntersectionObserver" in window)) return;
  var name = bar.querySelector(".sb-name"), price = bar.querySelector(".sb-price"), go = bar.querySelector(".sb-go");
  var products = document.querySelectorAll(".prose .product[data-name], .prose .pcard[data-name]");
  var hideWhen = document.querySelectorAll(".article-head, .verdict, .site-foot");
  var hiding = new Set();

  var toggle = function () {
    var on = hiding.size === 0;
    bar.classList.toggle("is-on", on);
    bar.toggleAttribute("inert", !on);
  };
  toggle();

  // La barra se oculta mientras se ve la cabecera, el veredicto (que ya tiene su botón) o el pie.
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) { en.isIntersecting ? hiding.add(en.target) : hiding.delete(en.target); });
    toggle();
  });
  hideWhen.forEach(function (el) { io.observe(el); });

  if (products.length) {
    var current = null;
    var io2 = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting || en.target === current) return;
        current = en.target;
        name.textContent = current.dataset.name;
        price.textContent = current.dataset.price || "";
        go.href = current.dataset.url;
      });
    }, { rootMargin: "-35% 0px -55% 0px" });
    products.forEach(function (p) { io2.observe(p); });
  }
})();
