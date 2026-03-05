import os
import firebase_admin
from firebase_admin import credentials, messaging

# Attempt to initialize if credentials present
if not firebase_admin._apps:
    try:
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_JSON")
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Warning: Failed to init Firebase: {e}")

def send_fcm_notification(device_tokens: list, title: str, body: str, data: dict = None):
    """
    Sends a push notification to specific device tokens using Firebase Admin SDK.
    Gracefully falls back to mock behavior if firebase isn't configured for local testing.
    """
    if not firebase_admin._apps:
        print(f"[MOCK FCM] Sending '{title} - {body}' to {len(device_tokens)} devices.")
        return

    if not device_tokens:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        tokens=device_tokens,
    )
    try:
        response = messaging.send_each_for_multicast(message)
        print(f"Successfully sent FCM message: {response.success_count} success, {response.failure_count} failures")
    except Exception as e:
        print(f"Failed to send FCM message: {e}")
