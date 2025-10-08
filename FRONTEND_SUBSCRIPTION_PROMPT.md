# 🎨 Промпт для реализации фронтенд части системы подписок

## 📋 КОНТЕКСТ

Реализована полная система подписок с интеграцией платежной системы Точка Банк на бэкенде. Необходимо создать фронтенд интерфейс для управления подписками.

---

## 🎯 БИЗНЕС-ТРЕБОВАНИЯ

### Функционал подписки:

1. **Триальный период:** 14 дней бесплатно при регистрации (активируется автоматически)
2. **Тарифные планы:**
   - 1 месяц - 990₽ (990₽/мес)
   - 3 месяца - 2490₽ (830₽/мес, выгода 16%)
   - 6 месяцев - 4490₽ (748₽/мес, выгода 24%)
   - 12 месяцев - 7990₽ (666₽/мес, выгода 33%)

3. **Пользователь может:**
   - Просматривать статус своей подписки
   - Покупать/продлевать подписку
   - Просматривать историю платежей
   - Выбирать способы оплаты (карта или СБП)

4. **Процесс оплаты:**
   - Выбор тарифа → создание платёжной ссылки → переход в браузер
   - Оплата на стороне Точки → редирект обратно в приложение
   - Проверка статуса → обновление UI

---

## 📡 API ENDPOINTS (BACKEND)

### 1. GET /api/subscriptions/plans
**Описание:** Получить список всех доступных тарифных планов

**Требует авторизации:** НЕТ

**Request:** Без параметров

**Response 200:**
```typescript
Array<{
  uuid: string;              // "59547ece-6264-45aa-b584-2552fe1700e1"
  plan_type: string;         // "month_1" | "month_3" | "month_6" | "month_12"
  name: string;              // "1 месяц"
  duration_months: number;   // 1
  price: number;             // 990.00
  price_per_month: number;   // 990.00
  description: string | null;// "Подписка на 1 месяц"
  is_active: boolean;        // true
}>
```

**Пример ответа:**
```json
[
  {
    "uuid": "59547ece-6264-45aa-b584-2552fe1700e1",
    "plan_type": "month_1",
    "name": "1 месяц",
    "duration_months": 1,
    "price": 990.00,
    "price_per_month": 990.00,
    "description": "Подписка на 1 месяц",
    "is_active": true
  },
  {
    "uuid": "388150b5-ff0b-4143-bb20-d6f93694627d",
    "plan_type": "month_3",
    "name": "3 месяца",
    "duration_months": 3,
    "price": 2490.00,
    "price_per_month": 830.00,
    "description": "Подписка на 3 месяца. Выгода 16%!",
    "is_active": true
  }
]
```

---

### 2. GET /api/subscriptions/status
**Описание:** Получить статус подписки текущего пользователя

**Требует авторизации:** ДА (Bearer token)

**Request:** Без параметров

**Response 200:**
```typescript
{
  subscription_status: "pending" | "active" | "expired";
  subscription_until: string | null;  // "2025-11-07" (дата в формате YYYY-MM-DD)
  is_trial: boolean;                  // true если триальная подписка
  trial_used: boolean;                // true если триал уже использован
  days_remaining: number | null;      // 14 (дней до окончания)
}
```

**Пример ответа:**
```json
{
  "subscription_status": "active",
  "subscription_until": "2025-10-22",
  "is_trial": true,
  "trial_used": true,
  "days_remaining": 14
}
```

---

### 3. POST /api/subscriptions/activate-trial
**Описание:** Активировать триальный период вручную (обычно активируется автоматически при регистрации)

**Требует авторизации:** ДА

**Request:** Без параметров

**Response 200:**
```typescript
{
  message: string;           // "Триальный период успешно активирован!"
  subscription_uuid: string; // UUID подписки
  expires_at: string;        // "2025-10-22T12:00:00" (ISO datetime)
  is_trial: boolean;         // true
}
```

**Response 400:** Триал уже использован
```json
{
  "detail": "Триальный период уже использован"
}
```

---

### 4. POST /api/subscriptions/purchase
**Описание:** Создать платёжную ссылку для покупки подписки

**Требует авторизации:** ДА

**Request Body:**
```typescript
{
  plan_uuid: string;           // UUID тарифного плана (из /plans)
  return_url?: string;         // Опционально, URL для возврата (по умолчанию deep link)
  payment_mode?: string[];     // ["card", "sbp"] по умолчанию. Возможно: "card", "sbp", "tinkoff", "dolyame"
}
```

