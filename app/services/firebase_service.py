import firebase_admin
from firebase_admin import credentials, messaging
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

class FirebaseService:
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Инициализация Firebase Admin SDK"""
        if cls._initialized:
            return
            
        try:
            # Путь к файлу с credentials (скачанный из Firebase Console)
            # Сначала проверяем переменную окружения
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
            
            if not cred_path:
                # Если переменная не установлена, используем путь по умолчанию
                cred_path = Path(__file__).parent.parent.parent / 'firebase-credentials.json'
            else:
                cred_path = Path(cred_path)
            
            if not cred_path.exists():
                logger.error(f"Firebase credentials не найден: {cred_path}")
                raise FileNotFoundError(f"Поместите firebase-credentials.json в {cred_path}")
            
            cred = credentials.Certificate(str(cred_path))
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            logger.info("✅ Firebase Admin SDK инициализирован успешно")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Firebase: {e}")
            raise
    
    @classmethod
    def send_notification(
        cls,
        fcm_token: str,
        title: str,
        body: str,
        data: dict = None
    ) -> bool:
        """
        Отправка push-уведомления через FCM
        
        Args:
            fcm_token: FCM токен устройства
            title: Заголовок уведомления
            body: Текст уведомления
            data: Дополнительные данные (опционально)
        
        Returns:
            bool: True если отправлено успешно
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id='timer_channel',
                        priority='max',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        ),
                    ),
                ),
            )
            
            response = messaging.send(message)
            logger.info(f"✅ FCM уведомление отправлено: {response}")
            return True
            
        except messaging.UnregisteredError:
            logger.warning(f"⚠️ FCM токен невалиден или устарел: {fcm_token[:20]}...")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка отправки FCM: {e}")
            return False
