"""
Скрипт для создания тарифных планов подписки
Запустите этот скрипт после применения миграций
"""

import asyncio
from app.database import async_session_maker
from app.subscriptions.models import SubscriptionPlan, SubscriptionPlanEnum


async def create_subscription_plans():
    """Создание тарифных планов"""
    
    plans = [
        {
            "plan_type": SubscriptionPlanEnum.month_1,
            "name": "1 месяц",
            "duration_months": 1,
            "price": 990.00,
            "price_per_month": 990.00,
            "description": "Подписка на 1 месяц"
        },
        {
            "plan_type": SubscriptionPlanEnum.month_3,
            "name": "3 месяца",
            "duration_months": 3,
            "price": 2490.00,
            "price_per_month": 830.00,
            "description": "Подписка на 3 месяца. Выгода 16%!"
        },
        {
            "plan_type": SubscriptionPlanEnum.month_6,
            "name": "6 месяцев",
            "duration_months": 6,
            "price": 4490.00,
            "price_per_month": 748.33,
            "description": "Подписка на 6 месяцев. Выгода 24%!"
        },
        {
            "plan_type": SubscriptionPlanEnum.month_12,
            "name": "12 месяцев",
            "duration_months": 12,
            "price": 7990.00,
            "price_per_month": 665.83,
            "description": "Подписка на 12 месяцев. Выгода 33%!"
        }
    ]
    
    async with async_session_maker() as session:
        for plan_data in plans:
            # Проверяем, существует ли уже такой план
            from sqlalchemy import select
            stmt = select(SubscriptionPlan).where(
                SubscriptionPlan.plan_type == plan_data["plan_type"]
            )
            result = await session.execute(stmt)
            existing_plan = result.scalar_one_or_none()
            
            if existing_plan:
                print(f"План '{plan_data['name']}' уже существует, пропускаем...")
                continue
            
            # Создаем новый план
            plan = SubscriptionPlan(**plan_data)
            session.add(plan)
            print(f"Создан план: {plan_data['name']} - {plan_data['price']} руб.")
        
        await session.commit()
        print("\n✅ Все тарифные планы успешно созданы!")


if __name__ == "__main__":
    print("Создание тарифных планов подписки...")
    asyncio.run(create_subscription_plans())