**Пример запроса:**
```json
{
  "plan_uuid": "59547ece-6264-45aa-b584-2552fe1700e1",
  "return_url": "myapp://payment/callback",
  "payment_mode": ["card", "sbp"]
}
```

**Response 200:**
```typescript
{
  payment_uuid: string;      // "ed07d0cc-91e2-4a0b-97f2-c41bcb5c4227"
  payment_url: string;       // "https://merch.tochka.com/order/?uuid=..."
  payment_link_id: string;   // "11"
  operation_id: string;      // "0c9639fc-5762-41c3-aa48-f5bf60bee75b"
}
```

**Что делать с ответом:**
1. Сохранить `payment_uuid` локально
2. Открыть `payment_url` в браузере/WebView
3. Пользователь оплачивает
4. Точка делает редирект на `return_url`
5. Проверить статус через `/payment/{payment_uuid}/status`

---

### 5. GET /api/subscriptions/payment/{payment_uuid}/status
**Описание:** Проверить статус конкретного платежа

**Требует авторизации:** ДА

**Path параметр:** `payment_uuid` - UUID платежа из ответа `/purchase`

**Response 200:**
```typescript
{
  status: "pending" | "processing" | "succeeded" | "failed" | "cancelled";
  amount: number;            // 990.00
  created_at: string;        // "2025-10-08T12:00:00" (ISO datetime)
  paid_at: string | null;    // "2025-10-08T12:05:00" или null
  receipt_url: string | null;// "https://..." URL чека
}
```

**Пример ответа (в процессе):**
```json
{
  "status": "processing",
  "amount": 990.00,
  "created_at": "2025-10-08T12:00:00",
  "paid_at": null,
  "receipt_url": null
}
```

**Пример ответа (успешно):**
```json
{
  "status": "succeeded",
  "amount": 990.00,
  "created_at": "2025-10-08T12:00:00",
  "paid_at": "2025-10-08T12:05:00",
  "receipt_url": "https://check.tochka.com/..."
}
```

---

### 6. GET /api/subscriptions/history
**Описание:** Получить историю платежей пользователя

**Требует авторизации:** ДА

**Request:** Без параметров

**Response 200:**
```typescript
{
  payments: Array<{
    uuid: string;           // UUID платежа
    amount: number;         // 990.00
    status: string;         // "succeeded" | "failed" | "cancelled"
    plan_name: string;      // "1 месяц"
    created_at: string;     // ISO datetime
    paid_at: string | null; // ISO datetime
    receipt_url: string | null;
  }>
}
```

**Пример ответа:**
```json
{
  "payments": [
    {
      "uuid": "ed07d0cc-91e2-4a0b-97f2-c41bcb5c4227",
      "amount": 990.00,
      "status": "succeeded",
      "plan_name": "1 месяц",
      "created_at": "2025-10-08T12:00:00",
      "paid_at": "2025-10-08T12:05:00",
      "receipt_url": "https://check.tochka.com/..."
    },
    {
      "uuid": "...",
      "amount": 2490.00,
      "status": "succeeded",
      "plan_name": "3 месяца",
      "created_at": "2025-09-01T15:30:00",
      "paid_at": "2025-09-01T15:32:00",
      "receipt_url": "https://..."
    }
  ]
}
```

---

## 🎨 ТРЕБУЕМЫЕ ЭКРАНЫ/КОМПОНЕНТЫ

### Экран 1: Профиль пользователя (обновить существующий)

**Что добавить:**

1. **Блок статуса подписки** (в верхней части профиля):

```tsx
<SubscriptionStatusCard>
  {/* Если подписка активна */}
  {status === 'active' && (
    <>
      <StatusBadge color="green">Активна</StatusBadge>
      {isTrial && <TrialBadge>Триальная</TrialBadge>}
      <Text>Действует до: {formatDate(subscription_until)}</Text>
      <Text>Осталось дней: {days_remaining}</Text>
      <Button onPress={() => navigate('SubscriptionPlans')}>
        Продлить подписку
      </Button>
    </>
  )}
  
  {/* Если подписка истекла */}
  {status === 'expired' && (
    <>
      <StatusBadge color="red">Истекла</StatusBadge>
      <Text>Подписка закончилась {formatDate(subscription_until)}</Text>
      <Button primary onPress={() => navigate('SubscriptionPlans')}>
        Продлить подписку
      </Button>
    </>
  )}
  
  {/* Если нет подписки */}
  {status === 'pending' && (
    <>
      <StatusBadge color="gray">Нет подписки</StatusBadge>
      {!trial_used && (
        <Button onPress={activateTrial}>
          Активировать триал (14 дней бесплатно)
        </Button>
      )}
      <Button primary onPress={() => navigate('SubscriptionPlans')}>
        Купить подписку
      </Button>
    </>
  )}
</SubscriptionStatusCard>
```

