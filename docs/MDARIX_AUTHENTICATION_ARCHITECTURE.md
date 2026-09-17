# MDARIX Authentication Architecture

R1 provides a local credential provider behind an authentication service abstraction. Future OIDC/SAML providers can implement the same boundary.

Signup creates a pending sandbox account. Passwords are stored only as salted scrypt hashes. Email verification uses random, single-use, time-limited tokens stored by hash; the development response exposes a controlled test token only for R1 test delivery and production email delivery remains a deployment dependency.

Sign-in validates credentials and account state, creates an expiring HttpOnly SameSite session cookie, and resolves tenant, user, active role, and effective permissions server-side. Sign-out invalidates the server session. Password reset uses hashed, single-use, time-limited tokens and replaces the password hash; plaintext passwords and tokens are never logged or returned by normal APIs.

Protected APIs must use authenticated context rather than client-submitted tenant/user/role values. Day23 can call a `verify_current_user_password`-equivalent service boundary for controlled approval re-authentication without receiving password hashes.

Known R1 limitations: production transactional email, MFA, SSO, CAPTCHA/rate-limit infrastructure, and full persistent user administration require later deployment/admin work.
