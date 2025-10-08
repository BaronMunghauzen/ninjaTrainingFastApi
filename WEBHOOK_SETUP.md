# 🔔 Настройка вебхуков Точка Банк

## Что такое вебхуки?

Вебхуки от Точки — это **автоматические уведомления** о статусе платежей. Когда пользователь оплачивает подписку, Точка отправляет POST запрос на ваш сервер с информацией о платеже.

**Документация:** https://developers.tochka.com/docs/tochka-api/opisanie-metodov/vebhuki

---

## ⚠️ Важно!

1. **Вебхук = JWT токен** - Точка отправляет JWT в теле запроса, который нужно расшифровать
2. **Проверка подписи** - JWT подписан приватным ключом Точки, проверяется публичным ключом
3. **Настройка через API** - Вебхуки настраиваются отдельно через метод Create Webhook
4. **Публичный URL** - Ваш сервер должен быть доступен из интернета

---

## 🚀 Быстрый старт

### Шаг 1: Убедитесь что сервер доступен извне

**Для локальной разработки используйте ngrok:**

```bash
# Установите ngrok: https://ngrok.com/
ngrok http 8000
```

Скопируйте URL (например: `https://abc123.ngrok.io`) и обновите в `.env`:

```env
BASE_URL=https://abc123.ngrok.io
```

**Для продакшена:**
```env
BASE_URL=https://yourdomain.com
```

### Шаг 2: Перезапустите сервер

```bash
uvicorn app.main:app --reload
```

### Шаг 3: Настройте вебхук

```bash
python setup_tochka_webhook.py
```

Этот скрипт:
1. Проверит существующие вебхуки
2. Создаст новый вебхук для события `acquiringInternetPayment`

**URL вебхука:** `{BASE_URL}/api/subscriptions/webhook`

---

## 📋 Требования

### JWT-токен должен иметь разрешение:
- `ManageWebhookData` - для создания/управления вебхуками

Если у вас нет этого разрешения:
1. Зайдите в личный кабинет Точки
2. Перейдите в раздел API
3. Обновите разрешения для JWT-токена

---

## 🔐 Как работает безопасность

### 1. Точка отправляет JWT токен
```
POST {BASE_URL}/api/subscriptions/webhook
Body: eyJhbGciOiJSUzI1NiIs...  (JWT токен как строка)
```

### 2. Сервер расшифровывает JWT
```python
from app.payments.webhook_validator import decode_webhook_jwt

# Расшифровываем с проверкой подписи (алгоритм RS256)
webhook_data = decode_webhook_jwt(jwt_token)
```

### 3. Проверяем подпись
JWT подписан приватным ключом Точки, проверяется их публичным ключом:
```python
TOCHKA_PUBLIC_KEY = {
    "kty": "RSA",
    "e": "AQAB",
    "n": "rwm77av7GIttq-JF1itEgLCGEZW_zz16RlUQ..."  # Полный ключ в коде
}
```

### 4. Если подпись валидна - обрабатываем данные

---

## 📊 Структура данных вебхука

После расшифровки JWT, данные имеют структуру:

```json
{
  "webhookType": "acquiringInternetPayment",
  "operationId": "0c9639fc-5762-41c3-aa48-f5bf60bee75b",
  "status": "PAID",
  "amount": 2490.0,
  "customerCode": "305015065",
  "purpose": "Подписка NinjaTraining: 3 месяца",
  "consumerId": "01f2ca69-19ff-47b7-8641-f7096a69d883",
  "receiptUrl": "https://...",
  ...
}
```

---

## 🧪 Тестирование вебхука

### Ручной тест (Send Webhook)

Точка предоставляет метод `Send Webhook` для отправки тестового вебхука:

```bash
curl -X POST "https://enter.tochka.com/webhooks/v1.0/webhook/{webhookId}/send" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Проверка в логах

После настройки вебхука сделайте тестовый платёж и проверьте логи сервера:

```
=== Получен вебхук от Точки ===
JWT Token (первые 100 символов): eyJhbGciOiJSUzI1NiIs...
✓ JWT вебхука успешно расшифрован и подпись проверена
Расшифрованные данные вебхука: {...}
Вебхук acquiringInternetPayment: operationId=..., status=PAID
✓ Платеж оплачен, активируем подписку
=== Вебхук успешно обработан ===
```

---

## ❓ Частые проблемы

### Вебхук не доходит до сервера
- ✅ Проверьте что BASE_URL доступен извне
- ✅ Используйте ngrok для локальной разработки
- ✅ Проверьте что вебхук создан (запустите `setup_tochka_webhook.py`)

### Ошибка "Invalid JWT signature"
- ✅ Проверьте что используется правильный публичный ключ Точки
- ✅ Вебхук должен быть настроен в Точке (не передавать webhookUrl при создании платежа)

### Вебхук не создаётся
- ✅ Проверьте разрешение `ManageWebhookData` в JWT-токене
- ✅ Возможно вебхук с таким URL уже существует

---

## 📝 Управление вебхуками

### Получить список вебхуков
```bash
python setup_tochka_webhook.py  # Покажет существующие вебхуки
```

### Удалить вебхук
```bash
curl -X DELETE "https://enter.tochka.com/webhooks/v1.0/webhook/{webhookId}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Изменить вебхук
```bash
curl -X PUT "https://enter.tochka.com/webhooks/v1.0/webhook/{webhookId}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"Data": {"url": "NEW_URL", "status": "enabled"}}'
```

---

## ✅ Чеклист настройки

- [ ] BASE_URL указывает на публичный адрес (или ngrok)
- [ ] Сервер запущен и доступен извне
- [ ] JWT-токен имеет разрешение ManageWebhookData
- [ ] Запущен скрипт `python setup_tochka_webhook.py`
- [ ] Вебхук создан успешно (проверьте вывод скрипта)
- [ ] Протестирован тестовый платёж
- [ ] В логах видно расшифровку JWT и обработку вебхука

---

## 🎯 Готово!

После настройки вебхука система будет автоматически:
1. Получать уведомления о платежах
2. Активировать подписки при успешной оплате
3. Обновлять статусы при отмене/истечении

Удачи! 🚀
