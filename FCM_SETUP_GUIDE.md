# Firebase Cloud Messaging (FCM) Setup Guide

## Обзор

Данный функционал добавляет поддержку Firebase Cloud Messaging для отправки push-уведомлений о завершении таймера отдыха между подходами в упражнениях.

## Что было добавлено

### 1. Зависимости
- `firebase-admin==6.5.0` - для работы с Firebase Admin SDK
- `APScheduler` - уже был установлен, используется для планирования уведомлений

### 2. База данных
- Добавлено поле `fcm_token` в таблицу `user` для хранения FCM токенов устройств
- Создана миграция `bb26141c2444_add_fcm_token_to_users.py`

### 3. Сервисы
- **FirebaseService** (`app/services/firebase_service.py`) - отправка push-уведомлений
- **SchedulerService** (`app/services/scheduler_service.py`) - планирование отложенных уведомлений

### 4. API Endpoints
- `POST /notifications/update-fcm-token` - обновление FCM токена пользователя
- `POST /notifications/schedule-timer` - планирование уведомления о завершении таймера
- `POST /notifications/cancel-timer` - отмена запланированного уведомления
- `POST /notifications/test-notification` - тестовая отправка уведомления
- `GET /notifications/scheduled-jobs` - просмотр запланированных задач

## Настройка Firebase

### 1. Создание проекта в Firebase Console

1. Перейдите в [Firebase Console](https://console.firebase.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Cloud Messaging в проекте

### 2. Получение Service Account ключа

1. Перейдите в **Project Settings** → **Service accounts**
2. Нажмите **Generate new private key**
3. Скачайте JSON файл с credentials
4. Переименуйте файл в `firebase-credentials.json`
5. Поместите файл в корень проекта (рядом с `main.py`)

### 3. Настройка переменных окружения (опционально)

Можно указать путь к credentials файлу через переменную окружения:

```bash
export FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
```

## Применение миграции

```bash
# Активируйте виртуальное окружение
.venv\Scripts\activate

# Примените миграцию
alembic upgrade head
```

## Тестирование

### 1. Тестовая отправка уведомления

```bash
curl -X POST "http://localhost:8000/notifications/test-notification?user_uuid=YOUR_USER_UUID"
```

### 2. Планирование таймера

```bash
curl -X POST "http://localhost:8000/notifications/schedule-timer" \
  -H "Content-Type: application/json" \
  -d '{
    "user_uuid": "YOUR_USER_UUID",
    "exercise_uuid": "EXERCISE_UUID",
    "exercise_name": "Отжимания",
    "duration_seconds": 60
  }'
```

## Использование в Flutter приложении

### 1. Обновление FCM токена

```dart
// Получение FCM токена
String? fcmToken = await FirebaseMessaging.instance.getToken();

// Отправка на сервер
await http.post(
  Uri.parse('$baseUrl/notifications/update-fcm-token'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'user_uuid': userUuid,
    'fcm_token': fcmToken,
  }),
);
```

### 2. Планирование уведомления о таймере

```dart
// При запуске таймера отдыха
await http.post(
  Uri.parse('$baseUrl/notifications/schedule-timer'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'user_uuid': userUuid,
    'exercise_uuid': exerciseUuid,
    'exercise_name': exerciseName,
    'duration_seconds': restDurationSeconds,
  }),
);
```

### 3. Отмена уведомления

```dart
// При отмене таймера
await http.post(
  Uri.parse('$baseUrl/notifications/cancel-timer'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'user_uuid': userUuid,
  }),
);
```

## Важные замечания

### Безопасность
- **НЕ КОММИТЬТЕ** `firebase-credentials.json` в Git
- Файл добавлен в `.gitignore`
- Используйте переменные окружения для production

### Производительность
- При перезапуске сервера APScheduler теряет запланированные задачи
- Для production рекомендуется использовать Redis или PostgreSQL как job store

### Таймзоны
- Backend использует UTC время
- Конвертация в локальное время происходит на клиенте

### Обновление токенов
- FCM токены могут изменяться
- Flutter приложение должно обновлять токены при изменении

## Логирование

Все операции логируются с соответствующими уровнями:
- `INFO` - успешные операции
- `WARNING` - невалидные токены
- `ERROR` - ошибки отправки/планирования

## Мониторинг

Используйте endpoint `/notifications/scheduled-jobs` для просмотра всех запланированных уведомлений.

## Troubleshooting

### Ошибка инициализации Firebase
- Проверьте наличие файла `firebase-credentials.json`
- Убедитесь в правильности JSON формата
- Проверьте права доступа к файлу

### Уведомления не приходят
- Проверьте FCM токен пользователя в базе данных
- Убедитесь что Firebase проект настроен правильно
- Проверьте логи сервера на наличие ошибок

### Таймеры не работают после перезапуска
- Это нормальное поведение для in-memory scheduler
- Используйте persistent job store для production
