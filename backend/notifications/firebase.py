# notifications/firebase.py
import os
import json
import tempfile
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase
if not firebase_admin._apps:
    # Try to get credentials from environment variable
    firebase_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    
    if firebase_json:
        # Create a temporary file for the credentials
        # This solves the Railway secret file issue
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(firebase_json)
            temp_file_path = f.name
        
        cred = credentials.Certificate(temp_file_path)
        firebase_admin.initialize_app(cred)
        
        # Clean up temp file after initialization
        try:
            os.unlink(temp_file_path)
        except:
            pass
    else:
        # Running locally - use file
        from pathlib import Path
        BASE_DIR = Path(__file__).resolve().parent.parent
        SERVICE_ACCOUNT_PATH = BASE_DIR / 'firebase-service-account.json'
        
        if not SERVICE_ACCOUNT_PATH.exists():
            raise FileNotFoundError(
                f"Firebase credentials not found.\n"
                f"Local: Create firebase-service-account.json at {SERVICE_ACCOUNT_PATH}\n"
                f"Railway: Add FIREBASE_SERVICE_ACCOUNT environment variable"
            )
        cred = credentials.Certificate(str(SERVICE_ACCOUNT_PATH))
        firebase_admin.initialize_app(cred)

def send_push_notification(token, title, body, data=None):
    """Send a push notification to a single device token."""
    if not token:
        return None

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon='/icons/icon-192x192.png',
                    badge='/icons/icon-72x72.png',
                    vibrate=[200, 100, 200],
                ),
                fcm_options=messaging.WebpushFCMOptions(
                    link='/'
                ),
            ),
        )
        response = messaging.send(message)
        return response
    except messaging.UnregisteredError:
        return 'unregistered'
    except Exception as e:
        print(f'FCM send error: {e}')
        return None

def send_push_to_multiple(tokens, title, body, data=None):
    """Send the same notification to multiple device tokens."""
    if not tokens:
        return

    valid_tokens = [t for t in tokens if t]
    if not valid_tokens:
        return

    batch_size = 500
    for i in range(0, len(valid_tokens), batch_size):
        batch = valid_tokens[i:i + batch_size]
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data={k: str(v) for k, v in (data or {}).items()},
                tokens=batch,
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=title,
                        body=body,
                        icon='/icons/icon-192x192.png',
                        badge='/icons/icon-72x72.png',
                        vibrate=[200, 100, 200],
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link='/'
                    ),
                ),
            )
            messaging.send_each_for_multicast(message)
        except Exception as e:
            print(f'FCM multicast error: {e}')