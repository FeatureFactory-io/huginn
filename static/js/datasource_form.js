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

(() => {
  const form = document.getElementById("ds-edit-form");
  if (!form) return;

  const replaceBtn = document.querySelector('[data-testid="datasource-replace-token-btn"]');
  const placeholder = document.getElementById("token-placeholder-section");
  const newSection = document.getElementById("new-token-section");
  const replaceFlag = form.querySelector('[name="replace_token"]');
  const newTok = form.querySelector('[name="new_token"]');
  const urlInput = form.querySelector('[name="base_url"]');
  const testBtn = form.querySelector('[data-testid="datasource-test-connection"]');
  const saveBtn = document.querySelector('[data-testid="datasource-save"]');

  function syncTestEnabled() {
    if (!testBtn || !urlInput) return;
    const urlOk = urlInput.value.trim().length > 0;
    const replacing = replaceFlag && replaceFlag.value === "1";
    if (replacing) {
      const tok = (newTok && newTok.value.trim()) || "";
      testBtn.disabled = !urlOk || !tok;
    } else {
      testBtn.disabled = !urlOk;
    }
  }

  function syncSaveEnabled() {
    if (!saveBtn) return;
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
  });
})();