**API вызовы:**
```typescript
// При открытии профиля
const status = await api.get('/api/subscriptions/status');
```

---

### Экран 2: Выбор тарифного плана (новый экран)

**Роут:** `SubscriptionPlans` или `/subscription/plans`

**Что отображать:**

```tsx
<SubscriptionPlansScreen>
  <Header>
    <BackButton />
    <Title>Выбор подписки</Title>
  </Header>
  
  <CurrentStatus>
    {/* Показать текущую подписку если есть */}
    {hasActiveSubscription && (
      <InfoCard>
        Текущая подписка до: {subscription_until}
        При покупке новой подписки срок продлится без разрыва
      </InfoCard>
    )}
  </CurrentStatus>
  
  <PlansList>
    {plans.map(plan => (
      <PlanCard key={plan.uuid}>
        <PlanHeader>
          <PlanName>{plan.name}</PlanName>
          {plan.duration_months > 1 && (
            <DiscountBadge>
              Выгода {calculateDiscount(plan)}%
            </DiscountBadge>
          )}
        </PlanHeader>
        
        <PriceBlock>
          <MainPrice>{formatPrice(plan.price)}</MainPrice>
          <PricePerMonth>
            {formatPrice(plan.price_per_month)}/месяц
          </PricePerMonth>
        </PriceBlock>
        
        <Description>{plan.description}</Description>
        
        <Features>
          <Feature>✓ Доступ ко всем тренировкам</Feature>
          <Feature>✓ Персональные программы</Feature>
          <Feature>✓ Отслеживание прогресса</Feature>
          <Feature>✓ Достижения и награды</Feature>
        </Features>
        
        <BuyButton 
          onPress={() => handlePurchase(plan)}
          primary={plan.duration_months === 3} // Выделить выгодный
        >
          Купить за {formatPrice(plan.price)}
        </BuyButton>
      </PlanCard>
    ))}
  </PlansList>
</SubscriptionPlansScreen>
```

**API вызовы:**
```typescript
// При открытии экрана
const plans = await api.get('/api/subscriptions/plans');

// Функция расчета скидки
function calculateDiscount(plan) {
  const basePricePerMonth = 990; // Цена 1 месяца
  const discount = ((basePricePerMonth - plan.price_per_month) / basePricePerMonth) * 100;
  return Math.round(discount);
}
```

---

### Экран 3: Обработка платежа (логика, не отдельный экран)

**Flow:**

```typescript
async function handlePurchase(plan) {
  try {
    // 1. Показать лоадер
    setLoading(true);
    
    // 2. Создать платёжную ссылку
    const response = await api.post('/api/subscriptions/purchase', {
      plan_uuid: plan.uuid,
      // return_url опционален, бэк подставит deep link автоматически
      payment_mode: ["card", "sbp"] // опционально
    });
    
    const { payment_url, payment_uuid } = response.data;
    
    // 3. Сохранить payment_uuid для проверки после возврата
    await AsyncStorage.setItem('current_payment_uuid', payment_uuid);
    await AsyncStorage.setItem('payment_plan_name', plan.name);
    
    // 4. Открыть браузер для оплаты
    await Linking.openURL(payment_url);
    
    setLoading(false);
    
  } catch (error) {
    setLoading(false);
    showError('Ошибка создания платежа: ' + error.message);
  }
}
```

---

### Компонент 4: Обработка Deep Link после оплаты

**Deep Link схема:** `myapp://payment/callback`

**Настройка Deep Links:**

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

**React Native код:**

