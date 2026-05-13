Feature: Act 0 — Registration, verification, approval, moderation
  As Commander Donland
  I want to register on a dev sandbox, verify my email, and be approved by an admin
  So that I can sign in to Huginn after onboarding

  # ESM Activity 05 (feature files): Huginn uses Screen IDs `{ENTITY}-{OPERATION}-{VERSION}` and
  # scenarios `AUTH-{…}-{NN}` / `USERS-{…}-{NN}` — not the Mimir `FOB-*` prefix from `.cursor/workflows/ESM-reference/ESM-reference-05-Write_Feature_Files.md`.

  # Covers journeys in docs/features/user_journey.md § Act 0 — screens AUTH-LOGIN-1 (signup edges),
  # AUTH-REGISTER-1, AUTH-AWAIT_VERIFICATION-1, AUTH-VERIFY_EMAIL-1, AUTH-AWAIT_APPROVAL-1.
  # Admin moderation (approve/reject) is performed via Django admin (/admin/) — no custom product screens.

  Background:
    Given the outbound email backend is observable for assertions

  # ---------------------------------------------------------------------------
  # DEBUG gating and login entry (AUTH-LOGIN-1 alignment)
  # ---------------------------------------------------------------------------

  Scenario: AUTH-REG-LOGIN-01 DEV shows Create account and navigates to register
    Given settings DEBUG is enabled
    And I am on the Huginn login page at "/"
    Then I see a link with data-testid "login-register-link"

  Scenario: AUTH-REG-LOGIN-02 Production hides Create account link
    Given settings DEBUG is disabled
    And I am on the Huginn login page at "/"
    Then I do not see a link with data-testid "login-register-link"
    And I see the muted helper text containing "Need an account? Contact your admin."

  Scenario: AUTH-REG-LOGIN-03 Direct register URL redirects when signup disabled
    Given settings DEBUG is disabled
    When I open the registration URL "AUTH-REGISTER-1"
    Then I am redirected to "AUTH-LOGIN-1"
    And I see a dismissable banner containing "Registration is disabled on this Huginn install. Contact your admin to request an account."

  # Scenarios 04-06: DEBUG setting is irrelevant here — login status messaging applies to all installs.
  # These users were seeded directly by the test; how their accounts were created does not matter.
  Scenario: AUTH-REG-LOGIN-04 Valid credentials pending email verification show resend prompt
    Given a user exists in state "pending_email_verification" with email "signup@example.com" and password "R3g-str0ng-pass"
    And I am on the Huginn login page at "/"
    When I fill in "login-email" with "signup@example.com"
    And I fill in "login-password" with "R3g-str0ng-pass"
    And I click the "Sign In" button
    Then I remain on the login page "AUTH-LOGIN-1"
    And I see a notice containing "Your email isn't verified yet. We sent a verification link to signup@example.com."
    And I see a rate-limited control labelled "Resend verification email"

  Scenario: AUTH-REG-LOGIN-05 Valid credentials pending admin approval show waiting message
    Given a user exists in state "pending_admin_approval" with email "signup@example.com" and password "R3g-str0ng-pass"
    And I am on the Huginn login page at "/"
    When I fill in "login-email" with "signup@example.com"
    And I fill in "login-password" with "R3g-str0ng-pass"
    And I click the "Sign In" button
    Then I remain on the login page "AUTH-LOGIN-1"
    And I see a notice containing "Your account is verified and waiting for admin approval. You'll receive an email once it's reviewed."

  Scenario: AUTH-REG-LOGIN-06 Valid credentials rejected account show rejection notice
    Given a user exists in state "rejected" with email "signup@example.com" and password "R3g-str0ng-pass"
    And I am on the Huginn login page at "/"
    When I fill in "login-email" with "signup@example.com"
    And I fill in "login-password" with "R3g-str0ng-pass"
    And I click the "Sign In" button
    Then I remain on the login page "AUTH-LOGIN-1"
    And I see a notice containing "Your account application was not approved. Please contact your admin if you believe this is an error."

  # Banner after approval: anonymous user earns the banner by opening Email 3’s sign-in URL (flash/redirect)—not guessed from session alone.
  Scenario: AUTH-REG-LOGIN-07 Welcome banner after following account-approved email sign-in link
    Given I am not authenticated
    When I follow the sign-in URL from Email 3 "Your Huginn account is approved"
    Then I am on the Huginn login page at "/"
    And I see a dismissable banner containing "Your account is approved — welcome to Huginn. Sign in to get started."

  # ---------------------------------------------------------------------------
  # AUTH-REGISTER-1 — form and flows
  # ---------------------------------------------------------------------------

  # Sprint "Registration" (milestone): simplified flow — no email verification, no admin approval.
  # Account is created with is_active=True and the user is immediately signed in.
  Scenario: AUTH-REGISTER-01 Successful submit creates active account and redirects to Tactical Plot
    Given settings DEBUG is enabled
    And no user exists with email "fresh@example.com"
    And I am on screen "AUTH-REGISTER-1"
    When I fill in "register-name" with "Commander Casey"
    And I fill in "register-email" with "fresh@example.com"
    And I fill in "register-password" with "Abcd-valid-987"
    And I fill in "register-password-confirm" with "Abcd-valid-987"
    And I click the button with data-testid "register-submit"
    Then a User exists with email "fresh@example.com" and is_active true
    And I am authenticated as "fresh@example.com"
    And I am redirected to the Tactical Plot "DASHBOARD-PROJECTS-1"

  Scenario: AUTH-REGISTER-02 Create account stays disabled until all fields valid client-side
    Given settings DEBUG is enabled
    And I am on screen "AUTH-REGISTER-1"
    And the registration form fields are empty
    Then the button with data-testid "register-submit" is disabled

  Scenario: AUTH-REGISTER-03 Password mismatch shows helper text under confirm
    Given settings DEBUG is enabled
    And I am on screen "AUTH-REGISTER-1"
    When I fill in "register-name" with "Commander Casey"
    And I fill in "register-email" with "fresh@example.com"
    And I fill in "register-password" with "Abcd-valid-987"
    And I fill in "register-password-confirm" with "different-password"
    Then I see mismatch helper text on the confirm password field "register-password-confirm"

  Scenario: AUTH-REGISTER-04 Server rejects weak password and shows inline validation
    Given settings DEBUG is enabled
    And I am on screen "AUTH-REGISTER-1"
    When I submit the registration form with name "Bad", email "pw@example.com", password "12345", confirmation "12345"
    Then I remain on screen "AUTH-REGISTER-1"
    And I see a server-side validation error for the password strength rules
    And no outbound email was sent with subject "Verify your email for Huginn"

  Scenario: AUTH-REGISTER-05 Sign-in link returns to login screen
    Given settings DEBUG is enabled
    And I am on screen "AUTH-REGISTER-1"
    When I click the link with text matching "Sign in"
    Then I am on screen "AUTH-LOGIN-1"

  Scenario: AUTH-REGISTER-06 Duplicate pending-verification email re-sends verification link silently
    Given settings DEBUG is enabled
    And a user exists in state "pending_email_verification" with email "dup@example.com"
    And I am on screen "AUTH-REGISTER-1"
    When I submit the registration form with name "Another", email "dup@example.com", password "Abcd-valid-987", confirmation "Abcd-valid-987"
    Then I am on screen "AUTH-AWAIT_VERIFICATION-1"
    And the screen shows generic success copy with no enumeration of prior state
    And an outbound SES email was sent with subject "Verify your email for Huginn"

  Scenario: AUTH-REGISTER-08 Already-active email shows same generic success screen with no enumeration
    # Enumeration protection: active/pending_admin_approval/rejected accounts must not be
    # distinguishable from a fresh signup at the UI level. A context-appropriate email is sent instead.
    Given settings DEBUG is enabled
    And a user exists in state "active" with email "existing@example.com"
    And I am on screen "AUTH-REGISTER-1"
    When I submit the registration form with name "Intruder", email "existing@example.com", password "Abcd-valid-987", confirmation "Abcd-valid-987"
    Then I am on screen "AUTH-AWAIT_VERIFICATION-1"
    And the screen shows generic success copy with no enumeration of prior state
    And no outbound email was sent with subject "Verify your email for Huginn"

  Scenario: AUTH-REGISTER-07 Connectivity error shows retry banner keeping non-secret fields
    Given settings DEBUG is enabled
    And the Huginn backend rejects registration transiently
    And I am on screen "AUTH-REGISTER-1"
    When I submit the registration form with name "Lonely", email "solo@example.com", password "Abcd-valid-987", confirmation "Abcd-valid-987"
    Then I see the banner error "Unable to create account right now. Please try again."
    And the field "register-name" still contains "Lonely"

  # ---------------------------------------------------------------------------
  # AUTH-AWAIT_VERIFICATION-1
  # ---------------------------------------------------------------------------

  Scenario: AUTH-AWAIT_VERIFICATION-01 Resend invokes rate-limit feedback
    Given settings DEBUG is enabled
    And I landed on screen "AUTH-AWAIT_VERIFICATION-1" after registering "await@example.com"
    When I click the button with data-testid "resend-verification"
    Then I see text containing "Sent. You can resend in"

  Scenario: AUTH-AWAIT_VERIFICATION-02 Back to sign in navigates to login
    Given settings DEBUG is enabled
    And I am on screen "AUTH-AWAIT_VERIFICATION-1" for email "await@example.com"
    When I click the link with text "Back to sign in"
    Then I am on screen "AUTH-LOGIN-1"

  Scenario: AUTH-AWAIT_VERIFICATION-03 Direct visit without pending session redirects home to login gate
    Given settings DEBUG is enabled
    And I have no active pending registration cookie or token for this browser
    When I open screen "AUTH-AWAIT_VERIFICATION-1"
    Then I am redirected to "AUTH-LOGIN-1"

  # ---------------------------------------------------------------------------
  # AUTH-VERIFY_EMAIL-1 — link consumption
  # ---------------------------------------------------------------------------

  Scenario: AUTH-VERIFY_EMAIL-01 Valid verification link verifies and shows email-verified messaging
    Given settings DEBUG is enabled
    And a user exists in state "pending_email_verification" with email "tok@example.com"
    When I visit the emailed verification URL for email "tok@example.com"
    Then I see the title "Email verified"
    And I see body text containing "Your account now needs to be approved by an admin."
    And an outbound SES email was sent with subject "Your Huginn account is awaiting admin approval"

  Scenario: AUTH-VERIFY_EMAIL-02 Expired verification link shows resend form
    Given settings DEBUG is enabled
    And verification link for email "exp@example.com" is older than 24 hours
    When I visit the expired verification URL for email "exp@example.com"
    Then I see the title "Link expired"
    And I see body text containing "request a new one"
    And I see a single-field email form labelled for resending verification

  Scenario: AUTH-VERIFY_EMAIL-03 Already verified shows already-verified messaging without second awaiting email
    Given settings DEBUG is enabled
    And a user exists in state "pending_admin_approval" with email "done@example.com"
    When I revisit a previously-used verification URL for email "done@example.com"
    Then I see the title "Already verified"
    And no additional outbound email was sent with subject "Your Huginn account is awaiting admin approval"

  Scenario: AUTH-VERIFY_EMAIL-04 Garbage token shows neutral unrecognised state
    Given settings DEBUG is enabled
    When I visit verification URL "/auth/verify/" with unknown token garbage
    Then I see the title "Link not recognised"
    And I see a secondary action to navigate to login

  # ---------------------------------------------------------------------------
  # AUTH-AWAIT_APPROVAL-1
  # ---------------------------------------------------------------------------

  Scenario: AUTH-AWAIT_APPROVAL-01 Shows approval-hold messaging
    Given settings DEBUG is enabled
    And a user exists in state "pending_admin_approval" with email "hold@example.com"
    And my session has the pending-approval context for email "hold@example.com"
    When I navigate to screen "AUTH-AWAIT_APPROVAL-1"
    Then I see the title "Hold tight — admin approval pending"
    And I see body text containing "We'll email you (hold@example.com)"

  Scenario: AUTH-AWAIT_APPROVAL-02 Direct visit without qualifying context redirects to login
    Given settings DEBUG is enabled
    When I open screen "AUTH-AWAIT_APPROVAL-1"
    Then I am redirected to "AUTH-LOGIN-1"

  # ---------------------------------------------------------------------------
  # Admin moderation — via Django admin (/admin/), not custom product screens
  # ---------------------------------------------------------------------------

  Scenario: ADMIN-APPROVE-01 Django admin Approve action activates user and sends approval email
    Given I am authenticated as Django staff user "ops@example.com"
    And a user exists in state "pending_admin_approval" with email "yes@example.com" and display name "Yesenia"
    When I run the Django admin "Approve selected users" action on user "yes@example.com"
    Then user "yes@example.com" is in state "active" with Django is_active true
    And an outbound SES email was sent with subject "Your Huginn account is approved"

  Scenario: ADMIN-REJECT-01 Django admin Reject action keeps user inactive and sends rejection email
    Given I am authenticated as Django staff user "ops@example.com"
    And a user exists in state "pending_admin_approval" with email "no@example.com" and display name "Noland"
    When I run the Django admin "Reject selected users" action on user "no@example.com"
    Then user "no@example.com" is in state "rejected" with Django is_active false
    And an outbound SES email was sent with subject "Your Huginn account request"

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: ACCESS-REG-01 Registration form keyboard order matches visual order
    Given settings DEBUG is enabled
    And I am on screen "AUTH-REGISTER-1"
    When I press Tab sequentially from register-name field
    Then focus order visits "register-email" then "register-password" then "register-password-confirm" before "register-submit"
