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
   SHORTS (robust, no :has)
   - media flush to card edges
   - hide original title + date
   - inject date permalink directly under media
   ========================= */

body.page-shorts ul.embedded.blog-posts{
  list-style: none;
  padding: 0;
  margin: 2rem 0 3rem;
  display: grid;
  gap: 1.25rem;
}

/* Card */
body.page-shorts ul.embedded.blog-posts > li{
  position: relative;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: rgba(0,0,0,0.015);
  overflow: hidden;
  padding: 0 !important;      /* kill any inherited padding */
  padding-left: 0 !important; /* neutralize theme list indent */
}

/* Dark mode card bg */
@media (prefers-color-scheme: dark){
  body.page-shorts ul.embedded.blog-posts > li{
    background: rgba(255,255,255,0.03);
  }
}

/* Kill theme list marker "–" */
body.page-shorts ul.embedded.blog-posts > li::before{
  content: none !important;
}

/* Hide original Bear date + title */
body.page-shorts ul.embedded.blog-posts > li > span,
body.page-shorts ul.embedded.blog-posts > li > a{
  display: none !important;
}

/* Content wrapper must be flush */
body.page-shorts ul.embedded.blog-posts > li > div{
  padding: 0 !important;
  margin: 0 !important;
}

/* First paragraph (usually the media wrapper) must be flush */
body.page-shorts ul.embedded.blog-posts > li > div > p:first-child{
  margin: 0 !important;
  padding: 0 !important;
  max-width: none !important;
}

/* Media: FULL WIDTH, no crop, no margins (override global theme rules) */
body.page-shorts ul.embedded.blog-posts > li > div img,
body.page-shorts ul.embedded.blog-posts > li > div video,
body.page-shorts ul.embedded.blog-posts > li > div iframe{
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  margin: 0 !important;     /* this is the usual culprit */
  border: 0 !important;
  height: auto !important;
  object-fit: contain !important; /* never crop */
  border-radius: var(--radius) var(--radius) 0 0 !important;
}

/* iframe ratio */
body.page-shorts ul.embedded.blog-posts > li > div iframe{
  aspect-ratio: 16 / 9;
}

/* Text paragraphs: inner padding */
body.page-shorts ul.embedded.blog-posts > li > div p{
  margin: 0.85rem 0 !important;
  padding: 0 1.1rem !important;
  max-width: var(--text-measure);
}

/* Keep the media paragraph flush even though the rule above hits all p */
body.page-shorts ul.embedded.blog-posts > li > div > p:first-child{
  padding: 0 !important;
}

/* Date permalink injected by JS (sits under media) */
body.page-shorts ul.embedded.blog-posts a.shorts-permalink{
  display: block;
  padding: 0.55rem 1.1rem 0; /* under media, before text */
  margin: 0;
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
</style>

<script>
(() => {
  function initShorts() {
    const marker = document.querySelector(".page-marker[data-page='shorts']");
    if (!marker) return;

    // Robust scoping: set body class once
    document.body.classList.add("page-shorts");

    // Find the list (don’t assume sibling structure)
    const list = document.querySelector("ul.embedded.blog-posts");
    if (!list) return;

    list.querySelectorAll(":scope > li").forEach(li => {
      const content = li.querySelector(":scope > div");
      if (!content) return;

      // idempotent: don't add twice
      if (content.querySelector(":scope > a.shorts-permalink")) return;

      const time = li.querySelector(":scope > span time");
      const titleLink = li.querySelector(":scope > a[href]");
      if (!time || !titleLink) return;

      const a = document.createElement("a");
      a.href = titleLink.getAttribute("href");
      a.className = "shorts-permalink";
      a.textContent = time.textContent.trim();

      // Place date permalink directly under the first media paragraph (if present)
      const firstP = content.querySelector(":scope > p:first-child");
      if (firstP) {
        firstP.insertAdjacentElement("afterend", a);
      } else {
        content.insertAdjacentElement("afterbegin", a);
      }
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
