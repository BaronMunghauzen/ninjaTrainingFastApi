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
        except ValueError as e:
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
    
    @classmethod
    def send_workout_notification(
        cls,
        fcm_token: str,
        user_training_uuid: str,
        training_uuid: str,
        training_type: str,
        background_image_url: str = None
    ) -> bool:
        """
        Отправка постоянного уведомления о тренировке в темном минималистичном стиле
        Без звука, вибрации и стандартного уведомления
        
        Args:
            fcm_token: FCM токен устройства
            user_training_uuid: UUID пользовательской тренировки
            training_uuid: UUID тренировки
            training_type: Тип тренировки ('userFree' или 'system_training')
            background_image_url: URL PNG изображения для фона уведомления (опционально)
        
        Returns:
            bool: True если отправлено успешно
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            # Определяем текст уведомления в зависимости от типа
            if training_type == "userFree":
                title = "Свободная тренировка"
                body = "Нажмите, чтобы продолжить"
            else:
                title = "Тренировка"
                body = "Нажмите, чтобы продолжить"
            
            # Уникальный tag для идентификации уведомления (для возможности удаления)
            notification_tag = f"workout_{user_training_uuid}"
            
            # Данные для уведомления
            data_for_fcm = {
                'type': 'workout_active',
                'user_training_uuid': str(user_training_uuid),
                'training_uuid': str(training_uuid),
                'training_type': str(training_type),
                'notification_tag': notification_tag
            }
            
            # Добавляем URL изображения в data, если передан
            if background_image_url:
                data_for_fcm['background_image_url'] = str(background_image_url)
            
            logger.info(f"📤 Отправляю постоянное уведомление о тренировке: title='{title}', tag='{notification_tag}', training_type='{training_type}', image={bool(background_image_url)}")
            
            # Конвертируем все значения в строки (требование FCM)
            data_for_fcm_str = {str(k): str(v) for k, v in data_for_fcm.items()}
            
            # Настройки Android уведомления
            # Без звука и вибрации - не указываем параметры sound и default_vibrate_timings
            # Постоянность уведомления (ongoing/sticky) настраивается на клиенте через канал
            android_notification_params = {
                'channel_id': 'workout_channel',
                'priority': 'max',
                'tag': notification_tag,  # Tag для идентификации и удаления
                'color': '#1A1A1A',  # Темный цвет для минималистичного дизайна
                'visibility': 'public',
                # Звук и вибрация отключены - не указываем параметры sound и default_vibrate_timings
                # Канал workout_channel должен быть настроен на клиенте с отключенными звуком, вибрацией и как ongoing
            }
            
            # Добавляем изображение, если передан URL
            if background_image_url:
                android_notification_params['image'] = background_image_url
            
            # Настройки iOS уведомления
            # Без звука - не указываем параметр sound
            apns_aps = messaging.Aps(
                # Звук отключен - не указываем параметр sound
                badge=1,
                category='WORKOUT_ACTIVE',  # Категория для persistent notification
                content_available=True,
            )
            
            # Дополнительные данные для iOS
            ios_custom_data = {
                'notification_tag': notification_tag,
                'type': 'workout_active'
            }
            
            # Добавляем URL изображения для iOS, если передан
            if background_image_url:
                ios_custom_data['background_image_url'] = str(background_image_url)
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data_for_fcm_str,
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(**android_notification_params),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=apns_aps,
                        custom_data=ios_custom_data
                    ),
                ),
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Постоянное уведомление о тренировке отправлено: tag='{notification_tag}', response={response}")
            return True
            
        except messaging.UnregisteredError as e:
            logger.warning(f"⚠️ FCM токен невалиден или устарел: {fcm_token[:20]}... (UnregisteredError: {e})")
            return "INVALID_TOKEN"
        except messaging.SenderIdMismatchError as e:
            logger.error(f"❌ Несоответствие Sender ID: {fcm_token[:20]}... (SenderIdMismatchError: {e})")
            return "INVALID_TOKEN"
        except ValueError as e:
            logger.error(f"❌ Неверные аргументы FCM: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о тренировке: {e}")
            return False
    
    @classmethod
    def cancel_workout_notification(
        cls,
        fcm_token: str,
        user_training_uuid: str
    ) -> bool:
        """
        Удаление постоянного уведомления о тренировке
        
        Args:
            fcm_token: FCM токен устройства
            user_training_uuid: UUID пользовательской тренировки
        
        Returns:
            bool: True если удалено успешно
        """
        if not cls._initialized:
            cls.initialize()
        
        try:
            notification_tag = f"workout_{user_training_uuid}"
            
            logger.info(f"🗑️ Удаляю уведомление о тренировке: tag='{notification_tag}'")
            
            # Для удаления уведомления отправляем специальное сообщение с data-only
            # и пустым notification, что сигнализирует клиенту об удалении
            data_for_fcm = {
                'type': 'workout_cancelled',
                'user_training_uuid': str(user_training_uuid),
                'notification_tag': notification_tag,
                'action': 'cancel'
            }
            
            # Конвертируем все значения в строки
            data_for_fcm_str = {str(k): str(v) for k, v in data_for_fcm.items()}
            
            message = messaging.Message(
                # Без notification - только data, чтобы клиент мог обработать удаление
                data=data_for_fcm_str,
                token=fcm_token,
                android=messaging.AndroidConfig(
                    priority='high',
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            content_available=True,
                            category='WORKOUT_CANCELLED',
                        ),
                        custom_data={
                            'notification_tag': notification_tag,
                            'type': 'workout_cancelled',
                            'action': 'cancel'
                        }
                    ),
                ),
            )
            
            response = messaging.send(message)
            logger.info(f"✅ Команда удаления уведомления отправлена: tag='{notification_tag}', response={response}")
            return True
            
        except messaging.UnregisteredError as e:
            logger.warning(f"⚠️ FCM токен невалиден или устарел: {fcm_token[:20]}... (UnregisteredError: {e})")
            return "INVALID_TOKEN"
        except messaging.SenderIdMismatchError as e:
            logger.error(f"❌ Несоответствие Sender ID: {fcm_token[:20]}... (SenderIdMismatchError: {e})")
            return "INVALID_TOKEN"
        except ValueError as e:
            logger.error(f"❌ Неверные аргументы FCM: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка удаления уведомления о тренировке: {e}")
            return False