```typescript
import { Linking } from 'react-native';
import { useEffect } from 'react';
import { useNavigation } from '@react-navigation/native';

export function usePaymentDeepLink() {
  const navigation = useNavigation();
  
  useEffect(() => {
    // Обработка initial URL (если приложение было закрыто)
    Linking.getInitialURL().then(url => {
      if (url) handleDeepLink(url);
    });
    
    // Обработка URL когда приложение открыто
    const subscription = Linking.addEventListener('url', ({ url }) => {
      handleDeepLink(url);
    });
    
    return () => subscription.remove();
  }, []);
  
  async function handleDeepLink(url: string) {
    console.log('Deep link received:', url);
    
    // Проверяем что это ссылка возврата из оплаты
    if (url.startsWith('myapp://payment/callback')) {
      // Получаем сохраненный payment_uuid
      const payment_uuid = await AsyncStorage.getItem('current_payment_uuid');
      
      if (!payment_uuid) {
        console.warn('payment_uuid не найден');
        return;
      }
      
      // Переходим на экран проверки платежа
      navigation.navigate('PaymentCheck', { payment_uuid });
    }
  }
}
```

---

### Экран 5: Проверка статуса платежа (новый экран)

**Роут:** `PaymentCheck` с параметром `payment_uuid`

**Что делать:**

```tsx
<PaymentCheckScreen>
  <Loader text="Проверка оплаты..." />
  
  {/* После успешной оплаты */}
  {status === 'succeeded' && (
    <SuccessAnimation>
      <Icon name="check-circle" size={80} color="green" />
      <Title>Оплата успешна!</Title>
      <Text>Подписка "{plan_name}" активирована</Text>
      <Text>Действует до: {subscription_until}</Text>
      
      {receipt_url && (
        <Button onPress={() => Linking.openURL(receipt_url)}>
          Скачать чек
        </Button>
      )}
      
      <Button primary onPress={() => navigation.navigate('Profile')}>
        Вернуться в профиль
      </Button>
    </SuccessAnimation>
  )}
  
  {/* При ошибке оплаты */}
  {status === 'failed' && (
    <ErrorView>
      <Icon name="x-circle" size={80} color="red" />
      <Title>Оплата не прошла</Title>
      <Text>Попробуйте снова или выберите другой способ оплаты</Text>
      
      <Button onPress={() => navigation.navigate('SubscriptionPlans')}>
        Выбрать другой тариф
      </Button>
    </ErrorView>
  )}
</PaymentCheckScreen>
```

**Логика проверки:**

```typescript
function PaymentCheckScreen({ route }) {
  const { payment_uuid } = route.params;
  const [status, setStatus] = useState('checking');
  const [paymentInfo, setPaymentInfo] = useState(null);
  
  useEffect(() => {
    checkPaymentStatus();
  }, []);
  
  async function checkPaymentStatus() {
    const maxAttempts = 15; // Максимум 30 секунд (15 * 2 сек)
    let attempts = 0;
    
    const check = async () => {
      try {
        const response = await api.get(
          `/api/subscriptions/payment/${payment_uuid}/status`
        );
        
        console.log('Payment status:', response.data.status);
        
        if (response.data.status === 'succeeded') {
          // ✅ Оплата прошла
          setStatus('succeeded');
          setPaymentInfo(response.data);
          
          // Обновляем данные пользователя
          await refreshUserData();
          
          // Очищаем сохраненные данные
          await AsyncStorage.removeItem('current_payment_uuid');
          
        } else if (response.data.status === 'processing' || response.data.status === 'pending') {
          // ⏳ Еще в процессе
          attempts++;
          
          if (attempts < maxAttempts) {
            // Проверяем снова через 2 секунды
            setTimeout(check, 2000);
          } else {
            // Превышен лимит попыток
            setStatus('timeout');
            showInfo('Оплата обрабатывается. Проверьте статус позже.');
          }
          
        } else {
          // ❌ failed, cancelled
          setStatus('failed');
          setPaymentInfo(response.data);
        }
        
      } catch (error) {
        console.error('Error checking payment:', error);
        setStatus('error');
        showError('Ошибка проверки платежа');
      }
    };
    
    // Первая проверка
    check();
  }
  
  return (/* UI из примера выше */);
}
```

---

### Экран 6: История платежей (опционально, но желательно)

**Роут:** `PaymentHistory` или `/subscription/history`

