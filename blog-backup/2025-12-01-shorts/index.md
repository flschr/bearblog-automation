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

<span hidden>Eine kleine Auswahl von sehenswerten Fotos von René Fischer.</span>

<style>
/* =========================
   SHORTS (robust)
   - full-bleed media in cards
   - title+date hidden (Bear default)
   - date permalink injected UNDER content
   - text-only shorts look like centered h2
   - load-more batches (JS adds .shorts-hidden)
   ========================= */

body.page-shorts ul.embedded.blog-posts{
  list-style: none;
  padding: 0;
  margin: 2rem 0 2rem;
  display: grid;
  gap: 1.25rem;
}

/* Card */
body.page-shorts ul.embedded.blog-posts > li{
  position: relative;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: rgba(0,0,0,0.015);
  overflow: hidden;     /* clip media to radius */
  padding: 0 !important; /* no inner padding */
  padding-left: 0 !important; /* kill global list dash layout */
}
@media (prefers-color-scheme: dark){
  body.page-shorts ul.embedded.blog-posts > li{
    background: rgba(255,255,255,0.03);
  }
}
body.page-shorts ul.embedded.blog-posts > li::before{
  content: none !important;
}

/* Hide Bear's original date + title link */
body.page-shorts ul.embedded.blog-posts > li > span,
body.page-shorts ul.embedded.blog-posts > li > a{
  display: none !important;
}

/* Content wrapper: no padding so media can be flush */
body.page-shorts ul.embedded.blog-posts > li > div{
  padding: 0 !important;
  margin: 0 !important;
}

/* First paragraph (often media wrapper) flush */
body.page-shorts ul.embedded.blog-posts > li > div > p:first-child{
  margin: 0 !important;
  padding: 0 !important;
  max-width: none !important;
}

/* Media: full width, no crop, override global theme margins/overbleed */
body.page-shorts ul.embedded.blog-posts > li > div img,
body.page-shorts ul.embedded.blog-posts > li > div video,
body.page-shorts ul.embedded.blog-posts > li > div iframe{
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  margin: 0 !important;
  border: 0 !important;
  height: auto !important;
  object-fit: contain !important;
  border-radius: var(--radius) var(--radius) 0 0 !important;
}
body.page-shorts ul.embedded.blog-posts > li > div iframe{
  aspect-ratio: 16 / 9;
  height: auto !important;
}

/* Text paragraphs inside card */
body.page-shorts ul.embedded.blog-posts > li > div p{
  margin: 0.95rem 0 !important;
  padding: 0 1.2rem !important;
  max-width: var(--text-measure);
}
/* First paragraph stays flush if it's media */
body.page-shorts ul.embedded.blog-posts > li > div > p:first-child{
  padding: 0 !important;
  max-width: none !important;
}

/* Injected date permalink (ALWAYS under everything) */
body.page-shorts ul.embedded.blog-posts a.shorts-permalink{
  display: block;
  padding: 0.35rem 1.2rem 1.05rem; /* closes card with breathing room */
  font-size: 0.82em;
  line-height: 1.2;
  color: var(--muted);
  text-decoration: none;
}
body.page-shorts ul.embedded.blog-posts a.shorts-permalink:hover{
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
  opacity: 0.9;
}

/* Load more UI */
body.page-shorts .shorts-loadmore-wrap{
  display: flex;
  justify-content: center;
  margin: 1.75rem 0 3rem;
}
body.page-shorts .shorts-loadmore{
  appearance: none;
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.65rem 1.05rem;
  background: rgba(0,0,0,0.015);
  color: var(--text-color);
  font: inherit;
  cursor: pointer;
}
@media (prefers-color-scheme: dark){
  body.page-shorts .shorts-loadmore{
    background: rgba(255,255,255,0.03);
  }
}
body.page-shorts .shorts-loadmore:hover{ opacity: 0.9; }
body.page-shorts .shorts-loadmore:disabled{ opacity: 0.6; cursor: default; }

/* Hidden items (after initial 20) */
body.page-shorts li.shorts-hidden{ display: none !important; }

/* =========================
   Text-only shorts (JS adds .shorts-textonly on <li>)
   ========================= */

body.page-shorts ul.embedded.blog-posts > li.shorts-textonly > div{
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;

  padding: 2.15rem 2.35rem 1.9rem !important; /* nice air */
}

body.page-shorts ul.embedded.blog-posts > li.shorts-textonly > div > p{
  margin: 0 !important;
  padding: 0 !important;

  font-family: var(--font-main);
  font-size: 1.55em;  /* ≈ h2 */
  line-height: 1.35;
  font-weight: 800;
  color: var(--heading-color);

  max-width: 34em;
}

body.page-shorts ul.embedded.blog-posts > li.shorts-textonly a.shorts-permalink{
  padding: 0 !important;
  margin-top: 1.05rem;
  font-size: 0.82em;
  text-align: center;
}
</style>

<script>
(() => {
  const BATCH = 20;

  // 1x1 transparent gif placeholder (tiny)
  const PLACEHOLDER =
    "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";

  function initShorts() {
    // Robust: only activate on /shorts/ pages with the embedded list
    const isShortsPath = (location.pathname || "").replace(/\/+$/, "/") === "/shorts/";
    const list = document.querySelector("ul.embedded.blog-posts");
    if (!isShortsPath || !list) return;

    document.body.classList.add("page-shorts");

    const items = Array.from(list.querySelectorAll(":scope > li"));

    // 1) Inject date permalink UNDER the text (idempotent)
    items.forEach(li => {
      const content = li.querySelector(":scope > div");
      if (!content) return;

      // mark text-only posts for styling
      const hasMedia = !!content.querySelector("img, video, iframe");
      if (!hasMedia) li.classList.add("shorts-textonly");

      // already injected?
      if (content.querySelector(":scope > a.shorts-permalink")) return;

      const time = li.querySelector(":scope > span time");
      const titleLink = li.querySelector(":scope > a[href]");
      if (!time || !titleLink) return;

      const a = document.createElement("a");
      a.href = titleLink.getAttribute("href");
      a.className = "shorts-permalink";
      a.textContent = time.textContent.trim();

      // Always at the end: UNDER all text paragraphs
      content.appendChild(a);
    });

    // 2) Hide after first batch
    items.forEach((li, idx) => {
      if (idx >= BATCH) li.classList.add("shorts-hidden");
    });

    // 3) Load more button (idempotent)
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
        if (remaining <= 0) {
          wrap.remove();
          return;
        }
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

    // 4) Lazy-unload images far away (DOM bleibt; Bilder werden entladen)
    const io = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        const img = entry.target;
        const real = img.getAttribute("data-src");
        if (!real) continue;

        if (entry.isIntersecting) {
          if (img.src !== real) img.src = real;
        } else {
          if (img.src === real) img.src = PLACEHOLDER;
        }
      }
    }, {
      root: null,
      rootMargin: "900px 0px 900px 0px",
      threshold: 0.01
    });

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

{{ posts | tag:shorts | content:True }}
