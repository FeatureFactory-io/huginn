(function () {
  const form = document.querySelector("form.projects-import-shell");
  if (!form) return;

  const search = form.querySelector('[data-testid="projects-import-search"]');
  const selectAll = form.querySelector('[data-testid="projects-import-select-all"]');
  const bulkBar = form.querySelector('[data-testid="projects-import-bulk-bar"]');
  const bulkCount = form.querySelector('[data-testid="projects-import-bulk-count"]');
  const btnBulk = document.getElementById("projects-import-selected-btn");
  const btnFooter = document.getElementById("projects-import-submit-footer");
  const rowChecks = () => Array.from(form.querySelectorAll("input.js-import-row-check:not(:disabled)"));

  function visibleRows() {
    return Array.from(form.querySelectorAll("tbody tr[data-import-row]")).filter((tr) => tr.style.display !== "none");
  }

  function selectedEligible() {
    return rowChecks().filter((cb) => cb.checked);
  }

  function syncUi() {
    const n = selectedEligible().length;
    const plural = n === 1 ? "" : "s";
    if (bulkCount) bulkCount.textContent = `${n} selected`;
    const showBar = n > 0;
    if (bulkBar) {
      bulkBar.classList.toggle("d-none", !showBar);
      bulkBar.classList.toggle("d-flex", showBar);
    }
    [btnBulk, btnFooter].forEach((b) => {
      if (b) b.disabled = n === 0;
    });
  }

  function syncSelectAll() {
    if (!selectAll) return;
    const eligible = visibleRows().flatMap((tr) => Array.from(tr.querySelectorAll("input.js-import-row-check")));
    if (eligible.length === 0) {
      selectAll.checked = false;
      selectAll.indeterminate = false;
      return;
    }
    const checked = eligible.filter((cb) => cb.checked).length;
    selectAll.checked = checked === eligible.length;
    selectAll.indeterminate = checked > 0 && checked < eligible.length;
  }

  if (search) {
    search.addEventListener("input", () => {
      const q = search.value.trim().toLowerCase();
      form.querySelectorAll("tbody tr[data-import-row]").forEach((tr) => {
        const hay = (tr.getAttribute("data-search-text") || "").toLowerCase();
        tr.style.display = !q || hay.includes(q) ? "" : "none";
      });
      syncSelectAll();
      syncUi();
    });
  }

  if (selectAll) {
    selectAll.addEventListener("change", () => {
      const on = selectAll.checked;
      visibleRows().forEach((tr) => {
        tr.querySelectorAll("input.js-import-row-check").forEach((cb) => {
          cb.checked = on;
        });
      });
      syncUi();
    });
  }

  form.querySelectorAll("input.js-import-row-check").forEach((cb) => {
    cb.addEventListener("change", () => {
      syncSelectAll();
      syncUi();
    });
  });

  syncSelectAll();
  syncUi();
})();