```tsx
<PaymentHistoryScreen>
  <Header>
    <BackButton />
    <Title>История платежей</Title>
  </Header>
  
  <PaymentsList>
    {payments.length === 0 && (
      <EmptyState>
        <Icon name="receipt" size={60} />
        <Text>Платежей пока нет</Text>
      </EmptyState>
    )}
    
    {payments.map(payment => (
      <PaymentCard key={payment.uuid}>
        <PaymentHeader>
          <PlanName>{payment.plan_name}</PlanName>
          <StatusBadge status={payment.status}>
            {getStatusText(payment.status)}
          </StatusBadge>
        </PaymentHeader>
        
        <PaymentDetails>
          <DetailRow>
            <Label>Сумма:</Label>
            <Value>{formatPrice(payment.amount)}</Value>
          </DetailRow>
          
          <DetailRow>
            <Label>Дата:</Label>
            <Value>{formatDate(payment.created_at)}</Value>
          </DetailRow>
          
          {payment.paid_at && (
            <DetailRow>
              <Label>Оплачено:</Label>
              <Value>{formatDateTime(payment.paid_at)}</Value>
            </DetailRow>
          )}
        </PaymentDetails>
        
        {payment.receipt_url && payment.status === 'succeeded' && (
          <DownloadReceiptButton 
            onPress={() => Linking.openURL(payment.receipt_url)}
          >
            Скачать чек
          </DownloadReceiptButton>
        )}
      </PaymentCard>
    ))}
  </PaymentsList>
</PaymentHistoryScreen>
```

**API вызов:**
```typescript
const response = await api.get('/api/subscriptions/history');
const { payments } = response.data;
```

**Функции форматирования:**
```typescript
function getStatusText(status: string): string {
  const statusMap = {
    'succeeded': 'Оплачен',
    'failed': 'Ошибка',
    'cancelled': 'Отменен',
    'processing': 'В обработке',
    'pending': 'Ожидает оплаты'
  };
  return statusMap[status] || status;
}

function formatPrice(amount: number): string {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0
  }).format(amount);
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('ru-RU');
}

function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('ru-RU');
}
```

---

## 🔄 ПОЛНЫЙ FLOW ПОЛЬЗОВАТЕЛЯ

### Сценарий 1: Новый пользователь (триал)

```
1. Регистрация
   ↓ (автоматически)
2. Триал активирован (14 дней)
   ↓
3. Профиль → видит "Триальная подписка, осталось 14 дней"
   ↓ (через 14 дней, cron обновляет статус)
4. Подписка истекла → subscription_status = 'expired'
   ↓
5. Профиль → видит "Подписка истекла" + кнопка "Продлить"
   ↓
6. Нажимает "Продлить" → Экран выбора тарифа
   ↓
7. Выбирает тариф → создается платёжная ссылка
   ↓
8. Открывается браузер → оплата на стороне Точки
   ↓
9. После оплаты → редирект myapp://payment/callback
   ↓
10. Приложение получает deep link → экран проверки платежа
   ↓
11. Проверка статуса каждые 2 сек → status = 'succeeded'
   ↓
12. Показать "Успешно!" → обновить данные пользователя
   ↓
13. Вернуться в профиль → видит "Активна до ..."
```

---

### Сценарий 2: Продление активной подписки

```
1. Профиль → "Активна до 08.11.2025, осталось 30 дней"
   ↓
2. Нажимает "Продлить" → Экран выбора тарифа
   ↓
3. Выбирает "3 месяца" → оплата
   ↓
4. После успешной оплаты:
   - Старая дата: 08.11.2025
   - Новая дата: 08.02.2026 (старая + 90 дней)
   - Подписка продлена БЕЗ РАЗРЫВА
```

---

## 📱 ДИЗАЙН РЕКОМЕНДАЦИИ

### Цветовая схема для статусов:

```typescript
const statusColors = {
  active: '#22C55E',    // Зеленый
  expired: '#EF4444',   // Красный
  pending: '#94A3B8',   // Серый
  trial: '#3B82F6'      // Синий (для триала)
};
```

### Акценты:

1. **Самый выгодный тариф** (3 или 6 месяцев):
   - Бейдж "Популярный" или "Выгодно"
   - Яркая рамка
   - Первичная кнопка

2. **Триальная подписка:**
   - Специальный бейдж "Триал"
   - Обратный отсчет дней

3. **Истекшая подписка:**
   - Красное предупреждение
   - Крупная кнопка "Продлить"

---

## 🛠️ ТЕХНИЧЕСКИЕ ДЕТАЛИ

### State Management

Рекомендую хранить глобально:

