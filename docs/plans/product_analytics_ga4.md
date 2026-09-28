# Consent-gated product analytics

## Contract

Huginn is a long-horizon product-to-market experiment. GA4 records anonymous
behavioural milestones on the public landing journey; Huginn and the registration
service remain authoritative for product and beta state. Analytics must not read
form values, customer content, credentials, tokens, or query strings.

## Skeleton and pseudocode

1. Render stable product, experiment, hypothesis, and variant IDs on public
   pages only.
2. Ask for analytics consent before loading the Google tag.
3. On allow, configure GA4 without advertising signals and send a manual,
   query-free page view.
4. Record named CTA, feature, and registration-start events.
5. Dispatch the registration service outcome and emit `sign_up` only for a
   confirmed `success` response.
6. Verify guest, authenticated, feature, outcome, and source-privacy paths.

## Release gates

- Local tests passing does not mean deployed.
- Pipeline deployment does not mean GA4 live data is verified.
- DebugView and Realtime evidence are required before enabling campaigns.
