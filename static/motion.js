/* Movimiento de Grano y Taza (GSAP + ScrollTrigger).
   Un único momento con autoría: al cargar la portada, el café "cae" en las tazas del selector.
   Las listas de productos y artículos aparecen una vez, escalonadas, al entrar en pantalla.
   Todo el contenido es visible por defecto: si GSAP no carga, la página funciona igual.
   Con "reducir movimiento" activado no se anima nada. */
(function () {
  if (!window.gsap) return;
  if (window.ScrollTrigger) gsap.registerPlugin(ScrollTrigger);
  var mm = gsap.matchMedia();

  mm.add("(prefers-reduced-motion: no-preference)", function () {
    var hero = document.querySelector(".hero");
    if (hero) {
      var tl = gsap.timeline({ defaults: { ease: "expo.out" } });
      tl.from(".hero h1", { y: 22, autoAlpha: 0, filter: "blur(6px)", duration: 0.9, clearProps: "filter" })
        .from(".hero .intro, .hero .hero-by", { y: 14, autoAlpha: 0, duration: 0.7, stagger: 0.1 }, "-=0.65")
        .from(".picker h2", { autoAlpha: 0, duration: 0.5 }, "-=0.6")
        .from(".picker li", { x: 20, autoAlpha: 0, duration: 0.6, stagger: 0.07 }, "-=0.5")
        .from(".picker .pour", {
          scaleY: 0, transformOrigin: "50% 0%", duration: 1.1, ease: "power1.inOut", stagger: 0.06
        }, "-=0.25");
    }

    if (window.ScrollTrigger) {
      var lists = gsap.utils.toArray(".pgrid.home .pcard, .ecards .ecard, .glist li");
      if (lists.length) {
        gsap.set(lists, { autoAlpha: 0, y: 18 });
        ScrollTrigger.batch(lists, {
          start: "top 90%",
          once: true,
          onEnter: function (els) {
            gsap.to(els, { autoAlpha: 1, y: 0, duration: 0.6, ease: "expo.out", stagger: 0.07, overwrite: true });
          }
        });
      }
    }
  });
})();
