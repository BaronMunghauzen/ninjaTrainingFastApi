import asyncio
from app.database import async_session_maker
from app.achievements.models import Achievement
from sqlalchemy import select

async def check_remaining():
    async with async_session_maker() as session:
        result = await session.execute(
            select(Achievement).where(Achievement.achievement_type_id.is_(None))
        )
        achievements = result.scalars().all()
        
        print("Достижения без типа:")
        for a in achievements:
            print(f"- {a.name}")

if __name__ == "__main__":
    asyncio.run(check_remaining())

