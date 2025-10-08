# ⏰ Как работает истечение подписки

## 📊 Статусы подписки

В таблице `user` есть поле `subscription_status` с тремя возможными значениями:

```python
class SubscriptionStatusEnum(str, Enum):
    pending = "pending"   # Нет подписки
    active = "active"     # Подписка активна
    expired = "expired"   # Подписка истекла
```

---

## 🔄 Переход статусов

```
pending → active → expired
   ↑                  ↓
   └──────────────────┘
   (новая оплата)
```

**pending → active:**
- При активации триала
- При успешной оплате подписки

**active → expired:**
- Когда `user.subscription_until` < текущая дата
- **НЕ происходит автоматически!**
- Требует запуск проверки

**expired → active:**
- При новой оплате подписки

---

## ⚙️ Как настроить автоматическую проверку

### ✅ Метод 1: Cron (РЕКОМЕНДУЕТСЯ)

Самый простой и надежный способ - использовать системный cron.

**Шаг 1:** Скрипт уже создан: `check_expired_subscriptions.py`

**Шаг 2:** На сервере настройте cron:

```bash
# Откройте crontab
crontab -e

# Добавьте строку (проверка каждый день в 01:00 ночи):
0 1 * * * cd /home/admin/ninjaTrainingFastApi && /home/admin/ninjaTrainingFastApi/venv/bin/python check_expired_subscriptions.py >> /var/log/subscription_check.log 2>&1
```

**Расписание cron:**
```
0 1 * * *     - Каждый день в 01:00
0 */6 * * *   - Каждые 6 часов
0 */1 * * *   - Каждый час
*/30 * * * *  - Каждые 30 минут
```

**Шаг 3:** Проверьте что cron работает:

```bash
# Запустите скрипт вручную
cd /home/admin/ninjaTrainingFastApi
source venv/bin/activate
python check_expired_subscriptions.py

# Проверьте лог cron
tail -f /var/log/subscription_check.log
```

---

### ✅ Метод 2: Проверка при каждом запросе (простой, но неоптимальный)

Можно добавить middleware, который проверяет текущего пользователя:

```python
# app/main.py

@app.middleware("http")
async def check_user_subscription(request: Request, call_next):
    # Если пользователь авторизован
    if "authorization" in request.headers or "users_access_token" in request.cookies:
        try:
            from app.users.dependencies import get_current_user_optional
            user = await get_current_user_optional(request)
            
            if user and user.subscription_status == 'active':
                # Проверяем дату
                from datetime import date
                if user.subscription_until and user.subscription_until < date.today():
                    # Истекла - обновляем
                    from app.users.dao import UsersDAO
                    await UsersDAO.update(user.uuid, subscription_status='expired')
        except:
            pass
    
    return await call_next(request)
```

**Минусы:**
- Проверяется только для активных пользователей
- Лишний запрос в БД при каждом request
- Неактивные пользователи не обновятся

---

### ✅ Метод 3: Systemd timer (альтернатива cron)

```bash
# Создайте service
sudo nano /etc/systemd/system/subscription-check.service
```

```ini
[Unit]
Description=Check expired subscriptions
After=network.target

[Service]
Type=oneshot
User=admin
WorkingDirectory=/home/admin/ninjaTrainingFastApi
Environment="PATH=/home/admin/ninjaTrainingFastApi/venv/bin"
ExecStart=/home/admin/ninjaTrainingFastApi/venv/bin/python check_expired_subscriptions.py
```

```bash
# Создайте timer
sudo nano /etc/systemd/system/subscription-check.timer
```

```ini
[Unit]
Description=Check expired subscriptions daily

[Timer]
OnCalendar=daily
OnCalendar=01:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# Запустите timer
sudo systemctl enable subscription-check.timer
sudo systemctl start subscription-check.timer

# Проверьте статус
sudo systemctl list-timers
```

---

## 🎯 Рекомендация

**Используйте Cron (Метод 1):**
- ✅ Простой
- ✅ Надежный
- ✅ Работает независимо от приложения
- ✅ Не нагружает приложение

**Частота проверки:**
- Минимум: 1 раз в день (ночью)
- Оптимально: Каждые 6 часов
- Максимум: Каждый час

---

## 📝 Что делает скрипт:

```python
async def check_and_update_expired_subscriptions():
    # 1. Получает всех пользователей с active подпиской
    users = await UsersDAO.find_all(subscription_status='active')
    
    # 2. Для каждого проверяет дату
    for user in users:
        if user.subscription_until < today:
            # 3. Обновляет статус
            await UsersDAO.update(
                user.uuid,
                subscription_status='expired'  # ✅
            )
```

**Запись в `subscriptions` НЕ меняется** - она остается как история.  
Меняется только `user.subscription_status`.

---

## 🚀 Запушу скрипт в Git:

<function_calls>
<invoke name="run_terminal_cmd">
<parameter name="command">git add check_expired_subscriptions.py SUBSCRIPTION_EXPIRATION.md
