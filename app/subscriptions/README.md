# 💳 Система подписок и платежей

Модуль для управления подписками пользователей с интеграцией платежной системы Точка Банк.

## 📋 Оглавление

- [Что реализовано](#что-реализовано)
- [Настройка](#настройка)
- [Применение миграций](#применение-миграций)
- [Создание тарифных планов](#создание-тарифных-планов)
- [API Endpoints](#api-endpoints)
- [Интеграция на фронтенде](#интеграция-на-фронтенде)
- [Настройка вебхуков](#настройка-вебхуков)

---

## ✅ Что реализовано

### Backend:
- ✅ Модели данных (SubscriptionPlan, Payment, Subscription)
- ✅ Интеграция с Точка API через платёжные ссылки
- ✅ Триальный период 2 недели при регистрации
- ✅ Тарифные планы: 1, 3, 6, 12 месяцев
- ✅ Обработка платежей и вебхуков
- ✅ История платежей
- ✅ Автоматическая фискализация чеков (54-ФЗ)

### Функционал:
- 🎁 Триальный период 14 дней
- 💰 Покупка подписки на разные периоды
- 📊 Проверка статуса подписки
- 📝 История платежей
- 🔔 Вебхуки от Точки для обновления статусов

---

## ⚙️ Настройка

### 1. Настройка переменных окружения

Добавьте в файл `.env` следующие переменные:

```env
# Настройки Точка Банк
TOCHKA_ACCESS_TOKEN=ваш_jwt_токен_здесь
TOCHKA_API_URL=https://api.tochka.com/v1
TOCHKA_VAT_CODE=vat20

# URL вашего сервера (для вебхуков)
BASE_URL=https://yourdomain.com
```

**Где взять JWT-токен:**
1. Зарегистрируйтесь в Точка Банке: https://enter.tochka.com/
2. Подключите интернет-эквайринг через интернет-банк
3. Перейдите в раздел API и создайте JWT-токен
4. Скопируйте токен в переменную `TOCHKA_ACCESS_TOKEN`

**Ставки НДС (TOCHKA_VAT_CODE):**
- `vat0` - НДС 0%
- `vat10` - НДС 10%
- `vat20` - НДС 20%
- `vat110` - НДС 10/110
- `vat120` - НДС 20/120
- `none` - без НДС

---

## 🗄️ Применение миграций

После настройки переменных окружения примените миграции:

```bash
# Активируйте виртуальное окружение
.\.venv\Scripts\Activate.ps1

# Примените миграцию
alembic upgrade head
```

Это создаст следующие таблицы:
- `subscription_plans` - тарифные планы
- `payments` - история платежей
- `subscriptions` - подписки пользователей
- Добавит поля `trial_used` и `trial_started_at` в таблицу `user`

---

## 💰 Создание тарифных планов

После применения миграций создайте тарифные планы:

```bash
python create_subscription_plans.py
```

Это создаст 4 плана по умолчанию:
- **1 месяц** - 990₽ (990₽/мес)
- **3 месяца** - 2490₽ (830₽/мес, выгода 16%)
- **6 месяцев** - 4490₽ (748₽/мес, выгода 24%)
- **12 месяцев** - 7990₽ (666₽/мес, выгода 33%)

Вы можете изменить цены в файле `create_subscription_plans.py` перед запуском.

---

## 🚀 API Endpoints

### Получить список тарифов
```http
GET /api/subscriptions/plans
```

**Ответ:**
```json
{
  "plans": [
    {
      "uuid": "...",
      "plan_type": "month_1",
      "name": "1 месяц",
      "duration_months": 1,
      "price": 990.00,
      "price_per_month": 990.00,
      "description": "Подписка на 1 месяц",
      "is_active": true
    }
  ]
}
```

---

### Активировать триал
```http
POST /api/subscriptions/activate-trial
Authorization: Bearer {access_token}
```

**Ответ:**
```json
{
  "message": "Триальный период успешно активирован!",
  "subscription_uuid": "...",
  "expires_at": "2025-10-21T19:00:00",
  "is_trial": true
}
```

---

### Купить подписку
```http
POST /api/subscriptions/purchase
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "plan_id": 1,
  "return_url": "myapp://payment/callback"  // опционально
}
```

**Ответ:**
```json
{
  "payment_uuid": "...",
  "payment_url": "https://payment.tochka.com/...",
  "payment_link_id": "..."
}
```

**Использование:**
1. Получите `payment_url` и откройте его в браузере/WebView
2. Пользователь оплачивает через Точку (карта или СБП)
3. После оплаты происходит редирект на `return_url`
4. На сервер приходит вебхук с результатом оплаты

---

### Проверить статус подписки
```http
GET /api/subscriptions/status
Authorization: Bearer {access_token}
```

**Ответ:**
```json
{
  "subscription_status": "active",
  "subscription_until": "2025-11-07",
  "is_trial": false,
  "trial_used": true,
  "days_remaining": 30
}
```

---

### Проверить статус платежа
```http
GET /api/subscriptions/payment/{payment_uuid}/status
Authorization: Bearer {access_token}
```

**Ответ:**
```json
{
  "status": "succeeded",
  "amount": 990.00,
  "created_at": "2025-10-07T19:00:00",
  "paid_at": "2025-10-07T19:05:00",
  "receipt_url": "https://..."
}
```

---

### История платежей
```http
GET /api/subscriptions/history
Authorization: Bearer {access_token}
```

**Ответ:**
```json
{
  "payments": [
    {
      "uuid": "...",
      "amount": 990.00,
      "status": "succeeded",
      "plan_name": "1 месяц",
      "created_at": "2025-10-07T19:00:00",
      "paid_at": "2025-10-07T19:05:00",
      "receipt_url": "https://..."
    }
  ]
}
```

---

### Вебхук от Точки
```http
POST /api/subscriptions/webhook
Content-Type: application/json

{
  "eventType": "acquiringInternetPayment",
  "Data": {
    "paymentLinkId": "...",
    "status": "paid",
    "metadata": {
      "payment_uuid": "...",
      "type": "subscription"
    }
  }
}
```

**Важно:** Этот endpoint вызывается автоматически Точкой при изменении статуса платежа.

---

## 📱 Интеграция на фронтенде

### Пример на TypeScript/React Native:

```typescript
// 1. Получение списка тарифов
const getSubscriptionPlans = async () => {
  const response = await api.get('/api/subscriptions/plans');
  return response.data;
};

// 2. Покупка подписки
const purchaseSubscription = async (planId: number) => {
  try {
    const response = await api.post('/api/subscriptions/purchase', {
      plan_id: planId
      // return_url опционален, по умолчанию используется deep link
    });
    
    const { payment_url, payment_uuid } = response.data;
    
    // Сохраняем payment_uuid для проверки после возврата
    await AsyncStorage.setItem('current_payment_uuid', payment_uuid);
    
    // Открываем браузер для оплаты
    await Linking.openURL(payment_url);
    
  } catch (error) {
    console.error('Ошибка создания платежа:', error);
  }
};

// 3. Обработка Deep Link при возврате из оплаты
const handleDeepLink = async (url: string) => {
  // url = "myapp://payment/callback?payment_uuid=xxx"
  
  const payment_uuid = await AsyncStorage.getItem('current_payment_uuid');
  
  if (!payment_uuid) return;
  
  // Проверяем статус платежа
  await checkPaymentStatus(payment_uuid);
};

// 4. Проверка статуса платежа
const checkPaymentStatus = async (payment_uuid: string) => {
  const maxAttempts = 10;
  let attempts = 0;
  
  const check = async () => {
    try {
      const response = await api.get(
        `/api/subscriptions/payment/${payment_uuid}/status`
      );
      
      if (response.data.status === 'succeeded') {
        // Оплата прошла успешно
        showSuccess('Подписка успешно оплачена!');
        await refreshUserData();
      } else if (['pending', 'processing'].includes(response.data.status)) {
        // Продолжаем проверять
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(check, 2000); // Проверяем каждые 2 сек
        } else {
          showInfo('Ожидание оплаты...');
        }
      } else {
        // failed, cancelled
        showError('Оплата не прошла');
      }
    } catch (error) {
      showError('Ошибка проверки оплаты');
    }
  };
  
  check();
};

// 5. Проверка статуса подписки
const getSubscriptionStatus = async () => {
  const response = await api.get('/api/subscriptions/status');
  return response.data;
};
```

### Deep Link настройка

**Android (AndroidManifest.xml):**
```xml
<intent-filter>
  <action android:name="android.intent.action.VIEW" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.BROWSABLE" />
  <data android:scheme="myapp" android:host="payment" />
</intent-filter>
```

**iOS (Info.plist):**
```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>myapp</string>
    </array>
  </dict>
</array>
```

---

## 🔔 Настройка вебхуков

### Для разработки (локально):

1. Установите ngrok: https://ngrok.com/
2. Запустите туннель:
   ```bash
   ngrok http 8000
   ```
3. Скопируйте URL (например: `https://abc123.ngrok.io`)
4. Обновите `BASE_URL` в `.env`:
   ```env
   BASE_URL=https://abc123.ngrok.io
   ```
5. Перезапустите сервер

### Для продакшена:

1. Разверните приложение на сервере с публичным IP
2. Настройте HTTPS (обязательно!)
3. Укажите URL вашего сервера в `BASE_URL`:
   ```env
   BASE_URL=https://yourdomain.com
   ```

**URL вебхука:** `{BASE_URL}/api/subscriptions/webhook`

Точка будет автоматически отправлять уведомления на этот URL при изменении статуса платежа.

---

## 🎯 Полный Flow оплаты

```
1. Пользователь выбирает тариф
   ↓
2. Фронт вызывает POST /api/subscriptions/purchase
   ↓
3. Бэкенд создает запись платежа в БД (status=pending)
   ↓
4. Бэкенд создает платёжную ссылку в Точке
   ↓
5. Бэкенд обновляет платеж (status=processing, payment_url=...)
   ↓
6. Фронт получает payment_url и открывает в браузере
   ↓
7. Пользователь оплачивает через Точку (карта/СБП)
   ↓
8. Точка отправляет вебхук на /api/subscriptions/webhook
   ↓
9. Бэкенд обрабатывает вебхук:
   - Обновляет payment (status=succeeded)
   - Создает subscription
   - Обновляет user (subscription_status=active)
   ↓
10. Точка делает редирект на return_url
   ↓
11. Фронт получает deep link и проверяет статус
   ↓
12. Фронт показывает результат и обновляет UI
```

---

## 📊 Структура БД

### subscription_plans
- id, uuid
- plan_type (enum: month_1, month_3, month_6, month_12)
- name, duration_months
- price, price_per_month
- description, is_active
- created_at, updated_at

### payments
- id, uuid
- user_id → user.id
- plan_id → subscription_plans.id
- amount, status (enum)
- payment_id (от Точки)
- payment_url, receipt_url
- error_message, payment_metadata
- created_at, updated_at, paid_at

### subscriptions
- id, uuid
- user_id → user.id
- plan_id → subscription_plans.id
- payment_id → payments.id
- started_at, expires_at
- is_trial, auto_renew
- created_at, updated_at

### user (новые поля)
- trial_used (bool)
- trial_started_at (datetime)

---

## 🛠️ Полезные команды

```bash
# Создать миграцию
alembic revision --autogenerate -m "описание"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# Создать тарифные планы
python create_subscription_plans.py

# Запустить сервер
uvicorn app.main:app --reload
```

---

## 📝 TODO (будущие улучшения)

- [ ] Автопродление подписок
- [ ] Промокоды и скидки
- [ ] Семейная подписка
- [ ] Возврат платежей
- [ ] Email-уведомления о статусе подписки
- [ ] Push-уведомления за 3 дня до окончания
- [ ] Реферальная программа

---

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи сервера
2. Проверьте правильность JWT-токена
3. Убедитесь, что вебхуки доходят до сервера
4. Проверьте статус платежа в личном кабинете Точки

**Документация Точка API:** https://developers.tochka.com/docs/tochka-api/
