Feature: AUTH-LOGIN-1 Login to Huginn
  As Commander Donland
  I want to sign in with my email and password
  So that I can access Huginn and manage my projects

  Background:
    Given I am on the Huginn login page at "/"

  # ---------------------------------------------------------------------------
  # Happy path
  # ---------------------------------------------------------------------------

  Scenario: AUTH-LOGIN-01 Successful login redirects to Projects Dashboard
    Given a valid account exists with email "donland@example.com" and password "s3cr3t"
    When I fill in "login-email" with "donland@example.com"
    And I fill in "login-password" with "s3cr3t"
    And I click the "Sign In" button
    Then I am redirected to the Projects Dashboard "DASHBOARD-PROJECTS-1"
    And I am authenticated as "donland@example.com"

  # ---------------------------------------------------------------------------
  # Error handling
  # ---------------------------------------------------------------------------

  Scenario: AUTH-LOGIN-02 Wrong password shows inline error
    Given a valid account exists with email "donland@example.com"
    When I fill in "login-email" with "donland@example.com"
    And I fill in "login-password" with "wrong-password"
    And I click the "Sign In" button
    Then I remain on the login page
    And I see the inline error "Invalid email or password"
    And the password field "login-password" is cleared

  Scenario: AUTH-LOGIN-03 Unknown email shows inline error
    When I fill in "login-email" with "unknown@example.com"
    And I fill in "login-password" with "anypassword"
    And I click the "Sign In" button
    Then I remain on the login page
    And I see the inline error "Invalid email or password"

  Scenario: AUTH-LOGIN-04 Network error shows connectivity message
    Given the Huginn backend is unreachable
    When I fill in "login-email" with "donland@example.com"
    And I fill in "login-password" with "s3cr3t"
    And I click the "Sign In" button
    Then I see the error "Unable to reach Huginn. Check your connection."
    And I remain on the login page

  # ---------------------------------------------------------------------------
  # Validation
  # ---------------------------------------------------------------------------

  Scenario: AUTH-LOGIN-05 Sign In button is disabled until both fields have input
    Given the login form is empty
    Then the "Sign In" button is disabled
    When I fill in "login-email" with "donland@example.com"
    Then the "Sign In" button is still disabled
    When I fill in "login-password" with "s3cr3t"
    Then the "Sign In" button is enabled

  Scenario: AUTH-LOGIN-06 Submitting with blank email shows validation error
    When I leave "login-email" blank
    And I fill in "login-password" with "s3cr3t"
    And I submit the login form
    Then I see a validation message on the "login-email" field

  Scenario: AUTH-LOGIN-07 Submitting with blank password shows validation error
    When I fill in "login-email" with "donland@example.com"
    And I leave "login-password" blank
    And I submit the login form
    Then I see a validation message on the "login-password" field

  # ---------------------------------------------------------------------------
  # Page layout
  # ---------------------------------------------------------------------------

  Scenario: AUTH-LOGIN-08 Login page displays correct layout elements
    Then I see the Huginn wordmark in the header
    And I see the tagline "Human-AI Command Composite"
    And I see an email input with data-testid "login-email"
    And I see a password input with data-testid "login-password"
    And I see the "Sign In" button
    And I see a "Forgot password?" link that is disabled
    And the "Forgot password?" link has a tooltip containing "Contact your admin"

  Scenario: AUTH-LOGIN-09 Password field masks input by default
    When I fill in "login-password" with "s3cr3t"
    Then the "login-password" input has type "password"

  # ---------------------------------------------------------------------------
  # Session / redirect
  # ---------------------------------------------------------------------------

  Scenario: AUTH-LOGIN-10 Already-authenticated user is redirected away from login
    Given I am already authenticated as "donland@example.com"
    When I navigate to the login page at "/"
    Then I am redirected to the Projects Dashboard "DASHBOARD-PROJECTS-1"

  Scenario: AUTH-LOGIN-11 Logging out clears session and returns to login page
    Given I am authenticated as "donland@example.com"
    When I click the logout control
    Then I am redirected to the login page
    And I am no longer authenticated

  # ---------------------------------------------------------------------------
  # Accessibility
  # ---------------------------------------------------------------------------

  Scenario: AUTH-LOGIN-12 Login form is keyboard-navigable
    When I press Tab from the email field
    Then focus moves to the password field
    When I press Tab from the password field
    Then focus moves to the "Sign In" button
    When I press Enter on the "Sign In" button
    Then the form is submitted

  Scenario: AUTH-LOGIN-13 Login form fields have accessible labels
    Then the "login-email" input has an associated label or aria-label
    And the "login-password" input has an associated label or aria-label
    And the "Sign In" button has a discernible text label
