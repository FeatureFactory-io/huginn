(function () {
  const form = document.querySelector('[data-testid="login-form"]');
  const email = document.querySelector('[data-testid="login-email"]');
  const password = document.querySelector('[data-testid="login-password"]');
  const btn = document.querySelector('[data-testid="login-submit"]');
  if (!form || !email || !password || !btn) return;

  function sync() {
    const ok = email.value.trim().length > 0 && password.value.length > 0;
    btn.disabled = !ok;
  }

  email.addEventListener("input", sync);
  password.addEventListener("input", sync);
  sync();

  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
    if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
      new bootstrap.Tooltip(el);
    }
  });
})();
