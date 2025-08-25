"""
Демонстрация работы достижений "Ранняя пташка" и "Сова"
"""
import asyncio
from app.achievements.service import AchievementService
from app.achievements.dao import AchievementDAO
from app.user_training.dao import UserTrainingDAO
from app.users.dao import UsersDAO


async def demo_achievements():
    """Демонстрация проверки достижений"""
    
    print("🎯 Демонстрация системы достижений")
    print("=" * 50)
    
    # Пример UUID пользователя (замените на реальный)
    user_uuid = "example-user-uuid"
    
    try:
        print(f"🔍 Проверяем достижения для пользователя: {user_uuid}")
        
        # Проверяем достижение "Ранняя пташка"
        print("\n🌅 Проверяем достижение 'Ранняя пташка'...")
        early_bird = await AchievementService.check_early_bird_achievement(user_uuid)
        
        if early_bird:
            print("✅ Достижение 'Ранняя пташка' выдано!")
            print(f"   ID: {early_bird.id}")
            print(f"   Название: {early_bird.name}")
            print(f"   Статус: {early_bird.status}")
        else:
            print("❌ Условия для получения достижения 'Ранняя пташка' не выполнены")
            print("   Требуется: 5 завершенных тренировок с 5 до 8 утра")
        
        # Проверяем достижение "Сова"
        print("\n🦉 Проверяем достижение 'Сова'...")
        night_owl = await AchievementService.check_night_owl_achievement(user_uuid)
        
        if night_owl:
            print("✅ Достижение 'Сова' выдано!")
            print(f"   ID: {night_owl.id}")
            print(f"   Название: {night_owl.name}")
            print(f"   Статус: {night_owl.status}")
        else:
            print("❌ Условия для получения достижения 'Сова' не выполнены")
            print("   Требуется: 5 завершенных тренировок с 21 до 00")
        
        print("\n📊 Получаем все достижения пользователя...")
        user_achievements = await AchievementService.get_user_achievements(user_uuid)
        
        if user_achievements:
            print(f"   Найдено достижений: {len(user_achievements)}")
            for i, ach in enumerate(user_achievements, 1):
                print(f"   {i}. {ach.name} - {ach.status}")
        else:
            print("   У пользователя пока нет достижений")
        
        print("\n🔍 Проверяем все возможные достижения...")
        new_achievements = await AchievementService.check_all_achievements_for_user(user_uuid)
        
        if new_achievements:
            print(f"   Новых достижений: {len(new_achievements)}")
            for ach in new_achievements:
                print(f"   🎉 {ach.name}")
        else:
            print("   Новых достижений не найдено")
            
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Демонстрация завершена")


async def demo_achievement_conditions():
    """Демонстрация условий получения достижений"""
    
    print("\n📋 Условия получения достижений:")
    print("=" * 50)
    
    print("🌅 Достижение 'Ранняя пташка':")
    print("1. Пользователь должен завершить минимум 5 тренировок")
    print("2. Время завершения тренировок: с 5:00 до 8:00 утра")
    print("3. Статус тренировок должен быть 'completed'")
    print("4. Достижение выдается только один раз")
    
    print("\n🦉 Достижение 'Сова':")
    print("1. Пользователь должен завершить минимум 5 тренировок")
    print("2. Время завершения тренировок: с 21:00 до 00:00 (полночь)")
    print("3. Статус тренировок должен быть 'completed'")
    print("4. Достижение выдается только один раз")
    
    print("\n🔧 Техническая реализация:")
    print("- SQL запрос использует EXTRACT('hour', completed_at)")
    print("- 'Ранняя пташка': hour >= 5 AND hour < 8")
    print("- 'Сова': hour >= 21")
    print("- Сортировка по времени завершения")
    print("- Автоматическая проверка через AchievementService")


if __name__ == "__main__":
    print("🚀 Запуск демонстрации системы достижений")
    
    # Запускаем демонстрацию
    asyncio.run(demo_achievements())
    asyncio.run(demo_achievement_conditions())
    
    print("\n💡 Для тестирования API используйте:")
    print("   POST /achievements/check-early-bird/{user_uuid}")
    print("   POST /achievements/check-night-owl/{user_uuid}")
    print("   GET /achievements/user/{user_uuid}/achievements")
    print("   POST /achievements/check-all/{user_uuid}")
