(function () {
  function bind(form) {
    var debounceMs = parseInt(form.getAttribute("data-hg-list-find-debounce") || "300", 10);

    form.querySelectorAll(".hg-filter-on-change-submit").forEach(function (el) {
      el.addEventListener("change", function () {
        form.requestSubmit();
      });
    });

    form.querySelectorAll(".hg-filter-on-input-submit").forEach(function (el) {
      var timer;
      el.addEventListener("input", function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
          form.requestSubmit();
        }, debounceMs);
      });
      el.addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
          e.preventDefault();
          clearTimeout(timer);
          form.requestSubmit();
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form[data-hg-list-find-auto]").forEach(bind);
  });
})();
