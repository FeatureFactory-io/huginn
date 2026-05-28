/* Edit datasource: test-before-save when replacing token. Create wizard needs no JS. */
(() => {
  const form = document.getElementById("ds-edit-form");
  if (!form) return;

  const replaceBtn = document.querySelector('[data-testid="datasource-replace-token-btn"]');
  const placeholder = document.getElementById("token-placeholder-section");
  const newSection = document.getElementById("new-token-section");
  const replaceFlag = form.querySelector('[name="replace_token"]');
  const newTok = form.querySelector('[name="new_token"]');
  const testBtn = form.querySelector('[data-testid="datasource-test-connection"]');
  const saveBtn = document.querySelector('[data-testid="datasource-save"]');

  function syncTestEnabled() {
    if (!testBtn) return;
    const urlInput = form.querySelector('[name="base_url"]');
    const urlOk = !urlInput || urlInput.value.trim().length > 0;
    const replacing = replaceFlag && replaceFlag.value === "1";
    if (replacing) {
      const tok = (newTok && newTok.value.trim()) || "";
      testBtn.disabled = !urlOk || !tok;
    } else {
      testBtn.disabled = false;
    }
  }

  function syncSaveEnabled() {
    if (!saveBtn) return;
    const replacing = replaceFlag && replaceFlag.value === "1";
    if (!replacing) {
      saveBtn.disabled = false;
      return;
    }
    const success = document.querySelector('[data-testid="datasource-edit-test-result"].alert-success');
    saveBtn.disabled = !success;
    saveBtn.dataset.afterSuccessfulTest = success ? "true" : "false";
  }

  replaceBtn?.addEventListener("click", () => {
    placeholder?.classList.add("d-none");
    newSection?.classList.remove("d-none");
    if (replaceFlag) replaceFlag.value = "1";
    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.dataset.afterSuccessfulTest = "false";
    }
    syncTestEnabled();
  });

  syncTestEnabled();
  syncSaveEnabled();

  form.addEventListener("input", () => {
    syncTestEnabled();
    if (saveBtn && saveBtn.dataset.afterSuccessfulTest === "true") {
      saveBtn.disabled = true;
      saveBtn.dataset.afterSuccessfulTest = "false";
    }
    syncSaveEnabled();
  });
})();
