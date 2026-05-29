/* Edit datasource: Replace Token toggle only. Buttons match create — always enabled. */
(() => {
  const form = document.getElementById("ds-form");
  if (!form) return;

  const replaceBtn = document.querySelector('[data-testid="datasource-replace-token-btn"]');
  if (!replaceBtn) return;

  const placeholder = document.getElementById("token-placeholder-section");
  const newSection = document.getElementById("new-token-section");
  const replaceFlag = form.querySelector('[name="replace_token"]');
  const newTok = form.querySelector('[name="new_token"]');

  replaceBtn.addEventListener("click", () => {
    placeholder?.classList.add("d-none");
    newSection?.classList.remove("d-none");
    if (replaceFlag) replaceFlag.value = "1";
    newTok?.focus();
  });
})();
