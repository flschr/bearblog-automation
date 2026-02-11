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
   SHORTS + Load more + Windowing (DOM removal)
   - Shows 20 at a time, keeps only MAX_VISIBLE in DOM
   - Hides original title/date, injects date permalink under media
   ========================= */

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
  body.page-shorts ul.embedded.blog-posts > li{
    background: rgba(255,255,255,0.03);
  }
}

body.page-shorts ul.embedded.blog-posts > li::before{
  content: none !important;
}

/* Hide original Bear date + title */
body.page-shorts ul.embedded.blog-posts > li > span,
body.page-shorts ul.embedded.blog-posts > li > a{
  display: none !important;
}

body.page-shorts ul.embedded.blog-posts > li > div{
  padding: 0 !important;
  margin: 0 !important;
}

/* first p flush */
body.page-shorts ul.embedded.blog-posts > li > div > p:first-child{
  margin: 0 !important;
  padding: 0 !important;
  max-width: none !important;
}

/* media full-bleed, override global theme margins */
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
}

/* text padding */
body.page-shorts ul.embedded.blog-posts > li > div p{
  margin: 0.85rem 0 !important;
  padding: 0 1.1rem !important;
  max-width: var(--text-measure);
}
body.page-shorts ul.embedded.blog-posts > li > div > p:first-child{
  padding: 0 !important;
}

/* injected date permalink (under media) */
body.page-shorts ul.embedded.blog-posts a.shorts-permalink{
  display: block;
  padding: 0.55rem 1.1rem 0;
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

/* "Load more" UI */
body.page-shorts .shorts-loadmore-wrap{
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  align-items: center;
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

body.page-shorts .shorts-loadmore:hover{
  opacity: 0.9;
}

body.page-shorts .shorts-loadmore:disabled{
  opacity: 0.6;
  cursor: default;
}

body.page-shorts .shorts-note{
  font-size: 0.85em;
  color: var(--muted);
}
</style>

<script>
(() => {
  const BATCH = 20;        // how many to reveal per click
  const MAX_VISIBLE = 60;  // keep only this many cards in DOM
  const HARD_LIMIT = 800;  // safety: stop if someone has absurd amounts

  function initShorts() {
    const marker = document.querySelector(".page-marker[data-page='shorts']");
    if (!marker) return;

    document.body.classList.add("page-shorts");

    const list = document.querySelector("ul.embedded.blog-posts");
    if (!list) return;

    // Work on a live array of <li> currently in DOM
    let items = Array.from(list.querySelectorAll(":scope > li")).slice(0, HARD_LIMIT);

    // 1) Inject date permalink under media (idempotent)
    function ensurePermalink(li) {
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
    }

    items.forEach(ensurePermalink);

    // 2) Show only first batch initially; remove the rest from DOM immediately
    //    (This is the key: we don't keep 500 cards hidden; we remove them.)
    let cursor = Math.min(BATCH, items.length);
    const stash = items.slice(cursor);       // not in DOM yet
    const visible = items.slice(0, cursor);  // in DOM
    stash.forEach(li => li.remove());        // detach from DOM

    // We will append from stash on demand
    function visibleCount() {
      return list.querySelectorAll(":scope > li").length;
    }

    function remainingCount() {
      return stash.length;
    }

    // Remove oldest visible cards until <= MAX_VISIBLE
    function trimOldestIfNeeded() {
      let over = visibleCount() - MAX_VISIBLE;
      if (over <= 0) return;

      // remove oldest (top) cards
      while (over > 0) {
        const first = list.querySelector(":scope > li");
        if (!first) break;
        first.remove();
        over--;
      }
    }

    // UI
    const wrap = document.createElement("div");
    wrap.className = "shorts-loadmore-wrap";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "shorts-loadmore";

    const note = document.createElement("span");
    note.className = "shorts-note";

    wrap.appendChild(btn);
    wrap.appendChild(note);

    list.insertAdjacentElement("afterend", wrap);

    function updateUI() {
      const remaining = remainingCount();
      if (remaining <= 0) {
        wrap.remove();
        return;
      }
      const next = Math.min(BATCH, remaining);
      btn.textContent = `Mehr laden (${next})`;

      // Tell the truth: we unload old stuff
      note.textContent = `Es bleiben max. ${MAX_VISIBLE} sichtbar (ältere werden entladen).`;
    }

    function revealNextBatch() {
      btn.disabled = true;

      const count = Math.min(BATCH, stash.length);
      for (let i = 0; i < count; i++) {
        const li = stash.shift(); // oldest remaining
        if (!li) break;

        // safety: permalink injection might be missing if template changed
        ensurePermalink(li);

        list.appendChild(li);
      }

      trimOldestIfNeeded();

      btn.disabled = false;
      updateUI();
    }

    btn.addEventListener("click", revealNextBatch);
    updateUI();
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
