"""
Email File Parser

Parses .eml files to extract email metadata:
- Sender name and email
- Subject
- Body (HTML or text)
- Received timestamp
- Attachments
"""
import email
from email import policy
from email.utils import parsedate_to_datetime
from datetime import datetime
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def parse_eml_file(file_content: bytes) -> dict:
    """
    Parse an .eml file and extract email data.
    
    Args:
        file_content: Raw bytes content of the .eml file
        
    Returns:
        Dict with parsed email data:
        {
            'sender_name': str | None,
            'sender_email': str,
            'subject': str,
            'body_html': str | None,
            'body_text': str | None,
            'received_at': datetime,
            'message_id': str | None,
            'attachments': list  # List of dicts with file data
        }
    """
    try:
        # Parse the email
        msg = email.message_from_bytes(file_content, policy=policy.default)
        
        # Extract sender
        from_header = msg.get('From', '')
        sender_name, sender_email = parse_sender(from_header)
        
        # Extract subject
        subject = msg.get('Subject', '(No Subject)')
        
        # Extract date
        date_header = msg.get('Date')
        if date_header:
            try:
                received_at = parsedate_to_datetime(date_header)
                # Make timezone aware if needed
                if received_at.tzinfo is None:
                    received_at = timezone.make_aware(received_at)
            except Exception:
                received_at = timezone.now()
        else:
            received_at = timezone.now()
        
        # Extract message ID
        message_id = msg.get('Message-ID', '').strip('<>') or None
        
        # Extract body
        body_html = None
        body_text = None
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = part.get('Content-Disposition', '')
                
                # Skip attachments for body
                if 'attachment' in content_disposition:
                    # Extract attachment
                    attachment_data = extract_attachment(part)
                    if attachment_data:
                        attachments.append(attachment_data)
                    continue
                
                if content_type == 'text/html':
                    try:
                        body_html = part.get_content()
                    except Exception:
                        body_html = str(part.get_payload(decode=True) or b'', 'utf-8', errors='replace')
                elif content_type == 'text/plain' and not body_text:
                    try:
                        body_text = part.get_content()
                    except Exception:
                        body_text = str(part.get_payload(decode=True) or b'', 'utf-8', errors='replace')
        else:
            content_type = msg.get_content_type()
            if content_type == 'text/html':
                body_html = msg.get_content()
            else:
                body_text = msg.get_content()
        
        # Fallback: use text body if no HTML
        if not body_html and body_text:
            body_html = f'<pre>{body_text}</pre>'
        elif not body_html:
            body_html = '(Empty email body)'
        
        return {
            'sender_name': sender_name,
            'sender_email': sender_email,
            'subject': subject,
            'body_html': body_html,
            'body_text': body_text,
            'received_at': received_at,
            'message_id': message_id,
            'attachments': attachments,
        }
        
    except Exception as e:
        logger.error(f'Failed to parse email file: {e}')
        raise ValueError(f'Failed to parse email file: {str(e)}')


def parse_sender(from_header: str) -> tuple:
    """
    Parse the From header to extract name and email.
    
    Examples:
        'John Doe <john@example.com>' -> ('John Doe', 'john@example.com')
        'john@example.com' -> (None, 'john@example.com')
    """
    from email.utils import parseaddr
    
    name, email_addr = parseaddr(from_header)
    
    if not email_addr:
        email_addr = from_header.strip()
    
    return (name if name else None, email_addr)


def extract_attachment(part) -> 'dict | None':
    """
    Extract attachment data from an email part.
    
    Returns:
        Dict with 'filename', 'content_type', 'data', 'size'
    """
    try:
        filename = part.get_filename()
        if not filename:
            return None
        
        content_type = part.get_content_type()
        data = part.get_payload(decode=True)
        
        if not data:
            return None
        
        return {
            'filename': filename,
            'content_type': content_type,
            'data': data,
            'size': len(data),
        }
    except Exception as e:
        logger.warning(f'Failed to extract attachment: {e}')
        return None
