# Administrator access

The URL remains `/admin/`. Every admin view now requires an active staff account AND an OTP-verified session. Ordinary `/accounts/login/` sessions cannot bypass that check. Player login remains separate.

## Deploy and activate

1. Commit and deploy the updated requirements and code. Run `python manage.py migrate` (the normal deployment startup already does this).
2. Open `/admin/`; it redirects to `/staff-auth/account/login/`.
3. Sign in with your existing administrator username/password. If this account has no authenticator, you will be sent to setup.
4. On your own device, scan the QR code with an authenticator and enter its current code. Never send the QR, setup secret or codes in chat.
5. Open **Seguridad y recuperación**, generate backup tokens and store them privately offline. Each token works once. Do this before relying on the authenticator.
6. Sign out and sign in again to verify password + authenticator access.

No production administrator has been enrolled by the code changes. Enrollment must be completed by the account owner after deployment; the admin will deny password-only access until then.

## Login limits and recovery

Five failed password attempts pause that username for 15 minutes, across workers and IP changes. Attempts during the pause do not extend it. OTP failures also use django-otp's device throttle. The username-based limit avoids locking all visitors behind Render's shared proxy IP. A successful password login clears previous password failures. No external email or SMS is configured.

If you lose your authenticator, select the backup-token option during MFA login. If temporarily locked out, wait 15 minutes, or use your authenticated Render shell to run `python manage.py axes_reset_username YOUR_USERNAME`. This only clears failed password attempts; it does not bypass MFA.

If you lose both the authenticator and all recovery tokens, use trusted Render shell access to inspect/delete only your own lost OTP device and repeat enrollment. This is an exceptional account recovery operation; do not disable MFA globally or delete other users' devices. Protect your Render and GitHub accounts with MFA too.

Library migrations belong to axes, otp_totp, otp_static and two_factor. There is no new Gchess model migration. Requirements use Django 6.0.9 (security update within the existing 6.0 series), django-axes and django-two-factor-auth with TOTP and one-use recovery tokens.
