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
    /* Safari paints the status-bar strip and its own toolbar with
       theme-color, so it must follow the manual toggle. The theme is driven
       by data-theme, not prefers-color-scheme, so a media-query meta cannot
       do this. Keep these hexes equal to --sand-bg and --night. */
    var tc = document.querySelector('meta[name="theme-color"]');
    if (tc) tc.setAttribute("content", mode === "night" ? "#2b1b1c" : "#f8f1ea");
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
    /* A disclosure menu is expected to close on Escape and on a click
       outside it. The menu.contains() guard matters: without it the click
       that opens the menu bubbles to document and closes it again. */
    document.addEventListener("keydown", function(e){
      if (e.key === "Escape" && nav.classList.contains("is-open")){
        closeMenu();
        menu.focus();
      }
    });
    document.addEventListener("click", function(e){
      if (!nav.classList.contains("is-open")) return;
      if (nav.contains(e.target) || menu.contains(e.target)) return;
      closeMenu();
    });
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

  /* The overflow lock is DELIBERATE: freezing the document is what sells the
     bar sliding off-screen behind the dialog. Keep it. It is cleared here
     rather than on the dialog's close event so an Escape press unwinds it
     too. */
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
        /* guarded so a throw here cannot strand the page with overflow:hidden */
        try {
          lightbox.showModal();
        } catch (err) {
          closeLightbox();
        }
      });
    });
    photoClose.addEventListener("click", closeLightbox);
    lightbox.addEventListener("click", function(e){
      if (e.target === lightbox) closeLightbox();
    });
    lightbox.addEventListener("cancel", closeLightbox);
  }

  /* ---------- seamless marquee ---------- */
  /* The -50% in `@keyframes slide` only lands seamlessly if the track is
     duplicated EXACTLY once — the CSS and this loop are a pair, do not
     change one without the other. Cloning nodes rather than reassigning
     innerHTML avoids a full reparse and keeps any listeners intact. */
  var track = document.getElementById("tickerTrack");
  if (track){
    var dupe = document.createDocumentFragment();
    Array.prototype.forEach.call(track.children, function(node){
      dupe.appendChild(node.cloneNode(true));
    });
    track.appendChild(dupe);
  }

  /* ---------- stat bars: fill in discrete 5% steps ---------- */
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function fillBar(card){
    card.querySelectorAll(".bar i").forEach(function(el){
      var target = Math.max(0, parseInt(el.dataset.level, 10) || 0),
          stat   = el.closest(".stat"),
          out    = stat && stat.querySelector("[data-out]");
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
  var seq = ["arrowup","arrowup","arrowdown","arrowdown",
             "arrowleft","arrowright","arrowleft","arrowright","b","a"],
      pos = 0;
  window.addEventListener("keydown", function(e){
    /* keyCode is deprecated, and the sequence must not eat keystrokes aimed
       at a field — there are none today, but a search box would break this. */
    var el = e.target;
    if (el && (el.isContentEditable ||
               /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName || ""))){
      pos = 0;
      return;
    }
    var key = String(e.key || "").toLowerCase();
    /* a mismatch that happens to be the FIRST key restarts at 1, not 0 */
    pos = (key === seq[pos]) ? pos + 1 : (key === seq[0] ? 1 : 0);
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
