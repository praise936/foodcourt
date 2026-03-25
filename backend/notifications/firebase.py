# notifications/firebase.py
# Initialises Firebase Admin SDK once and exposes a send function
# Called from orders and menu views whenever something happens

import os
import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path

# Path to the service account file sitting beside manage.py
BASE_DIR = Path(__file__).resolve().parent.parent
SERVICE_ACCOUNT_PATH = BASE_DIR / 'firebase-service-account.json'

# Initialise only once — guard against double init during hot reload
if not firebase_admin._apps:
    cred = credentials.Certificate(str(SERVICE_ACCOUNT_PATH))
    firebase_admin.initialize_app(cred)


def send_push_notification(token, title, body, data=None):
    """
    Send a push notification to a single device token.
    token  — the FCM registration token saved on the user
    title  — notification headline
    body   — notification body text
    data   — optional dict of extra key/value strings
    """
    if not token:
        return None

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            # data payload — all values must be strings
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
            # Web push specific config
            webpush=messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon='/icons/icon-192x192.png',
                    badge='/icons/icon-72x72.png',
                    # Vibrate on phone
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
        # Token is no longer valid — caller should delete it
        return 'unregistered'
    except Exception as e:
        print(f'FCM send error: {e}')
        return None


def send_push_to_multiple(tokens, title, body, data=None):
    """
    Send the same notification to a list of device tokens.
    Splits into batches of 500 (FCM limit).
    """
    if not tokens:
        return

    # Remove empty tokens
    valid_tokens = [t for t in tokens if t]
    if not valid_tokens:
        return

    # FCM multicast limit is 500 per call
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