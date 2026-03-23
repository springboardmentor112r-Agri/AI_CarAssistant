"""
Email service using Brevo (formerly Sendinblue).
Sends password reset emails via Brevo SMTP API.
Never raises — email failure is logged,
not propagated to user.
"""
import httpx
from app.core.config import settings

def _get_reset_email_html(reset_url: str) -> str:
  """
  Clean, professional reset email HTML.
  Works in all email clients.
  """
  return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width">
  <title>Reset Your Password</title>
</head>
<body style="margin:0;padding:0;background:#0f172a;
             font-family:-apple-system,BlinkMacSystemFont,
             'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#0f172a;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="480" cellpadding="0" cellspacing="0"
               style="background:#1e293b;border-radius:16px;
                      border:1px solid #334155;
                      overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="padding:32px 40px 24px;
                       border-bottom:1px solid #334155;">
              <table cellpadding="0" cellspacing="0">
                <tr>
                  <td style="background:#3b82f6;
                             border-radius:10px;
                             padding:10px 14px;
                             font-size:20px;">
                    &#128196;
                  </td>
                  <td style="padding-left:12px;">
                    <span style="color:#ffffff;
                                 font-size:18px;
                                 font-weight:700;">
                      Contract AI
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 40px;">
              <h1 style="margin:0 0 12px;
                         color:#ffffff;
                         font-size:22px;
                         font-weight:700;">
                Reset your password
              </h1>
              <p style="margin:0 0 24px;
                        color:#94a3b8;
                        font-size:15px;
                        line-height:1.6;">
                We received a request to reset your
                Contract AI password. Click the button
                below to choose a new password.
              </p>
              <p style="margin:0 0 24px;
                        color:#94a3b8;
                        font-size:15px;
                        line-height:1.6;">
                This link expires in
                <strong style="color:#f8fafc;">
                  30 minutes
                </strong>.
              </p>

              <!-- CTA Button -->
              <table cellpadding="0" cellspacing="0"
                     style="margin:0 0 32px;">
                <tr>
                  <td style="background:#3b82f6;
                             border-radius:10px;">
                    <a href="{reset_url}"
                       style="display:inline-block;
                              padding:14px 32px;
                              color:#ffffff;
                              font-size:15px;
                              font-weight:600;
                              text-decoration:none;">
                      Reset Password &#8594;
                    </a>
                  </td>
                </tr>
              </table>

              <!-- Fallback URL -->
              <p style="margin:0 0 8px;
                        color:#64748b;
                        font-size:13px;">
                Or copy this link into your browser:
              </p>
              <p style="margin:0 0 32px;
                        color:#3b82f6;
                        font-size:12px;
                        word-break:break-all;">
                {reset_url}
              </p>

              <!-- Security note -->
              <div style="background:#0f172a;
                          border-radius:10px;
                          padding:16px 20px;
                          border:1px solid #334155;">
                <p style="margin:0;
                          color:#64748b;
                          font-size:13px;
                          line-height:1.6;">
                  &#128274; If you did not request a password
                  reset, you can safely ignore this email.
                  Your password will not change.
                </p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 40px;
                       border-top:1px solid #334155;">
              <p style="margin:0;
                        color:#475569;
                        font-size:12px;
                        text-align:center;">
                Contract AI - This is an automated email,
                please do not reply.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

def send_password_reset_email(
  to_email: str,
  reset_token: str,
) -> bool:
  """
  Send password reset email via Brevo SMTP API.
  SYNC function — safe for BackgroundTasks.
  Returns True if sent, False if failed.
  Never raises.
  """
  try:
    if not settings.BREVO_API_KEY:
      print(
        "[Email] BREVO_API_KEY not set — skipping\n"
        f"[Email] Token for testing: {reset_token}\n"
        f"[Email] Reset URL: {settings.FRONTEND_URL}"
        f"/reset-password?token={reset_token}"
      )
      return False

    reset_url = (
      f"{settings.FRONTEND_URL}"
      f"/reset-password?token={reset_token}"
    )

    print(f"[Email] Sending reset email to {to_email}")
    print(f"[Email] Reset URL: {reset_url}")

    payload = {
      "sender": {
        "name": "Contract AI",
        "email": settings.EMAIL_FROM,
      },
      "to": [{"email": to_email}],
      "subject": "Reset your Contract AI password",
      "htmlContent": _get_reset_email_html(reset_url),
    }

    response = httpx.post(
      "https://api.brevo.com/v3/smtp/email",
      headers={
        "api-key": settings.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      json=payload,
      timeout=15,
    )
    response.raise_for_status()
    result = response.json()

    print(
      f"[Email] Sent to {to_email} "
      f"messageId={result.get('messageId', 'unknown')}"
    )
    return True

  except Exception as e:
    print(f"[Email] Failed: {e}")
    return False
