from firebase_admin import messaging

class NotificationService:
    def __init__(self):
        # Initialize if needed
        pass

    async def send_push_notification(self, fcm_token: str, title: str, body: str):
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=fcm_token,
        )
        try:
            response = messaging.send(message)
            return response
        except Exception as e:
            print(f"Error sending notification: {e}")
            return None