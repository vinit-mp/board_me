import re
import imaplib
import email
from email.header import decode_header
from datetime import datetime

def connect_to_email(email_address, password, imap_server="imap.gmail.com"):
    """Connect to email account via IMAP."""
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, password)
        return mail
    except Exception as e:
        print(f"Error connecting to email: {str(e)}")
        return None

def search_for_flight_bookings(mail, folder="INBOX", days=30):
    """Search emails for flight booking information."""
    mail.select(folder)
    
    # Search for recent emails
    date = (datetime.now() - datetime.timedelta(days=days)).strftime("%d-%b-%Y")
    status, messages = mail.search(None, f'(SINCE {date})')
    
    email_ids = messages[0].split()
    
    flight_bookings = []
    
    # Common patterns found in flight booking emails
    flight_patterns = [
        r'flight confirmation',
        r'booking confirmation',
        r'flight itinerary',
        r'e-ticket',
        r'boarding pass',
        r'flight \w+\d+',  # Flight followed by letters and numbers (e.g., "Flight AA123")
        r'confirmation number',
        r'reservation number',
        r'booking reference',
        r'\b[A-Z]{2}\d{3,4}\b',  # Common flight number pattern (e.g., AA123)
        r'\b[A-Z]{6}\b'  # Common booking reference format (e.g., ABCDEF)
    ]
    
    airline_names = [
        'delta', 'american airlines', 'united', 'southwest', 'jetblue', 
        'alaska airlines', 'frontier', 'spirit', 'british airways', 'lufthansa', 
        'air france', 'emirates', 'qatar airways', 'cathay pacific', 'singapore airlines',
        'air canada', 'klm', 'turkish airlines', 'airasia', 'ryanair', 'easyjet', 
        'virgin atlantic', 'hawaiian airlines', 'eva air', 'etihad'
    ]
    
    for email_id in email_ids:
        # Fetch email content
        status, msg_data = mail.fetch(email_id, '(RFC822)')
        
        for response in msg_data:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])
                
                # Get email subject and decode it
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get sender
                sender = msg.get("From", "")
                
                # Initialize email body
                body = ""
                
                # Get email body
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        # Skip attachments
                        if "attachment" in content_disposition:
                            continue
                        
                        # Get text content
                        if content_type == "text/plain" or content_type == "text/html":
                            try:
                                body_part = part.get_payload(decode=True).decode()
                                body += body_part
                            except:
                                pass
                else:
                    # Not multipart - get payload directly
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except:
                        body = ""
                
                # Check for flight booking patterns in subject and body
                flight_indicators = []
                
                # Check for flight patterns
                for pattern in flight_patterns:
                    if re.search(pattern, subject.lower()) or re.search(pattern, body.lower()):
                        flight_indicators.append(pattern)
                
                # Check for airline names
                for airline in airline_names:
                    if airline in subject.lower() or airline in body.lower():
                        flight_indicators.append(airline)
                
                # If we found at least 2 indicators, consider it a flight booking
                if len(flight_indicators) >= 2:
                    # Extract date information using regex
                    date_patterns = [
                        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
                        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
                        r'\d{2}/\d{2}/\d{4}',
                        r'\d{2}-\d{2}-\d{4}'
                    ]
                    
                    dates = []
                    for date_pattern in date_patterns:
                        dates.extend(re.findall(date_pattern, body))
                    
                    # Try to extract flight numbers
                    flight_numbers = re.findall(r'\b[A-Z]{2}\s*\d{3,4}\b', body)
                    
                    booking_info = {
                        'subject': subject,
                        'sender': sender,
                        'date_received': msg['Date'],
                        'flight_indicators': flight_indicators,
                        'potential_travel_dates': dates[:5] if dates else [],
                        'potential_flight_numbers': flight_numbers[:5] if flight_numbers else []
                    }
                    
                    flight_bookings.append(booking_info)
    
    return flight_bookings

def display_flight_bookings(bookings):
    """Display detected flight bookings in a readable format."""
    if not bookings:
        print("No flight bookings detected in your email.")
        return
    
    print(f"Found {len(bookings)} potential flight booking emails:")
    print("-" * 50)
    
    for i, booking in enumerate(bookings, 1):
        print(f"Booking #{i}:")
        print(f"  Subject: {booking['subject']}")
        print(f"  From: {booking['sender']}")
        print(f"  Received: {booking['date_received']}")
        
        if booking['potential_travel_dates']:
            print("  Potential travel dates:")
            for date in booking['potential_travel_dates']:
                print(f"    - {date}")
        
        if booking['potential_flight_numbers']:
            print("  Potential flight numbers:")
            for flight_num in booking['potential_flight_numbers']:
                print(f"    - {flight_num}")
        
        print(f"  Detected based on: {', '.join(booking['flight_indicators'])}")
        print("-" * 50)

def main():
    # Replace with your email credentials
    email_address = "your_email@gmail.com"
    password = "your_password_or_app_password"  # Use app password for Gmail
    
    # Connect to email
    mail = connect_to_email(email_address, password)
    if not mail:
        return
    
    # Search for flight bookings in the last 60 days
    flight_bookings = search_for_flight_bookings(mail, days=60)
    
    # Display results
    display_flight_bookings(flight_bookings)
    
    # Logout
    mail.logout()

if __name__ == "__main__":
    main()