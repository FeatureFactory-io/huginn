/**
 * Client registration against the production aws-factory POST /registrations route.
 * Mirrors heimdall-site dist/assets/registration.mjs with Huginn experiment ids.
 */
(function (global) {
  "use strict";

  const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const REQUEST_TIMEOUT_MS = 8000;
  const FACTORY_ENDPOINT = "https://dnucu9yrr1.execute-api.us-east-1.amazonaws.com/registrations";

  const DEFAULT_DEPENDENCIES = Object.freeze({
    fetcher: global.fetch.bind(global),
    createIdempotencyKey: function () {
      if (global.crypto && typeof global.crypto.randomUUID === "function") {
        return global.crypto.randomUUID();
      }
      return "huginn-" + Date.now();
    },
    logger: console,
  });

  /**
   * Validate and normalize one email at the UI boundary.
   *
   * :param email: Untrusted visitor input. Example: "Ada@Example.com"
   * :return: Lowercase address ready for submission. Example: "ada@example.com"
   * :raises Error: When the address is empty or malformed.
   */
  function validateEmail(email) {
    const normalizedEmail = String(email == null ? "" : email).trim().toLowerCase();
    if (!EMAIL_PATTERN.test(normalizedEmail)) {
      throw new Error("Enter a valid email address.");
    }
    return normalizedEmail;
  }

  /**
   * Build the immutable aws-factory registration payload.
   *
   * :param email: Valid visitor email address. Example: "ada@example.com"
   * :return: Factory registration contract. Example: {experimentId: "exp-huginn-beta-001", email: "ada@example.com"}
   * :raises Error: When the address is malformed.
   */
  function createRegistrationPayload(email) {
    return Object.freeze({
      experimentId: "exp-huginn-beta-001",
      hypothesisId: "hyp-command-composite-demand-001",
      email: validateEmail(email),
      consent: true,
      synthetic: false,
      journeyId: "jrn-huginn-landing-001",
      variantId: "var-landing-001",
      sourceId: "src-direct",
      mediumId: "med-website",
      campaignId: "cmp-huginn-beta-001",
      contentId: "cnt-hero-001",
      termId: "term-none",
    });
  }

  /**
   * Map HTTP status to copy-safe UI state.
   *
   * :param status: HTTP response status. Example: 200
   * :return: Stable outcome key. Example: "success"
   */
  function mapStatusToOutcome(status) {
    if (status >= 200 && status < 300) return "success";
    if (status === 409) return "duplicate";
    if (status === 429) return "throttled";
    if (status === 502 || status === 503 || status === 504) return "unavailable";
    return "error";
  }

  /**
   * Submit one beta registration with a bounded timeout.
   *
   * :param email: Visitor email address. Example: "ada@example.com"
   * :param endpoint: Absolute HTTPS aws-factory registration URL. Example: FACTORY_ENDPOINT
   * :param dependencies: Explicit network, identifier, and logging dependencies.
   * :return: Safe outcome key; response bodies are never trusted. Example: "success"
   */
  function submitRegistration(email, endpoint, dependencies) {
    const resolvedEndpoint = endpoint || FACTORY_ENDPOINT;
    const resolvedDependencies = dependencies || DEFAULT_DEPENDENCIES;
    validateEndpoint(resolvedEndpoint);
    const payload = createRegistrationPayload(email);
    const idempotencyKey = resolvedDependencies.createIdempotencyKey();
    console.log("[beta] submitting registration experimentId=" + payload.experimentId);
    return postRegistration(resolvedEndpoint, payload, idempotencyKey, resolvedDependencies.fetcher)
      .then(function (response) {
        const outcome = mapStatusToOutcome(response.status);
        resolvedDependencies.logger.info("huginn_beta_registration", {
          experimentId: payload.experimentId,
          outcome: outcome,
        });
        return outcome;
      })
      .catch(function (error) {
        const errorType = error && error.name ? error.name : "Error";
        resolvedDependencies.logger.info("huginn_beta_registration_unavailable", { errorType: errorType });
        resolvedDependencies.logger.info("huginn_beta_registration", {
          experimentId: payload.experimentId,
          outcome: "unavailable",
        });
        return "unavailable";
      });
  }

  function validateEndpoint(endpoint) {
    const parsedEndpoint = new URL(endpoint);
    if (parsedEndpoint.protocol !== "https:" || parsedEndpoint.username || parsedEndpoint.password) {
      throw new Error("Registration endpoint must be a credential-free HTTPS URL.");
    }
  }

  function postRegistration(endpoint, payload, idempotencyKey, fetcher) {
    const init = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify(payload),
    };
    if (typeof AbortSignal !== "undefined" && typeof AbortSignal.timeout === "function") {
      init.signal = AbortSignal.timeout(REQUEST_TIMEOUT_MS);
    }
    return fetcher(endpoint, init);
  }

  global.HuginnBeta = Object.freeze({
    FACTORY_ENDPOINT: FACTORY_ENDPOINT,
    validateEmail: validateEmail,
    createRegistrationPayload: createRegistrationPayload,
    mapStatusToOutcome: mapStatusToOutcome,
    submitRegistration: submitRegistration,
  });
})(window);
