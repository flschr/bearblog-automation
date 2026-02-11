---
uid: KpcGoCZNcfaVierAuLSW
title: Shorts
slug: shorts
alias: ""
published_date: "2025-12-01T19:32:00+00:00"
all_tags: "[]"
publish: "True"
make_discoverable: "False"
is_page: "True"
canonical_url: ""
meta_description: ""
meta_image: "https://bear-images.sfo2.cdn.digitaloceanspaces.com/fischr/photo-1592634549335-f6be8df97b47.webp"
lang: ""
class_name: ""
first_published_at: "2025-12-01T19:32:00+00:00"
---

<style>
body.page-shorts ul.embedded.blog-posts{
  list-style: none;
  padding: 0;
  margin: 2rem 0 2rem;
  display: grid;
  gap: 1.25rem;
}

body.page-shorts ul.embedded.blog-posts > li{
  position: relative;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: rgba(0,0,0,0.015);
  overflow: hidden;
  padding: 0 !important;
  padding-left: 0 !important;
}

@media (prefers-color-scheme: dark){
  body.page-shorts ul.embedded.blog-posts > li{ background: rgba(255,255,255,0.03); }
}

body.page-shorts ul.embedded.blog-posts > li::before{ content:none !important; }
body.page-shorts ul.embedded.blog-posts > li > span,
body.page-shorts ul.embedded.blog-posts > li > a{ display:none !important; }

body.page-shorts ul.embedded.blog-posts > li > div{ padding:0 !important; margin:0 !important; }

body.page-shorts ul.embedded.blog-posts > li > div > p:first-child{
  margin:0 !important; padding:0 !important; max-width:none !important;
}

body.page-shorts ul.embedded.blog-posts > li > div img,
body.page-shorts ul.embedded.blog-posts > li > div video,
body.page-shorts ul.embedded.blog-posts > li > div iframe{
  display:block !important;
  width:100% !important;
  max-width:100% !important;
  margin:0 !important;
  border:0 !important;
  height:auto !important;
  object-fit:contain !important;
  border-radius: var(--radius) var(--radius) 0 0 !important;
}

body.page-shorts ul.embedded.blog-posts > li > div iframe{ aspect-ratio:16/9; }

body.page-shorts ul.embedded.blog-posts > li > div p{
  margin:0.85rem 0 !important;
  padding:0 1.1rem !important;
  max-width: var(--text-measure);
}
body.page-shorts ul.embedded.blog-posts > li > div > p:first-child{ padding:0 !important; }

body.page-shorts ul.embedded.blog-posts a.shorts-permalink{
  display:block;
  padding:0.55rem 1.1rem 0;
  font-size:0.82em;
  line-height:1.2;
  color: var(--muted);
  text-decoration:none;
}
body.page-shorts ul.embedded.blog-posts a.shorts-permalink:hover{
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
  opacity: 0.9;
}

/* Load more UI */
body.page-shorts .shorts-loadmore-wrap{
  display:flex;
  justify-content:center;
  margin:1.75rem 0 3rem;
}
body.page-shorts .shorts-loadmore{
  appearance:none;
  border:1px solid var(--border);
  border-radius:999px;
  padding:0.65rem 1.05rem;
  background: rgba(0,0,0,0.015);
  color: var(--text-color);
  font: inherit;
  cursor:pointer;
}
@media (prefers-color-scheme: dark){
  body.page-shorts .shorts-loadmore{ background: rgba(255,255,255,0.03); }
}
body.page-shorts .shorts-loadmore:disabled{ opacity:.6; cursor:default; }

/* Hidden items (after initial 20) */
body.page-shorts li.shorts-hidden{ display:none !important; }
</style>

<script>
(() => {
  const BATCH = 20;

  // 1x1 transparent gif placeholder (tiny)
  const PLACEHOLDER =
    "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";

  function initShorts() {
    const marker = document.querySelector(".page-marker[data-page='shorts']");
    if (!marker) return;

    document.body.classList.add("page-shorts");

    const list = document.querySelector("ul.embedded.blog-posts");
    if (!list) return;

    const items = Array.from(list.querySelectorAll(":scope > li"));

    // Inject permalink under media (idempotent)
    items.forEach(li => {
      const content = li.querySelector(":scope > div");
      if (!content) return;
      if (content.querySelector(":scope > a.shorts-permalink")) return;

      const time = li.querySelector(":scope > span time");
      const titleLink = li.querySelector(":scope > a[href]");
      if (!time || !titleLink) return;

      const a = document.createElement("a");
      a.href = titleLink.getAttribute("href");
      a.className = "shorts-permalink";
      a.textContent = time.textContent.trim();

      const firstP = content.querySelector(":scope > p:first-child");
      if (firstP) firstP.insertAdjacentElement("afterend", a);
      else content.insertAdjacentElement("afterbegin", a);
    });

    // Hide after first batch
    items.forEach((li, idx) => { if (idx >= BATCH) li.classList.add("shorts-hidden"); });

    // Build Load more button
    if (items.length > BATCH && !document.querySelector(".shorts-loadmore-wrap")) {
      const wrap = document.createElement("div");
      wrap.className = "shorts-loadmore-wrap";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "shorts-loadmore";
      wrap.appendChild(btn);
      list.insertAdjacentElement("afterend", wrap);

      const visibleCount = () => items.filter(li => !li.classList.contains("shorts-hidden")).length;

      const updateBtn = () => {
        const shown = visibleCount();
        const remaining = items.length - shown;
        if (remaining <= 0) { wrap.remove(); return; }
        btn.textContent = `Mehr laden (${Math.min(BATCH, remaining)})`;
      };

      btn.addEventListener("click", () => {
        btn.disabled = true;
        const shown = visibleCount();
        const end = Math.min(shown + BATCH, items.length);
        for (let i = shown; i < end; i++) items[i].classList.remove("shorts-hidden");
        btn.disabled = false;
        updateBtn();
      });

      updateBtn();
    }

    // Lazy-unload images far away (and reload when near)
    // Cards stay in DOM + scrollable; only image bytes get dropped.
    const io = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        const img = entry.target;
        const isNear = entry.isIntersecting;

        if (isNear) {
          // restore real src if unloaded
          const real = img.getAttribute("data-src");
          if (real && img.src !== real) {
            img.src = real;
          }
        } else {
          // unload when offscreen (but only if it was loaded at least once)
          const real = img.getAttribute("data-src");
          if (real && img.src === real) {
            img.src = PLACEHOLDER;
          }
        }
      }
    }, {
      // Unload when sufficiently far away; preload when approaching.
      root: null,
      rootMargin: "800px 0px 800px 0px",
      threshold: 0.01
    });

    // Register all images once: store src into data-src, keep initial src
    list.querySelectorAll("img").forEach(img => {
      if (!img.getAttribute("data-src")) {
        img.setAttribute("data-src", img.currentSrc || img.src);
      }
      io.observe(img);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initShorts, { once: true });
  } else {
    initShorts();
  }
})();
</script>

<span class="page-marker" data-page="shorts" hidden></span>
{{ posts | tag:shorts | content:True }}
