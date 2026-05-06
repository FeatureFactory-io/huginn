/* Enable GitLab datasource step-2 actions based on inputs and test feedback. */
(() => {
  const form = document.getElementById("ds-create-form-step2");
  if (!form) return;

  const testBtn = document.querySelector('[data-testid="datasource-test-connection"]');
  const saveBtn = document.querySelector('[data-testid="datasource-save"]');
  const urlInput = form.querySelector('[name="base_url"]');
  const tokenInput = form.querySelector('[name="token"]');

  function syncTestEnabled() {
    if (!testBtn || !urlInput || !tokenInput) return;
    const ok = urlInput.value.trim().length > 0 && tokenInput.value.trim().length > 0;
    testBtn.disabled = !ok;
  }

  function syncSaveEnabled() {
    if (!saveBtn) return;
    const success = document.querySelector('[data-testid="datasource-test-result"].alert-success');
    saveBtn.disabled = !success;
    saveBtn.dataset.afterSuccessfulTest = success ? "true" : "false";
  }

  syncTestEnabled();
  syncSaveEnabled();

  form.addEventListener("input", () => {
    syncTestEnabled();
    if (saveBtn && saveBtn.dataset.afterSuccessfulTest === "true") {
      saveBtn.disabled = true;
      saveBtn.dataset.afterSuccessfulTest = "false";
    }
  });
})();