```typescript
// Zustand или Redux
interface SubscriptionState {
  status: 'pending' | 'active' | 'expired';
  subscription_until: string | null;
  is_trial: boolean;
  trial_used: boolean;
  days_remaining: number | null;
  plans: Plan[];
}

// Actions
async function fetchSubscriptionStatus() {
  const data = await api.get('/api/subscriptions/status');
  setSubscriptionState(data);
}

async function fetchPlans() {
  const plans = await api.get('/api/subscriptions/plans');
  setPlans(plans);
}
```

---

### API Client

```typescript
// api/subscriptions.ts

export const subscriptionsAPI = {
  // Получить список тарифов
  getPlans: async () => {
    const response = await apiClient.get('/api/subscriptions/plans');
    return response.data;
  },
  
  // Получить статус подписки
  getStatus: async () => {
    const response = await apiClient.get('/api/subscriptions/status');
    return response.data;
  },
  
  // Активировать триал
  activateTrial: async () => {
    const response = await apiClient.post('/api/subscriptions/activate-trial');
    return response.data;
  },
  
  // Создать платёжную ссылку
  createPayment: async (planUuid: string, paymentMode?: string[]) => {
    const response = await apiClient.post('/api/subscriptions/purchase', {
      plan_uuid: planUuid,
      payment_mode: paymentMode
    });
    return response.data;
  },
  
  // Проверить статус платежа
  checkPaymentStatus: async (paymentUuid: string) => {
    const response = await apiClient.get(
      `/api/subscriptions/payment/${paymentUuid}/status`
    );
    return response.data;
  },
  
  // Получить историю платежей
  getHistory: async () => {
    const response = await apiClient.get('/api/subscriptions/history');
    return response.data;
  }
};
```

---

## ⚠️ ВАЖНЫЕ МОМЕНТЫ

### 1. **Обработка ошибок**

```typescript
try {
  await subscriptionsAPI.createPayment(plan.uuid);
} catch (error) {
  if (error.response?.status === 400) {
    // Неверные данные
    showError(error.response.data.detail);
  } else if (error.response?.status === 401) {
    // Не авторизован
    navigation.navigate('Login');
  } else {
    // Другие ошибки
    showError('Ошибка создания платежа. Попробуйте позже.');
  }
}
```

---

### 2. **Timeout для проверки платежа**

```typescript
// Не проверяйте бесконечно!
const MAX_ATTEMPTS = 15;  // 30 секунд
const CHECK_INTERVAL = 2000; // 2 секунды

// Если превышен лимит:
if (attempts >= MAX_ATTEMPTS) {
  showInfo('Оплата обрабатывается. Статус обновится автоматически.');
  navigation.navigate('PaymentHistory');
}
```

---

### 3. **Обновление данных после оплаты**

```typescript
async function refreshUserData() {
  // Обновить глобальное состояние пользователя
  await fetchUserProfile();
  await fetchSubscriptionStatus();
}
```

---

### 4. **Отображение времени действия ссылки**

Платёжная ссылка действует **5 минут** (`ttl: 5`). Можно показать таймер:

```typescript
<PaymentLinkNotice>
  ⚠️ Ссылка действительна 5 минут
</PaymentLinkNotice>
```

---

## 📊 UI КОМПОНЕНТЫ

### Индикатор подписки на главном экране

```tsx
<SubscriptionBanner>
  {subscription_status === 'active' && days_remaining <= 3 && (
    <WarningBanner>
      ⚠️ Подписка заканчивается через {days_remaining} дней
      <Button size="small" onPress={() => navigate('SubscriptionPlans')}>
        Продлить
      </Button>
    </WarningBanner>
  )}
  
  {subscription_status === 'expired' && (
    <ExpiredBanner>
      ❌ Подписка истекла
      <Button primary onPress={() => navigate('SubscriptionPlans')}>
        Продлить подписку
      </Button>
    </ExpiredBanner>
  )}
</SubscriptionBanner>
```

---

## 🎯 МИНИМАЛЬНО НЕОБХОДИМЫЙ ФУНКЦИОНАЛ

### Обязательно реализовать:

- [x] Экран выбора тарифа (список планов)
- [x] Покупка подписки (создание платёжной ссылки)
- [x] Открытие браузера для оплаты
- [x] Deep Link обработка возврата
- [x] Проверка статуса платежа
- [x] Отображение статуса подписки в профиле
- [x] Обновление UI после успешной оплаты

### Желательно добавить:

