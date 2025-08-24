"""
Скрипт для активации пользователя в системе
"""
import asyncio
import requests
from app.database import async_session_maker
from app.users.dao import UsersDAO
from app.email_verification.dao import EmailVerificationDAO
from sqlalchemy import text

BASE_URL = "http://localhost:8000"

async def activate_user_by_email(email: str):
    """Активировать пользователя по email (подтвердить email)"""
    async with async_session_maker() as session:
        # Найти пользователя по email
        user = await UsersDAO.find_one_or_none(email=email)
        if not user:
            print(f"❌ Пользователь с email {email} не найден")
            return False
        
        print(f"👤 Найден пользователь: {user.email}")
        print(f"📧 Email подтвержден: {user.email_verified}")
        print(f"📊 Статус подписки: {user.subscription_status}")
        
        if user.email_verified:
            print("✅ Email уже подтвержден")
            return True
        
        # Найти действующий токен подтверждения
        verification = await EmailVerificationDAO.find_by_user_id(user.id)
        if not verification:
            print("❌ Токен подтверждения не найден")
            return False
        
        print(f"🔑 Найден токен: {verification.token[:10]}...")
        
        # Подтвердить email через API
        try:
            response = requests.get(f"{BASE_URL}/auth/verify-email/", params={"token": verification.token})
            if response.status_code == 200:
                print("✅ Email успешно подтвержден!")
                return True
            else:
                print(f"❌ Ошибка подтверждения email: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            return False

async def activate_user_directly(email: str):
    """Прямая активация пользователя в базе данных"""
    async with async_session_maker() as session:
        # Найти пользователя по email
        user = await UsersDAO.find_one_or_none(email=email)
        if not user:
            print(f"❌ Пользователь с email {email} не найден")
            return False
        
        print(f"👤 Найден пользователь: {user.email}")
        print(f"📧 Email подтвержден: {user.email_verified}")
        
        if user.email_verified:
            print("✅ Email уже подтвержден")
            return True
        
        # Прямое обновление в базе данных
        await UsersDAO.update(user.uuid, email_verified=True)
        
        # Деактивировать все токены подтверждения
        await session.execute(
            text("UPDATE email_verification SET is_used = true WHERE user_id = :user_id"),
            {"user_id": user.id}
        )
        await session.commit()
        
        print("✅ Email подтвержден напрямую в базе данных!")
        return True

async def list_unverified_users():
    """Показать список неподтвержденных пользователей"""
    async with async_session_maker() as session:
        result = await session.execute(
            text("SELECT email, first_name, last_name, email_verified, subscription_status FROM \"user\" WHERE email_verified = false ORDER BY id DESC LIMIT 10")
        )
        users = result.fetchall()
        
        if not users:
            print("✅ Все пользователи подтверждены!")
            return
        
        print("\n📋 Неподтвержденные пользователи:")
        print("-" * 80)
        for i, user in enumerate(users, 1):
            name = f"{user[1] or ''} {user[2] or ''}".strip() or "Без имени"
            print(f"{i:2d}. {user[0]:30s} | {name:20s} | {user[4]}")

async def resend_verification_email(email: str):
    """Повторно отправить email подтверждения"""
    try:
        response = requests.post(f"{BASE_URL}/auth/resend-verification/", params={"email": email})
        if response.status_code == 200:
            print("✅ Email подтверждения отправлен повторно!")
            return True
        else:
            print(f"❌ Ошибка отправки email: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

async def main():
    print("🚀 Скрипт активации пользователя")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. Показать неподтвержденных пользователей")
        print("2. Активировать пользователя через API")
        print("3. Активировать пользователя напрямую в БД")
        print("4. Повторно отправить email подтверждения")
        print("0. Выход")
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == "0":
            print("👋 До свидания!")
            break
        elif choice == "1":
            await list_unverified_users()
        elif choice == "2":
            email = input("Введите email пользователя: ").strip()
            if email:
                await activate_user_by_email(email)
        elif choice == "3":
            email = input("Введите email пользователя: ").strip()
            if email:
                await activate_user_directly(email)
        elif choice == "4":
            email = input("Введите email пользователя: ").strip()
            if email:
                await resend_verification_email(email)
        else:
            print("❌ Неверный выбор!")

if __name__ == "__main__":
    asyncio.run(main())

