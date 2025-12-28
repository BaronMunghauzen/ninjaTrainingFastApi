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
        data: dict = None,
        channel_id: str = 'default_channel'
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
            data_str = f", data={data}" if data else ""
            logger.info(f"📤 Отправляю FCM уведомление: title='{title}', body='{body}', channel_id='{channel_id}'{data_str}")
            
            # Конвертируем все значения в data в строки (требование FCM)
            data_for_fcm = {}
            if data:
                for key, value in data.items():
                    data_for_fcm[str(key)] = str(value)
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data_for_fcm,
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        channel_id=channel_id,
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
            data_str = f", data={data_for_fcm}" if data_for_fcm else ""
            logger.info(f"✅ FCM уведомление отправлено: title='{title}', body='{body}', channel_id='{channel_id}'{data_str}, response={response}")
            return True
            
        except messaging.UnregisteredError as e:
            logger.warning(f"⚠️ FCM токен невалиден или устарел: {fcm_token[:20]}... (UnregisteredError: {e})")
            logger.warning(f"   Это может произойти, если: приложение было переустановлено, токен устарел, или устройство было удалено из Firebase")
            # Возвращаем специальный код для невалидного токена
            return "INVALID_TOKEN"
        except messaging.SenderIdMismatchError as e:
            logger.error(f"❌ Несоответствие Sender ID: {fcm_token[:20]}... (SenderIdMismatchError: {e})")
            logger.error(f"   Токен принадлежит другому проекту Firebase. Проверьте конфигурацию Firebase credentials.")
            return "INVALID_TOKEN"
        except messaging.InvalidArgumentError as e:
            logger.error(f"❌ Неверные аргументы FCM: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка отправки FCM: {e}")
            return False
    
    @classmethod
    def send_notification_with_cleanup(
        cls,
        fcm_token: str,
        title: str,
        body: str,
        data: dict = None,
        user_uuid: str = None,
        session = None
    ) -> bool:
        """
        Отправка уведомления с автоматической очисткой невалидных токенов
        
        Args:
            fcm_token: FCM токен устройства
            title: Заголовок уведомления
            body: Текст уведомления
            data: Дополнительные данные (опционально)
            user_uuid: UUID пользователя (для очистки токена)
            session: SQLAlchemy сессия (для очистки токена)
        
        Returns:
            bool: True если отправлено успешно
        """
        result = cls.send_notification(fcm_token, title, body, data)
        
        # Если токен невалиден и есть данные для очистки
        if result == "INVALID_TOKEN" and user_uuid and session:
            try:
                from app.users.models import User
                from sqlalchemy import select
                
                # Получаем пользователя
                result_query = session.execute(
                    select(User).filter(User.uuid == user_uuid)
                )
                user = result_query.scalar_one_or_none()
                
                if user and user.fcm_token == fcm_token:
                    # Очищаем токен
                    user.fcm_token = None
                    session.commit()
                    logger.info(f"🧹 Очищен невалидный FCM токен для пользователя {user_uuid}")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка очистки токена: {e}")
        
        return result == True