- [ ] История платежей
- [ ] Скачивание чеков
- [ ] Уведомления об окончании подписки
- [ ] Красивые анимации успеха/ошибки
- [ ] Выбор способов оплаты (карта/СБП)

---

## 📝 ТИПЫ ДАННЫХ (TypeScript)

```typescript
// types/subscription.ts

export interface SubscriptionPlan {
  uuid: string;
  plan_type: 'month_1' | 'month_3' | 'month_6' | 'month_12';
  name: string;
  duration_months: number;
  price: number;
  price_per_month: number;
  description: string | null;
  is_active: boolean;
}

export interface SubscriptionStatus {
  subscription_status: 'pending' | 'active' | 'expired';
  subscription_until: string | null;
  is_trial: boolean;
  trial_used: boolean;
  days_remaining: number | null;
}

export interface PaymentResponse {
  payment_uuid: string;
  payment_url: string;
  payment_link_id: string;
  operation_id: string;
}

export interface PaymentStatus {
  status: 'pending' | 'processing' | 'succeeded' | 'failed' | 'cancelled';
  amount: number;
  created_at: string;
  paid_at: string | null;
  receipt_url: string | null;
}

export interface PaymentHistoryItem {
  uuid: string;
  amount: number;
  status: string;
  plan_name: string;
  created_at: string;
  paid_at: string | null;
  receipt_url: string | null;
}
```

---

## ✅ ЧЕКЛИСТ РЕАЛИЗАЦИИ

### Подготовка:
- [ ] Установить зависимости для deep links (если еще нет)
- [ ] Настроить deep link схему `myapp://`
- [ ] Протестировать открытие браузера из приложения

### Экраны:
- [ ] Обновить экран профиля (добавить блок подписки)
- [ ] Создать экран выбора тарифов
- [ ] Создать экран проверки платежа
- [ ] Создать экран истории платежей (опционально)

### Логика:
- [ ] API клиент для всех endpoints
- [ ] Обработка deep links
- [ ] Проверка статуса платежа с retry
- [ ] Обновление глобального состояния
- [ ] Обработка ошибок

### UI/UX:
- [ ] Компонент карточки тарифа
- [ ] Индикаторы статуса подписки
- [ ] Анимации успеха/ошибки
- [ ] Лоадеры и скелетоны

---

## 🚀 НАЧНИ С ЭТОГО

Используй этот промпт в Cursor для реализации фронтенда:

```
Мне нужно реализовать систему подписок на фронтенде (React Native / Flutter / что используется).

КОНТЕКСТ:
На бэкенде реализована полная система подписок с интеграцией Точка Банк.
Пользователь получает 14 дней триала при регистрации.
Есть 4 тарифных плана: 1, 3, 6, 12 месяцев.

НУЖНО РЕАЛИЗОВАТЬ:

1. ЭКРАН ВЫБОРА ТАРИФА
- Показать список планов из GET /api/subscriptions/plans
- Карточки с ценой, выгодой, описанием
- Выделить самый выгодный тариф
- Кнопка "Купить" для каждого плана

2. ПРОЦЕСС ОПЛАТЫ
- При клике на "Купить" → POST /api/subscriptions/purchase
- Получить payment_url → открыть в браузере
- Сохранить payment_uuid локально

3. ОБРАБОТКА ВОЗВРАТА ИЗ ОПЛАТЫ
- Deep link: myapp://payment/callback
- Получить сохраненный payment_uuid
- Переход на экран проверки статуса

4. ЭКРАН ПРОВЕРКИ ПЛАТЕЖА
- Показать лоадер "Проверка оплаты..."
- Опрашивать GET /api/subscriptions/payment/{uuid}/status каждые 2 сек
- Максимум 15 попыток (30 секунд)
- При succeeded → показать успех, обновить данные
- При failed → показать ошибку

5. ОБНОВИТЬ ЭКРАН ПРОФИЛЯ
- Показать статус подписки (GET /api/subscriptions/status)
- Дата окончания и дней до окончания
- Кнопка "Продлить" или "Активировать триал"

6. (ОПЦИОНАЛЬНО) ИСТОРИЯ ПЛАТЕЖЕЙ
- GET /api/subscriptions/history
- Список всех платежей с чеками

ДЕТАЛИ В ФАЙЛЕ: [прикрепить этот документ]
```

---

Этот промпт можно использовать в Cursor! 🎯
