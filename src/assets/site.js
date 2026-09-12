(function(){
  "use strict";

  /* Shared by index.html AND every generated blog page, so every lookup
     must tolerate a missing element — a post page has no ticker or stat
     card, and an unguarded getElementById(...).x throws and kills the
     reveal logic further down. */
  var yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  /* ---------- theme (rose <-> night), persisted ---------- */
  var root = document.documentElement,
      btn  = document.getElementById("themeToggle"),
      KEY  = "px-theme";

  function apply(mode){
    if (mode === "night") root.setAttribute("data-theme","night");
    else root.removeAttribute("data-theme");
    if (!btn) return;
    var nextTheme = (mode === "night") ? "light" : "dark";
    btn.textContent = "";
    btn.dataset.icon = (mode === "night") ? "sun" : "moon";
    btn.setAttribute("aria-label", "Switch to " + nextTheme + " theme");
    btn.setAttribute("aria-pressed", String(mode === "night"));
  }
  var saved = null;
  try { saved = localStorage.getItem(KEY); } catch(e){}
  apply(saved === "night" ? "night" : "rose");

  function toggleTheme(){
    var next = root.hasAttribute("data-theme") ? "rose" : "night";
    apply(next);
    try { localStorage.setItem(KEY, next); } catch(e){}
  }
  if (btn) btn.addEventListener("click", toggleTheme);

  /* ---------- mobile navigation ---------- */
  var menu = document.getElementById("menuToggle"),
      nav = document.querySelector(".nav-links");
  function closeMenu(){
    if (!menu || !nav) return;
    nav.classList.remove("is-open");
    menu.classList.remove("is-open");
    menu.setAttribute("aria-expanded", "false");
    menu.setAttribute("aria-label", "Open navigation");
  }
  if (menu && nav){
    menu.addEventListener("click", function(){
      var open = !nav.classList.contains("is-open");
      nav.classList.toggle("is-open", open);
      menu.classList.toggle("is-open", open);
      menu.setAttribute("aria-expanded", String(open));
      menu.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
    });
    nav.querySelectorAll("a").forEach(function(link){
      link.addEventListener("click", closeMenu);
    });
    window.addEventListener("resize", function(){
      if (window.innerWidth > 900) closeMenu();
    }, {passive:true});
  }

  /* ---------- photo lightbox ---------- */
  var lightbox = document.getElementById("photoLightbox"),
      lightboxImage = document.getElementById("photoLightboxImage"),
      photoDownload = document.getElementById("photoDownload"),
      photoClose = document.getElementById("photoClose"),
      lightboxTitle = document.getElementById("photoLightboxTitle"),
      lightboxPlace = document.getElementById("photoLightboxPlace"),
      lightboxCamera = document.getElementById("photoLightboxCamera"),
      lightboxFilm = document.getElementById("photoLightboxFilm"),
      lightboxApp = document.getElementById("photoLightboxApp");

  function closeLightbox(){
    if (!lightbox) return;
    lightbox.close();
    document.documentElement.style.overflow = "";
    document.body.style.overflow = "";
    if (lightboxImage) lightboxImage.removeAttribute("src");
  }
  if (lightbox && lightboxImage && photoDownload && photoClose){
    document.querySelectorAll(".photo-open").forEach(function(link){
      link.addEventListener("click", function(e){
        e.preventDefault();
        var source = link.dataset.photoFull;
        lightboxImage.src = source;
        lightboxImage.alt = link.querySelector("img").alt;
        photoDownload.href = source;
        lightboxTitle.textContent = link.dataset.photoTitle || "";
        lightboxPlace.textContent = link.dataset.photoPlace || "";
        lightboxCamera.textContent = link.dataset.photoCamera || "";
        lightboxFilm.textContent = link.dataset.photoFilm || "";
        lightboxApp.textContent = link.dataset.photoApp || "";
        document.documentElement.style.overflow = "hidden";
        document.body.style.overflow = "hidden";
        lightbox.showModal();
      });
    });
    photoClose.addEventListener("click", closeLightbox);
    lightbox.addEventListener("click", function(e){
      if (e.target === lightbox) closeLightbox();
    });
    lightbox.addEventListener("cancel", closeLightbox);
  }

  /* ---------- seamless marquee ---------- */
  var track = document.getElementById("tickerTrack");
  if (track) track.innerHTML += track.innerHTML;

  /* ---------- stat bars: fill in discrete 5% steps ---------- */
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function fillBar(card){
    card.querySelectorAll(".bar i").forEach(function(el){
      var target = Math.max(0, parseInt(el.dataset.level, 10) || 0),
          out    = el.closest(".stat").querySelector("[data-out]");
      if (reduced){
        el.style.width = target + "%";
        if (out) out.textContent = target;
        return;
      }
      var v = 0;
      var iv = setInterval(function(){
        v += 5;                       // one whole cell per tick
        if (v >= target){ v = target; clearInterval(iv); }
        el.style.width = v + "%";
        if (out) out.textContent = v;
      }, 40);
    });
  }

  /* ---------- reveal ----------
     IntersectionObserver alone strands content that gets jumped past
     (anchor links, deep links, restored scroll). Pair it with a sweep. */
  var items = Array.prototype.slice.call(document.querySelectorAll(".reveal")),
      barsDone = false;

  function show(el){
    el.classList.add("in");
    if (!barsDone && el.classList.contains("card")){ barsDone = true; fillBar(el); }
  }

  if (!("IntersectionObserver" in window) || reduced){
    items.forEach(show);
    items.length = 0;
  } else {
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if (!e.isIntersecting) return;
        show(e.target);
        io.unobserve(e.target);
        var i = items.indexOf(e.target);
        if (i > -1) items.splice(i,1);
      });
    }, { rootMargin:"0px 0px -10% 0px", threshold:0.06 });

    items.forEach(function(el){ io.observe(el); });

    var ticking = false;
    function sweep(){
      ticking = false;
      for (var i = items.length - 1; i >= 0; i--){
        var el = items[i];
        if (el.getBoundingClientRect().top < window.innerHeight * 0.94){
          show(el); io.unobserve(el); items.splice(i,1);
        }
      }
    }
    function onScroll(){ if (!ticking){ ticking = true; requestAnimationFrame(sweep); } }
    window.addEventListener("scroll", onScroll, {passive:true});
    window.addEventListener("resize", onScroll, {passive:true});
    window.addEventListener("hashchange", function(){ setTimeout(sweep,60); });
    setTimeout(sweep, 250);
  }

  /* ---------- konami code -> flip theme ---------- */
  var seq = [38,38,40,40,37,39,37,39,66,65], pos = 0;
  window.addEventListener("keydown", function(e){
    pos = (e.keyCode === seq[pos]) ? pos + 1 : 0;
    if (pos === seq.length){
      pos = 0;
      toggleTheme();
      document.body.animate(
        [{filter:"invert(1)"},{filter:"none"}],
        {duration:400, easing:"steps(4, end)"}
      );
    }
  });
})();
