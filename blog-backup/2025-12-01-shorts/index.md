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
   SHORTS
   Requirements:
   - NO :has()
   - media flush to card edges
   - top corners rounded (only)
   - date as permalink under media
   - neutralize Bear/Basetheme list "–" styling
   - optional perf: content-visibility
   ========================= */

/* Scoped to this page via marker (cheap in modern engines) */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts{
  list-style: none;
  padding: 0;
  margin: 2rem 0 3rem;
  display: grid;
  gap: 1.25rem;
}

/* Card */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li{
  position: relative;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: rgba(0,0,0,0.015);
  overflow: hidden;   /* clip media to rounded card */
  padding: 0;         /* no padding on card itself */

  /* PERF (Chromium): render offscreen items lazily */
  content-visibility: auto;
  contain-intrinsic-size: 900px; /* approx card height to keep scroll stable */
}

@media (prefers-color-scheme: dark){
  .page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li{
    background: rgba(255,255,255,0.03);
  }
}

/* ---- Neutralize global ul.blog-posts list styling (the "–" etc.) ---- */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li{
  padding-left: 0 !important;
}
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li::before{
  content: none !important;
}

/* Hide original date + title (we’ll inject date permalink via JS) */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li > span,
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li > a{
  display: none !important;
}

/* Content wrapper: no padding (so media can be edge-to-edge) */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li > div{
  padding: 0;
  margin: 0;
}

/* Media paragraph (first p containing media) stays flush */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li > div > p:first-child{
  margin: 0;
  padding: 0;
  max-width: none;
}

/* Media itself: FULL WIDTH, no crop */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li > div img,
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li > div video,
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li > div iframe{
  display: block;
  width: 100%;
  max-width: 100%;
  margin: 0;
  border: 0;
  height: auto;
  object-fit: contain; /* never crop */
  border-radius: var(--radius) var(--radius) 0 0; /* only top corners */
}

/* iframe ratio */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li > div iframe{
  aspect-ratio: 16 / 9;
  height: auto !important;
}

/* Text paragraphs: padding inside card */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li > div p{
  margin: 0.85rem 0;
  padding: 0 1.1rem;
  max-width: var(--text-measure);
}

/* Keep first media paragraph flush even if theme styles p */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts > li > div > p:first-child{
  padding: 0 !important;
}

/* Date permalink injected by JS */
.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts .shorts-permalink{
  display: block;
  padding: 0.15rem 1.1rem 0.95rem;
  margin-top: 0.25rem;
  font-size: 0.82em;
  line-height: 1.2;
  color: var(--muted);
  text-decoration: none;
}

.page-marker[data-page="shorts"] ~ ul.embedded.blog-posts .shorts-permalink:hover{
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
  opacity: 0.9;
}
</style>

<script>
(() => {
  // Run once, safe if executed multiple times
  function initShortsPermalinks() {
    const marker = document.querySelector(".page-marker[data-page='shorts']");
    if (!marker) return;

    const list = marker.nextElementSibling;
    if (!list || !list.matches("ul.embedded.blog-posts")) return;

    list.querySelectorAll(":scope > li").forEach(li => {
      // idempotent: don't inject twice
      const content = li.querySelector(":scope > div");
      if (!content || content.querySelector(":scope > a.shorts-permalink")) return;

      const time = li.querySelector(":scope > span time");
      const titleLink = li.querySelector(":scope > a[href]");
      if (!time || !titleLink) return;

      const a = document.createElement("a");
      a.href = titleLink.getAttribute("href");
      a.className = "shorts-permalink";
      a.textContent = time.textContent.trim();

      content.appendChild(a);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initShortsPermalinks, { once: true });
  } else {
    initShortsPermalinks();
  }
})();
</script>

<span class="page-marker" data-page="shorts" hidden></span>
{{ posts | tag:shorts | content:True }}
