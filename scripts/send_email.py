"""
Send job kit emails to Callie with proper body and attachments.
Reads email-rules.md format. Uses gws CLI with body from file to avoid shell truncation.

Usage:
  python send_email.py <to> <subject> <body_file> [attachment1] [attachment2] ...
"""
import subprocess
import sys
import os


def get_gws_path():
    gws_path = os.path.join(os.environ.get("APPDATA", ""), "npm", "gws.cmd")
    if os.path.exists(gws_path):
        return gws_path
    return "gws"


def send_email(to, subject, body_file, attachments=None):
    with open(body_file, "r", encoding="utf-8") as f:
        body = f.read()

    cmd = [
        get_gws_path(), "gmail", "+send",
        "--to", to,
        "--subject", subject,
        "--body", body,
    ]
    if attachments:
        for a in attachments:
            cmd.extend(["-a", a])

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        print(f"SUCCESS: Sent to {to}")
        print(f"  Subject: {subject}")
        print(f"  Body length: {len(body)} chars")
        if attachments:
            print(f"  Attachments: {', '.join(attachments)}")
    else:
        print(f"ERROR: {result.stderr[:500]}")
    return result.returncode == 0


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python send_email.py <to> <subject> <body_file> [attachments...]")
        sys.exit(1)

    to = sys.argv[1]
    subject = sys.argv[2]
    body_file = sys.argv[3]
    attachments = sys.argv[4:] if len(sys.argv) > 4 else None

    success = send_email(to, subject, body_file, attachments)
    sys.exit(0 if success else 1)
