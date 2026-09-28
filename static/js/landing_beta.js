/**
 * Opens the landing beta modal and posts the form through HuginnBeta.submitRegistration.
 */
(function () {
  "use strict";

  const OUTCOME_COPY = Object.freeze({
    success: "You're on the list. We'll be in touch.",
    duplicate: "That email is already on the beta list.",
    throttled: "Too many attempts. Please wait a moment and try again.",
    unavailable: "The signup service is unavailable. Please try again shortly.",
    error: "We couldn't add you right now. Please check the address and try again.",
  });

  function initializeBetaDialog() {
    const dialog = document.querySelector('[data-testid="beta-dialog"]');
    if (!dialog) return;
    document.querySelectorAll("[data-open-beta]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        event.preventDefault();
        openDialog(dialog);
      });
    });
    bindBetaForm(dialog);
    console.log("[beta] landing dialog ready");
  }

  function openDialog(dialog) {
    if (typeof bootstrap === "undefined" || !bootstrap.Modal) {
      console.log("[beta] bootstrap modal unavailable");
      return;
    }
    const modal = bootstrap.Modal.getOrCreateInstance(dialog);
    dialog.addEventListener(
      "shown.bs.modal",
      function () {
        const email = dialog.querySelector("input[name='email']");
        if (email) email.focus();
      },
      { once: true }
    );
    modal.show();
  }

  function bindBetaForm(dialog) {
    const form = dialog.querySelector("[data-beta-form]");
    if (!(form instanceof HTMLFormElement)) return;
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      handleSubmission(form);
    });
  }

  function handleSubmission(form) {
    const email = form.elements.namedItem("email");
    const consent = form.elements.namedItem("consent");
    const button = form.querySelector("button[type='submit']");
    const status = form.querySelector("[role='status']");
    if (!(email instanceof HTMLInputElement) || !(consent instanceof HTMLInputElement) || !button || !status) {
      return;
    }
    if (!validateForm(email, consent, status)) return;
    if (!window.HuginnBeta || typeof window.HuginnBeta.submitRegistration !== "function") {
      status.textContent = OUTCOME_COPY.unavailable;
      console.log("[beta] registration module missing");
      return;
    }
    setSubmitting(button, status, true);
    window.HuginnBeta.submitRegistration(email.value, form.dataset.endpoint)
      .then(function (outcome) {
        presentOutcome(outcome, button, status);
      })
      .catch(function (error) {
        status.textContent = error instanceof Error ? error.message : OUTCOME_COPY.error;
        button.disabled = false;
        button.textContent = "Join the beta";
        dispatchRegistrationOutcome("error");
        console.log("[beta] submission rejected", error);
      });
  }

  function validateForm(email, consent, status) {
    if (!email.checkValidity()) {
      email.focus();
      status.textContent = "Enter a valid email address.";
      return false;
    }
    if (!consent.checked) {
      consent.focus();
      status.textContent = "Please agree to receive beta updates.";
      return false;
    }
    return true;
  }

  function setSubmitting(button, status, isSubmitting) {
    button.disabled = isSubmitting;
    button.textContent = isSubmitting ? "Joining…" : "Join the beta";
    if (isSubmitting) status.textContent = "Submitting your request…";
  }

  function presentOutcome(outcome, button, status) {
    status.textContent = OUTCOME_COPY[outcome] || OUTCOME_COPY.error;
    const complete = outcome === "success" || outcome === "duplicate";
    button.disabled = complete;
    button.textContent = complete ? "Request received" : "Join the beta";
    dispatchRegistrationOutcome(outcome);
    console.log("[beta] outcome=" + outcome);
  }

  function dispatchRegistrationOutcome(outcome) {
    window.dispatchEvent(new CustomEvent("ff:registration-outcome", { detail: { outcome: outcome } }));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeBetaDialog);
  } else {
    initializeBetaDialog();
  }
})();
