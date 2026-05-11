import smtplib
import imaplib
import poplib
import email
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_USER = os.environ.get('EMAIL_USER', '')
EMAIL_PASS = os.environ.get('EMAIL_PASS', '')

SMTP_HOST  = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT  = int(os.environ.get('SMTP_PORT', 587))

IMAP_HOST  = os.environ.get('IMAP_HOST', 'imap.gmail.com')
IMAP_PORT  = int(os.environ.get('IMAP_PORT', 993))

POP3_HOST  = os.environ.get('POP3_HOST', 'pop.gmail.com')
POP3_PORT  = int(os.environ.get('POP3_PORT', 995))


def send_smtp(to_email: str, subject: str, body: str) -> dict:
    if not EMAIL_USER or not EMAIL_PASS:
        return {'success': False, 'error': 'EMAIL_USER / EMAIL_PASS not configured'}
    try:
        msg = MIMEMultipart('alternative')
        msg['From']    = EMAIL_USER
        msg['To']      = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())

        return {'success': True, 'message': f'Email sent to {to_email} via SMTP'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def check_imap(limit: int = 5) -> dict:
    if not EMAIL_USER or not EMAIL_PASS:
        return {'success': False, 'error': 'EMAIL_USER / EMAIL_PASS not configured'}
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select('INBOX')
        _, data = mail.search(None, 'ALL')
        ids = data[0].split()
        last_ids = ids[-limit:] if len(ids) >= limit else ids

        messages = []
        for mid in reversed(last_ids):
            _, msg_data = mail.fetch(mid, '(RFC822)')
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            messages.append({
                'from':    msg.get('From'),
                'subject': msg.get('Subject'),
                'date':    msg.get('Date'),
            })
        mail.logout()
        return {'success': True, 'protocol': 'IMAP4 SSL', 'count': len(messages), 'messages': messages}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def check_pop3(limit: int = 5) -> dict:
    if not EMAIL_USER or not EMAIL_PASS:
        return {'success': False, 'error': 'EMAIL_USER / EMAIL_PASS not configured'}
    try:
        mailbox = poplib.POP3_SSL(POP3_HOST, POP3_PORT)
        mailbox.user(EMAIL_USER)
        mailbox.pass_(EMAIL_PASS)

        num_messages = len(mailbox.list()[1])
        start = max(1, num_messages - limit + 1)

        messages = []
        for i in range(num_messages, start - 1, -1):
            raw_lines = mailbox.retr(i)[1]
            raw = b'\r\n'.join(raw_lines)
            msg = email.message_from_bytes(raw)
            messages.append({
                'from':    msg.get('From'),
                'subject': msg.get('Subject'),
                'date':    msg.get('Date'),
            })
        mailbox.quit()
        return {'success': True, 'protocol': 'POP3 SSL', 'count': len(messages), 'messages': messages}
    except Exception as e:
        return {'success': False, 'error': str(e)}
