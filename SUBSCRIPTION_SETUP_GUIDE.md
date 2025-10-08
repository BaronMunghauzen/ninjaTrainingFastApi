# 🚀 Инструкция по запуску системы подписок

## ✅ Что уже сделано

Вся система подписок реализована и готова к использованию:

1. ✅ Созданы модели данных (SubscriptionPlan, Payment, Subscription)
2. ✅ Реализован сервис интеграции с Точка API
3. ✅ Создан сервис бизнес-логики подписок
4. ✅ Добавлены API endpoints
5. ✅ Обновлена модель User
6. ✅ Создана миграция базы данных
7. ✅ Роутер подключен к приложению

---

## 📝 Следующие шаги

### 1. Настройте переменные окружения

Откройте файл `.env` и добавьте/обновите следующие переменные:

```env
# Настройки Точка Банк
TOCHKA_ACCESS_TOKEN=your_jwt_token_here
TOCHKA_API_URL=https://api.tochka.com/v1
TOCHKA_VAT_CODE=vat20

# URL вашего сервера (для вебхуков)
BASE_URL=http://localhost:8000
```

**Куда вставить JWT-токен:**
- Замените `your_jwt_token_here` на ваш реальный JWT-токен от Точки
- Токен можно получить в личном кабинете Точки: https://enter.tochka.com/

**Важно про BASE_URL:**
- Для разработки можно оставить `http://localhost:8000`
- Для работы вебхуков нужен публичный URL (используйте ngrok)
- Для продакшена укажите реальный домен с HTTPS

---

### 2. Примените миграцию базы данных

```bash
# Убедитесь, что виртуальное окружение активировано
.\.venv\Scripts\Activate.ps1

# Примените миграцию
alembic upgrade head
```

Это создаст новые таблицы:
- `subscription_plans` - тарифные планы
- `payments` - платежи
- `subscriptions` - подписки
- Добавит поля `trial_used` и `trial_started_at` в таблицу `user`

---

### 3. Создайте тарифные планы

```bash
python create_subscription_plans.py
```

Это создаст 4 стандартных плана:
- 1 месяц - 990₽
- 3 месяца - 2490₽ (выгода 16%)
- 6 месяцев - 4490₽ (выгода 24%)
- 12 месяцев - 7990₽ (выгода 33%)

**Если хотите изменить цены:**
Отредактируйте файл `create_subscription_plans.py` перед запуском.

---

### 4. Запустите сервер

```bash
uvicorn app.main:app --reload
```

Сервер запустится на `http://localhost:8000`

---

### 5. Проверьте работу API

Откройте в браузере:
```
http://localhost:8000/docs
```

Вы увидите Swagger документацию со всеми новыми endpoints:
- `GET /api/subscriptions/plans` - список тарифов
- `POST /api/subscriptions/activate-trial` - активация триала
- `POST /api/subscriptions/purchase` - покупка подписки
- `GET /api/subscriptions/status` - статус подписки
- `GET /api/subscriptions/payment/{uuid}/status` - статус платежа
- `GET /api/subscriptions/history` - история платежей
- `POST /api/subscriptions/webhook` - вебхук от Точки

---

### 6. (Опционально) Настройте ngrok для тестирования вебхуков

Для тестирования вебхуков локально:

```bash
# Установите ngrok: https://ngrok.com/download
ngrok http 8000
```

Скопируйте URL (например: `https://abc123.ngrok.io`) и обновите в `.env`:
```env
BASE_URL=https://abc123.ngrok.io
```

Перезапустите сервер.

---

## 🧪 Тестирование

### Тест 1: Получение списка тарифов

```bash
curl http://localhost:8000/api/subscriptions/plans
```

Должен вернуть список из 4 тарифных планов.

### Тест 2: Активация триала (требует авторизации)

```bash
curl -X POST http://localhost:8000/api/subscriptions/activate-trial \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Тест 3: Создание платежа (требует авторизации)

```bash
curl -X POST http://localhost:8000/api/subscriptions/purchase \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_id": 1}'
```

Должен вернуть `payment_url` для оплаты.

---

## 📱 Интеграция на фронтенде

### Основной flow:

1. **Получить список тарифов**
   ```typescript
   GET /api/subscriptions/plans
   ```

2. **Пользователь выбирает тариф**
   
3. **Создать платёжную ссылку**
   ```typescript
   POST /api/subscriptions/purchase
   Body: { plan_id: 1 }
   ```

4. **Открыть payment_url в браузере**
   ```typescript
   Linking.openURL(payment_url)
   ```

5. **После оплаты обработать Deep Link**
   ```typescript
   // myapp://payment/callback?payment_uuid=xxx
   ```

6. **Проверить статус платежа**
   ```typescript
   GET /api/subscriptions/payment/{payment_uuid}/status
   ```

7. **Обновить UI**

Подробные примеры кода - в файле `app/subscriptions/README.md`

---

## 🔧 Настройка Deep Links

### React Native:

```typescript
// Регистрация схемы
Linking.addEventListener('url', handleDeepLink);

const handleDeepLink = async ({ url }: { url: string }) => {
  if (url.startsWith('myapp://payment/callback')) {
    // Обработка возврата из оплаты
    const payment_uuid = extractPaymentUUID(url);
    await checkPaymentStatus(payment_uuid);
  }
};
```

### Android (AndroidManifest.xml):

```xml
<intent-filter>
  <action android:name="android.intent.action.VIEW" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.BROWSABLE" />
  <data android:scheme="myapp" android:host="payment" />
</intent-filter>
```

### iOS (Info.plist):

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

## 🎯 Чеклист готовности к продакшену

- [ ] Получен реальный JWT-токен от Точки
- [ ] Подключен интернет-эквайринг в Точке
- [ ] Настроен HTTPS на сервере
- [ ] Настроены переменные окружения
- [ ] Применены миграции
- [ ] Созданы тарифные планы
- [ ] Вебхуки доходят до сервера
- [ ] Протестирован полный цикл оплаты
- [ ] Настроены Deep Links в приложении
- [ ] Подготовлена договор оферты
- [ ] Подготовлена политика конфиденциальности

---

## 📚 Полезные ссылки

- Документация Точка API: https://developers.tochka.com/docs/tochka-api/
- Личный кабинет Точки: https://enter.tochka.com/
- Подробная документация модуля: `app/subscriptions/README.md`
- Регистрация ИП/ООО: https://www.nalog.gov.ru/

---

## ❓ Частые вопросы

**Q: Как получить JWT-токен?**
A: В личном кабинете Точки → Раздел API → Создать токен

**Q: Нужна ли онлайн-касса?**
A: Нет! Точка автоматически фискализирует чеки через платёжные ссылки.

**Q: Работает ли без PCI DSS?**
A: Да! Платёжные ссылки обрабатываются на стороне Точки.

**Q: Как тестировать без реальных платежей?**
A: Точка предоставляет sandbox-окружение для тестирования.

**Q: Вебхуки не доходят, что делать?**
A: Проверьте, что BASE_URL доступен извне (используйте ngrok для разработки).

**Q: Можно ли менять цены?**
A: Да, отредактируйте `create_subscription_plans.py` или обновите через SQL.

---

## 🆘 Поддержка

Если что-то не работает:
1. Проверьте логи сервера
2. Проверьте настройки в `.env`
3. Убедитесь, что миграции применены
4. Проверьте, что JWT-токен валидный
5. Посмотрите статус платежей в личном кабинете Точки

Удачи с запуском! 🚀
