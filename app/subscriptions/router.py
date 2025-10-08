"""
API роутер для работы с подписками
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List
from datetime import datetime, date
import logging

from app.users.dependencies import get_current_user
from app.users.models import User
from app.subscriptions.service import SubscriptionService
from app.subscriptions.dao import SubscriptionPlanDAO, PaymentDAO, SubscriptionDAO
from app.subscriptions.schemas import (
    SPaymentInitiate,
    SPaymentResponse,
    SPaymentStatus,
    SSubscriptionStatus,
    SSubscriptionPlanResponse,
    STrialActivation
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/subscriptions', tags=['Subscriptions'])


@router.get("/plans", response_model=List[SSubscriptionPlanResponse])
async def get_subscription_plans():
    """
    Получить список всех доступных тарифных планов
    
    Возвращает все активные планы, отсортированные по длительности
    """
    try:
        plans = await SubscriptionPlanDAO.find_all(is_active=True)
        
        # Сортируем по длительности
        plans_sorted = sorted(plans, key=lambda x: x.duration_months)
        
        return plans_sorted
        
    except Exception as e:
        logger.error(f"Ошибка получения тарифных планов: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения тарифных планов"
        )


@router.post("/activate-trial", response_model=STrialActivation)
async def activate_trial(user: User = Depends(get_current_user)):
    """
    Активировать триальный период (2 недели)
    
    Доступно только один раз для каждого пользователя
    """
    try:
        if user.trial_used:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Триальный период уже использован"
            )
        
        result = await SubscriptionService.create_trial_subscription(user.id)
        
        return {
            "message": "Триальный период успешно активирован!",
            "subscription_uuid": result['subscription_uuid'],
            "expires_at": result['expires_at'],
            "is_trial": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка активации триала для пользователя {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка активации триального периода: {str(e)}"
        )


@router.post("/purchase", response_model=SPaymentResponse)
async def purchase_subscription(
    data: SPaymentInitiate,
    user: User = Depends(get_current_user)
):
    """
    Инициация покупки подписки - создание платёжной ссылки
    
    Создаёт платёжную ссылку в Точке и возвращает URL для оплаты.
    После оплаты пользователь будет перенаправлен на return_url.
    """
    try:
        result = await SubscriptionService.initiate_payment(
            user_id=user.id,
            plan_uuid=str(data.plan_uuid),
            return_url=data.return_url,
            payment_mode=data.payment_mode
        )
        
        logger.info(f"Платёжная ссылка создана для пользователя {user.id}: {result['payment_uuid']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Ошибка создания платежа для пользователя {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка создания платежа: {str(e)}"
        )


@router.get("/status", response_model=SSubscriptionStatus)
async def get_subscription_status(user: User = Depends(get_current_user)):
    """
    Получить статус подписки текущего пользователя
    
    Возвращает информацию о подписке, дате окончания и количестве оставшихся дней
    """
    try:
        # Определяем, триальная ли подписка
        is_trial = False
        if user.subscription_status.value == 'active' and user.subscription_until:
            # Проверяем, есть ли оплаченная подписка
            subscriptions = await SubscriptionDAO.find_all(
                user_id=user.id,
                is_trial=False
            )
            is_trial = len(subscriptions) == 0
        
        # Вычисляем количество дней до окончания
        days_remaining = None
        if user.subscription_until:
            delta = user.subscription_until - date.today()
            days_remaining = max(0, delta.days)
        
        return {
            "subscription_status": user.subscription_status.value,
            "subscription_until": user.subscription_until,
            "is_trial": is_trial,
            "trial_used": user.trial_used,
            "days_remaining": days_remaining
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения статуса подписки для пользователя {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения статуса подписки"
        )


@router.get("/payment/{payment_uuid}/status", response_model=SPaymentStatus)
async def check_payment_status(
    payment_uuid: str,
    user: User = Depends(get_current_user)
):
    """
    Проверить статус конкретного платежа
    
    Используется для проверки статуса после возврата из платёжной формы.
    Если статус в БД не финальный, делается запрос в Точку для обновления.
    """
    try:
        payment = await PaymentDAO.find_full_data(payment_uuid)
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Платеж не найден"
            )
        
        if payment.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ запрещён"
            )
        
        # Если статус уже финальный, возвращаем его
        if payment.status.value in ['succeeded', 'failed', 'cancelled', 'refunded']:
            logger.info(f"Возврат финального статуса платежа {payment_uuid}: {payment.status.value}")
            
            return {
                "status": payment.status.value,
                "amount": float(payment.amount),
                "created_at": payment.created_at,
                "paid_at": payment.paid_at,
                "receipt_url": payment.receipt_url
            }
        
        # Иначе проверяем актуальный статус в Точке
        logger.info(f"Проверка актуального статуса платежа {payment_uuid} в Точке")
        
        from app.payments.tochka_service import TochkaPaymentService
        
        tochka = TochkaPaymentService()
        # Используем operation_id (UUID операции от Точки), а не payment_id
        status_info = await tochka.get_payment_status(payment.operation_id)
        
        # Обновляем статус если изменился (статусы от Точки в верхнем регистре)
        # APPROVED или PAID означают успешную оплату
        if status_info['status'].upper() in ['PAID', 'APPROVED'] and payment.status.value != 'succeeded':
            logger.info(f"Платеж {payment_uuid} оплачен, активируем подписку")
            await SubscriptionService.process_successful_payment(payment_uuid)
            
            # Обновляем данные из БД
            payment = await PaymentDAO.find_full_data(payment_uuid)
        
        return {
            "status": payment.status.value,
            "amount": float(payment.amount),
            "created_at": payment.created_at,
            "paid_at": payment.paid_at,
            "receipt_url": payment.receipt_url or status_info.get('receipt_url')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка проверки статуса платежа {payment_uuid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка проверки статуса платежа"
        )


@router.post("/webhook")
async def payment_webhook(request: Request):
    """
    Вебхук для обработки уведомлений от Точки
    
    Точка отправляет JWT токен в теле запроса, который нужно расшифровать.
    Документация: https://developers.tochka.com/docs/tochka-api/opisanie-metodov/vebhuki
    
    **Важно:** 
    - Этот endpoint должен быть доступен извне (не localhost)
    - Для разработки используйте ngrok
    - Вебхук для события `acquiringInternetPayment`
    """
    try:
        # Получаем тело запроса как текст (JWT токен)
        jwt_token = (await request.body()).decode('utf-8')
        
        logger.info(f"=== Получен вебхук от Точки ===")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"JWT Token (первые 100 символов): {jwt_token[:100]}...")
        
        # Расшифровываем и проверяем JWT
        from app.payments.webhook_validator import decode_webhook_jwt
        
        try:
            webhook_data = decode_webhook_jwt(jwt_token)
            logger.info(f"Расшифрованные данные вебхука: {webhook_data}")
        except Exception as e:
            logger.error(f"Ошибка расшифровки JWT вебхука: {e}")
            # Невалидный вебхук - возвращаем 400
            return {"status": "error", "message": "Invalid JWT signature"}
        
        # Обрабатываем расшифрованные данные
        await SubscriptionService.process_webhook(webhook_data)
        
        logger.info(f"=== Вебхук успешно обработан ===")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}", exc_info=True)
        # Возвращаем 200, чтобы Точка не повторяла запрос
        return {"status": "error", "message": str(e)}


@router.get("/history")
async def get_payment_history(user: User = Depends(get_current_user)):
    """
    Получить историю платежей пользователя
    
    Возвращает список всех платежей с их статусами
    """
    try:
        payments = await PaymentDAO.find_all(user_id=user.id)
        
        # Сортируем по дате создания (новые первыми)
        payments_sorted = sorted(payments, key=lambda x: x.created_at, reverse=True)
        
        result = []
        for payment in payments_sorted:
            # Получаем информацию о плане
            from app.subscriptions.dao import SubscriptionPlanDAO
            plan = await SubscriptionPlanDAO.find_one_or_none_by_id(payment.plan_id)
            
            result.append({
                "uuid": str(payment.uuid),
                "amount": float(payment.amount),
                "status": payment.status.value,
                "plan_name": plan.name if plan else "Неизвестный план",
                "created_at": payment.created_at.isoformat(),
                "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
                "receipt_url": payment.receipt_url
            })
        
        return {"payments": result}
        
    except Exception as e:
        logger.error(f"Ошибка получения истории платежей для пользователя {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка получения истории платежей"
        )
