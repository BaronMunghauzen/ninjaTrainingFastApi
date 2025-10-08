from app.dao.base import BaseDAO
from app.subscriptions.models import Subscription, SubscriptionPlan, Payment


class SubscriptionDAO(BaseDAO):
    """DAO для работы с подписками"""
    model = Subscription


class SubscriptionPlanDAO(BaseDAO):
    """DAO для работы с тарифными планами"""
    model = SubscriptionPlan


class PaymentDAO(BaseDAO):
    """DAO для работы с платежами"""
    model = Payment
