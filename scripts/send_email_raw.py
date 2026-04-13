"""
Send emails using Gmail API directly via gws upload endpoint.
Builds proper MIME message with multiline body and attachments.
Uses --upload with message/rfc822 to avoid command-line length limits.
"""
import subprocess
import sys
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def get_gws_path():
    gws_path = os.path.join(os.environ.get("APPDATA", ""), "npm", "gws.cmd")
    if os.path.exists(gws_path):
        return gws_path
    return "gws"


def send_email(to, subject, body_file, attachments=None):
    # Read body
    with open(body_file, "r", encoding="utf-8") as f:
        body_text = f.read().strip()

    # Build MIME message
    if attachments:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body_text, "plain"))
        for filepath in attachments:
            with open(filepath, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename(filepath)
            part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
            msg.attach(part)
    else:
        msg = MIMEText(body_text, "plain")

    msg["To"] = to
    msg["Subject"] = subject

    # Write MIME to temp .eml file
    eml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_outgoing.eml")
    with open(eml_file, "wb") as f:
        f.write(msg.as_bytes())

    # Send via gws upload
    cmd = [
        get_gws_path(), "gmail", "users", "messages", "send",
        "--params", '{"userId": "me"}',
        "--upload", eml_file,
        "--upload-content-type", "message/rfc822",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    # Cleanup
    if os.path.exists(eml_file):
        os.remove(eml_file)

    if result.returncode == 0:
        print(f"SUCCESS: Sent to {to}")
        print(f"  Subject: {subject}")
        print(f"  Body: {len(body_text)} chars")
        if attachments:
            print(f"  Attachments: {', '.join(os.path.basename(a) for a in attachments)}")
        return True
    else:
        print(f"ERROR: rc={result.returncode}")
        print(f"  stderr: {result.stderr[:500]}")
        print(f"  stdout: {result.stdout[:500]}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python send_email_raw.py <to> <subject> <body_file> [attachments...]")
        sys.exit(1)

    to = sys.argv[1]
    subject = sys.argv[2]
    body_file = sys.argv[3]
    attachments = sys.argv[4:] if len(sys.argv) > 4 else None

    success = send_email(to, subject, body_file, attachments)
    sys.exit(0 if success else 1)
