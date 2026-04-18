/* ==========================================================================
   Single source of truth for every count shown across the site.
   Every page that has a number on it loads this file via
      <script src="…/assets/counts.js"></script>
   and marks the number's DOM node with `data-count="<path>"`.
   On load, the script below rewrites every matching element with the value
   from the object. HTML retains the fallback number as static text so the
   page still reads correctly if JS fails.
   ========================================================================== */

window.COUNTS = {
  // Top-level archive counts (shown on the landing)
  stories: 44,
  quizzes: 29,
  questions: 295,
  guides: 10,
  categories: 4,

  // Practice hub
  avg: 10,   // ~avg questions per quiz

  // Library folder sizes
  folder: {
    "cheat-sheets": 3,
    "deep-dives": 2,
    "roadmaps-and-project-ideas": 3,
    "unity-hacks": 2,
  },
};

/* --------------------------------------------------------------------------
   Populate any element with `data-count="<dot.path>"` — e.g.
      <strong data-count="stories">44</strong>
      <span data-count="folder.cheat-sheets">3</span>
   -------------------------------------------------------------------------- */
(function () {
  function populate() {
    const get = (path) =>
      path.split(".").reduce((o, k) => (o == null ? undefined : o[k]), window.COUNTS);
    document.querySelectorAll("[data-count]").forEach((el) => {
      const v = get(el.dataset.count);
      if (v != null) el.textContent = String(v);
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", populate);
  } else {
    populate();
  }
})();
