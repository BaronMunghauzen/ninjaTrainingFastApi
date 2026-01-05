"""
Сервис для автоматического создания программы питания

Логика подбора блюд:
1. Предфильтрация пулов блюд по категориям (завтрак, обед, ужин, супы)
2. Ограничения по разнообразию (не использовать одно блюдо более N раз в неделю на один прием)
3. Распределение КБЖУ по приемам пищи (завтрак ~25%, обед ~35%, ужин ~30%, перекусы ~10%)
4. Подбор блюд с учетом целевых КБЖУ (knapsack-подобный алгоритм)
5. Оптимизация для соблюдения пропорций макронутриентов
"""
from typing import List, Dict, Any, Optional, Tuple
import random
import json
from app.recipes.dao import RecipeDAO
from app.recipes.models import Recipe
from app.logger import logger


class MealPlanService:
    """Сервис для генерации программ питания"""
    
    # Распределение калорий по приемам пищи (в процентах от дневной нормы)
    # Основано на лучших практиках диетологии
    MEAL_DISTRIBUTION = {
        "breakfast": 0.25,    # Завтрак - 25%
        "lunch": 0.35,        # Обед - 35%
        "dinner": 0.30,       # Ужин - 30%
        "snack": 0.10         # Перекусы - 10%
    }
    
    # Категории приемов пищи
    MEAL_CATEGORIES = ["breakfast", "lunch", "dinner", "snack"]
    
    # Рекомендации для программы питания
    RECOMMENDATIONS = [
        "Пейте достаточное количество воды: 30-35 мл на 1 кг веса в день",
        "Распределяйте приемы пищи равномерно в течение дня",
        "Не пропускайте завтрак - это важный прием пищи для метаболизма",
        "Ужин должен быть легким и не позже чем за 2-3 часа до сна",
        "Включайте в рацион достаточное количество овощей и фруктов",
        "Следите за балансом белков, жиров и углеводов",
        "Адаптируйте программу под свои вкусовые предпочтения",
        "При необходимости корректируйте порции в зависимости от уровня активности"
    ]
    
    @classmethod
    async def generate_meal_plan(
        cls,
        user_id: int,
        meals_per_day: int,
        days_count: int,
        max_repeats_per_week: int,
        allowed_recipe_uuids: Optional[List[str]],
        target_calories: float,
        target_proteins: float,
        target_fats: float,
        target_carbs: float,
        include_soup_in_lunch: bool = True
    ) -> Dict[str, Any]:
        """
        Генерация программы питания
        
        Args:
            user_id: ID пользователя
            meals_per_day: Количество приемов пищи в день (минимум 3)
            days_count: Количество дней программы
            max_repeats_per_week: Максимальное количество повторов блюда в неделю на один прием
            allowed_recipe_uuids: Список разрешенных рецептов (None = все)
            target_calories: Целевой уровень калорий
            target_proteins: Целевой уровень белков
            target_fats: Целевой уровень жиров
            target_carbs: Целевой уровень углеводов
            
        Returns:
            Словарь с программой питания в формате:
            {
                "days": [
                    {
                        "day": 1,
                        "meals": [
                            {
                                "meal_type": "breakfast",
                                "recipes": [{"uuid": "...", "name": "...", "calories": ..., ...}],
                                "total_calories": ...,
                                ...
                            }
                        ]
                    }
                ]
            }
        """
        # Получаем доступные рецепты
        recipes = await cls._get_available_recipes(user_id, allowed_recipe_uuids)
        
        if not recipes:
            raise ValueError("Нет доступных рецептов для создания программы питания")
        
        # Разделяем рецепты по категориям
        recipes_by_category = cls._categorize_recipes(recipes)
        
        # Определяем типы приемов пищи
        meal_types = cls._determine_meal_types(meals_per_day)
        
        # Генерируем программу по дням
        plan_days = []
        dish_usage = {}  # Отслеживание использования блюд: {(recipe_uuid, meal_type): count}
        
        for day in range(1, days_count + 1):
            day_plan = {
                "day": day,
                "meals": []
            }
            
            # Отслеживание блюд, использованных в текущий день (для предотвращения повторов)
            day_dishes = set()
            
            for meal_type in meal_types:
                # Получаем пул кандидатов для этого приема пищи
                candidates = cls._get_meal_candidates(
                    recipes_by_category,
                    meal_type,
                    allowed_recipe_uuids
                )
                
                if not candidates:
                    logger.warning(f"Нет кандидатов для {meal_type} на день {day}")
                    continue
                
                # Рассчитываем целевые КБЖУ для приема пищи
                target_meal = cls._calculate_meal_targets(
                    meal_type,
                    target_calories,
                    target_proteins,
                    target_fats,
                    target_carbs,
                    meals_per_day
                )
                
                # Подбираем блюда для приема пищи
                selected_recipes = cls._select_recipes_for_meal(
                    candidates,
                    target_meal,
                    dish_usage,
                    meal_type,
                    day,
                    max_repeats_per_week,
                    day_dishes,  # Передаем список уже использованных в этот день блюд
                    include_soup_in_lunch  # Параметр для контроля добавления супа
                )
                
                # Добавляем выбранные блюда в список использованных за день
                for recipe in selected_recipes:
                    day_dishes.add(recipe["uuid"])
                
                # Рассчитываем фактические КБЖУ приема пищи
                meal_totals = cls._calculate_meal_totals(selected_recipes)
                
            day_plan["meals"].append({
                "meal_type": meal_type,
                "recipes": selected_recipes,
                "target_calories": target_meal["calories"],
                "target_proteins": target_meal["proteins"],
                "target_fats": target_meal["fats"],
                "target_carbs": target_meal["carbs"],
                "actual_calories": meal_totals["calories"],
                "actual_proteins": meal_totals["proteins"],
                "actual_fats": meal_totals["fats"],
                "actual_carbs": meal_totals["carbs"]
            })
            
            # Обновляем счетчик использования блюд
            for recipe in selected_recipes:
                key = (recipe["uuid"], meal_type)
                dish_usage[key] = dish_usage.get(key, 0) + 1
            
            # Post-оптимизация дня: проверяем отклонения
            cls._optimize_day_macros(
                day_plan,
                target_calories,
                target_proteins,
                target_fats,
                target_carbs
            )
            
            plan_days.append(day_plan)
        
        return {
            "days": plan_days
        }
    
    @classmethod
    async def _get_available_recipes(
        cls,
        user_id: int,
        allowed_recipe_uuids: Optional[List[str]]
    ) -> List[Recipe]:
        """Получить доступные рецепты (системные и пользовательские)"""
        # Получаем системные рецепты (user_id = None)
        system_recipes = await RecipeDAO.find_all(user_id=None, actual=True)
        
        # Получаем пользовательские рецепты
        user_recipes = await RecipeDAO.find_all(user_uuid=str(user_id), actual=True)
        
        all_recipes = list(system_recipes) + list(user_recipes)
        
        # Фильтруем по allowed_recipe_uuids если указаны
        if allowed_recipe_uuids:
            allowed_uuids = [str(uuid) for uuid in allowed_recipe_uuids]
            all_recipes = [
                r for r in all_recipes
                if str(r.uuid) in allowed_uuids
            ]
        
        return all_recipes
    
    @classmethod
    def _categorize_recipes(cls, recipes: List[Recipe]) -> Dict[str, List[Dict]]:
        """Разделить рецепты по категориям"""
        categorized = {
            "breakfast": [],
            "lunch": [],
            "dinner": [],
            "snack": [],
            "soup": [],
            "other": []
        }
        
        for recipe in recipes:
            recipe_dict = {
                "uuid": str(recipe.uuid),
                "name": recipe.name,
                "category": recipe.category or "other",
                "calories_per_portion": recipe.calories_per_portion or 0,
                "proteins_per_portion": recipe.proteins_per_portion or 0,
                "fats_per_portion": recipe.fats_per_portion or 0,
                "carbs_per_portion": recipe.carbs_per_portion or 0,
                "portions_count": recipe.portions_count or 1
            }
            
            category = (recipe.category or "other").lower()
            if category in categorized:
                categorized[category].append(recipe_dict)
            else:
                categorized["other"].append(recipe_dict)
        
        return categorized
    
    @classmethod
    def _determine_meal_types(cls, meals_per_day: int) -> List[str]:
        """Определить типы приемов пищи на основе их количества"""
        if meals_per_day == 3:
            return ["breakfast", "lunch", "dinner"]
        elif meals_per_day == 4:
            return ["breakfast", "lunch", "dinner", "snack"]
        elif meals_per_day == 5:
            return ["breakfast", "snack", "lunch", "snack", "dinner"]
        else:
            # Для большего количества приемов пищи
            result = ["breakfast"]
            for i in range(meals_per_day - 2):
                result.append("snack")
            result.append("dinner")
            return result
    
    @classmethod
    def _get_meal_candidates(
        cls,
        recipes_by_category: Dict[str, List[Dict]],
        meal_type: str,
        allowed_recipe_uuids: Optional[List[str]]
    ) -> List[Dict]:
        """Получить пул кандидатов для приема пищи"""
        candidates = []
        
        # Для завтрака берем блюда категории "breakfast"
        if meal_type == "breakfast":
            candidates.extend(recipes_by_category.get("breakfast", []))
        
        # Для обеда берем супы и блюда категории "lunch"
        elif meal_type == "lunch":
            candidates.extend(recipes_by_category.get("soup", []))
            candidates.extend(recipes_by_category.get("lunch", []))
        
        # Для ужина берем блюда категории "dinner"
        elif meal_type == "dinner":
            candidates.extend(recipes_by_category.get("dinner", []))
        
        # Для перекусов берем легкие блюда
        elif meal_type == "snack":
            candidates.extend(recipes_by_category.get("snack", []))
        
        # Если нет специфичных кандидатов, берем из "other"
        if not candidates:
            candidates.extend(recipes_by_category.get("other", []))
        
        # Убираем дубликаты по UUID
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate["uuid"] not in seen:
                seen.add(candidate["uuid"])
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    @classmethod
    def _calculate_meal_targets(
        cls,
        meal_type: str,
        target_calories: float,
        target_proteins: float,
        target_fats: float,
        target_carbs: float,
        meals_per_day: int
    ) -> Dict[str, float]:
        """Рассчитать целевые КБЖУ для приема пищи"""
        if meal_type in cls.MEAL_DISTRIBUTION:
            distribution = cls.MEAL_DISTRIBUTION[meal_type]
        else:
            # Для перекусов распределяем равномерно оставшиеся проценты
            distribution = (1.0 - sum(cls.MEAL_DISTRIBUTION.values())) / meals_per_day
        
        return {
            "calories": target_calories * distribution,
            "proteins": target_proteins * distribution,
            "fats": target_fats * distribution,
            "carbs": target_carbs * distribution
        }
    
    @classmethod
    def _select_recipes_for_meal(
        cls,
        candidates: List[Dict],
        target_meal: Dict[str, float],
        dish_usage: Dict[Tuple[str, str], int],
        meal_type: str,
        day: int,
        max_repeats_per_week: int,
        day_dishes: set,
        include_soup_in_lunch: bool = True
    ) -> List[Dict]:
        """
        Подобрать блюда для приема пищи
        
        Использует улучшенный алгоритм подбора с учетом:
        - Целевых КБЖУ (допуск ±15%)
        - Ограничений на повторы блюд в неделю
        - Запрета на повторение блюда в разные приемы одного дня (если есть альтернативы)
        - Weighted random для разнообразия
        - Подбор супа + второго для обеда
        """
        # Фильтруем кандидатов по ограничениям на повторы в неделю
        filtered_candidates = []
        for candidate in candidates:
            key = (candidate["uuid"], meal_type)
            current_week_count = dish_usage.get(key, 0)
            if current_week_count < max_repeats_per_week:
                filtered_candidates.append(candidate)
        
        if not filtered_candidates:
            # Если все блюда исчерпаны, используем всех кандидатов
            filtered_candidates = candidates
        
        # Исключаем блюда, уже использованные в этот день (если есть альтернативы)
        available_candidates = [
            c for c in filtered_candidates 
            if c["uuid"] not in day_dishes
        ]
        
        # Если после фильтрации не осталось альтернатив, используем все отфильтрованные
        if not available_candidates and len(filtered_candidates) > 0:
            available_candidates = filtered_candidates
        
        if not available_candidates:
            available_candidates = candidates
        
        tolerance = 0.15  # Допуск 15%
        
        # Для обеда: подбираем суп + второе (или только второе, в зависимости от параметра)
        if meal_type == "lunch":
            return cls._select_lunch_dishes(
                available_candidates,
                target_meal,
                tolerance,
                include_soup_in_lunch
            )
        
        # Для остальных приемов пищи: подбираем 1-2 блюда
        return cls._select_regular_meal_dishes(
            available_candidates,
            target_meal,
            tolerance
        )
    
    @classmethod
    def _select_lunch_dishes(
        cls,
        candidates: List[Dict],
        target_meal: Dict[str, float],
        tolerance: float,
        include_soup: bool = True
    ) -> List[Dict]:
        """
        Подобрать блюда для обеда
        
        Args:
            candidates: Список кандидатов блюд
            target_meal: Целевые КБЖУ для обеда
            tolerance: Допуск отклонения от цели
            include_soup: Включать ли суп в обед (True = суп + второе, False = только второе)
        """
        # Разделяем кандидатов на супы и вторые блюда
        soups = [c for c in candidates if (c.get("category", "").lower() == "soup" or 
                                          "суп" in c.get("name", "").lower())]
        main_dishes = [c for c in candidates if c not in soups]
        
        selected = []
        current_calories = 0
        current_proteins = 0
        current_fats = 0
        current_carbs = 0
        
        # Если нужно включить суп, пытаемся выбрать его
        if include_soup and soups:
            soup = cls._weighted_random_select(
                soups,
                target_meal["calories"] * 0.4,  # Суп должен быть ~40% от целевых калорий
                current_calories,
                target_meal["calories"] * tolerance
            )
            if soup:
                selected.append(soup)
                current_calories += soup["calories_per_portion"] or 0
                current_proteins += soup["proteins_per_portion"] or 0
                current_fats += soup["fats_per_portion"] or 0
                current_carbs += soup["carbs_per_portion"] or 0
        
        # Пытаемся добавить второе блюдо
        remaining_calories = target_meal["calories"] - current_calories
        if main_dishes and remaining_calories > target_meal["calories"] * 0.2:  # Минимум 20% должно остаться
            main_dish = cls._weighted_random_select(
                main_dishes,
                remaining_calories if include_soup else target_meal["calories"],  # Если супа нет, берем все калории на второе
                current_calories,
                target_meal["calories"] * tolerance
            )
            if main_dish:
                new_total = current_calories + (main_dish["calories_per_portion"] or 0)
                if new_total <= target_meal["calories"] * (1 + tolerance):
                    selected.append(main_dish)
        
        # Если ничего не выбрано, берем ближайшее блюдо (второе блюдо или любое доступное)
        if not selected:
            if main_dishes:
                selected.append(cls._weighted_random_select(main_dishes, target_meal["calories"], 0, tolerance))
            elif candidates:
                selected.append(cls._weighted_random_select(candidates, target_meal["calories"], 0, tolerance))
        
        return selected if selected else []
    
    @classmethod
    def _select_regular_meal_dishes(
        cls,
        candidates: List[Dict],
        target_meal: Dict[str, float],
        tolerance: float
    ) -> List[Dict]:
        """Подобрать блюда для обычного приема пищи (не обед)"""
        selected = []
        current_calories = 0
        
        # Используем weighted random для выбора основного блюда
        main_dish = cls._weighted_random_select(
            candidates,
            target_meal["calories"],
            current_calories,
            target_meal["calories"] * tolerance
        )
        
        if main_dish:
            selected.append(main_dish)
            current_calories += main_dish["calories_per_portion"] or 0
            
            # Если нужно добавить еще блюдо (например, для завтрака можно добавить фрукты)
            remaining = target_meal["calories"] - current_calories
            if remaining > target_meal["calories"] * 0.2:  # Если осталось >20%
                # Ищем легкое дополнительное блюдо
                remaining_candidates = [c for c in candidates if c["uuid"] != main_dish["uuid"]]
                additional = cls._weighted_random_select(
                    remaining_candidates,
                    remaining,
                    current_calories,
                    target_meal["calories"] * tolerance
                )
                if additional:
                    new_total = current_calories + (additional["calories_per_portion"] or 0)
                    if new_total <= target_meal["calories"] * (1 + tolerance):
                        selected.append(additional)
        
        # Если ничего не выбрано, берем ближайшее блюдо
        if not selected and candidates:
            selected.append(cls._weighted_random_select(candidates, target_meal["calories"], 0, tolerance))
        
        return selected if selected else []
    
    @classmethod
    def _weighted_random_select(
        cls,
        candidates: List[Dict],
        target_calories: float,
        current_calories: float,
        tolerance: float
    ) -> Optional[Dict]:
        """
        Weighted random выбор блюда с учетом близости к целевым калориям
        
        Блюда, более близкие к целевым калориям, имеют больший вес при выборе.
        Но добавляется случайность для разнообразия.
        """
        if not candidates:
            return None
        
        # Вычисляем "пригодность" каждого кандидата (score)
        scores = []
        for candidate in candidates:
            candidate_calories = candidate.get("calories_per_portion", 0) or 0
            if candidate_calories == 0:
                continue
            
            # Ожидаемые калории после добавления этого блюда
            expected_total = current_calories + candidate_calories
            
            # Вычисляем отклонение от цели
            deviation = abs(expected_total - target_calories)
            
            # Чем меньше отклонение, тем выше score (используем обратную зависимость)
            # Добавляем 1 чтобы избежать деления на 0
            score = 1.0 / (deviation + 1)
            
            # Бонус за блюда, которые не превышают цель
            if expected_total <= target_calories * (1 + tolerance):
                score *= 1.5
            
            scores.append((candidate, score))
        
        if not scores:
            return None
        
        # Сортируем по score и берем топ-N кандидатов для случайного выбора
        sorted_candidates = sorted(scores, key=lambda x: x[1], reverse=True)
        
        # Берем топ 30% или минимум 3 кандидата для случайного выбора
        top_count = max(3, len(sorted_candidates) // 3)
        top_candidates = sorted_candidates[:top_count]
        
        # Weighted random: чем выше score, тем больше вероятность
        total_score = sum(score for _, score in top_candidates)
        if total_score == 0:
            # Если все score = 0, выбираем случайно
            return random.choice([c for c, _ in top_candidates])
        
        # Генерируем случайное число и выбираем кандидата
        rand = random.uniform(0, total_score)
        cumulative = 0
        for candidate, score in top_candidates:
            cumulative += score
            if rand <= cumulative:
                return candidate
        
        # Fallback: возвращаем первый кандидат
        return top_candidates[0][0]
    
    @classmethod
    def _calculate_meal_totals(cls, recipes: List[Dict]) -> Dict[str, float]:
        """Рассчитать суммарные КБЖУ приема пищи"""
        totals = {
            "calories": 0,
            "proteins": 0,
            "fats": 0,
            "carbs": 0
        }
        
        for recipe in recipes:
            totals["calories"] += recipe.get("calories_per_portion", 0)
            totals["proteins"] += recipe.get("proteins_per_portion", 0)
            totals["fats"] += recipe.get("fats_per_portion", 0)
            totals["carbs"] += recipe.get("carbs_per_portion", 0)
        
        return totals
    
    @classmethod
    def _optimize_day_macros(
        cls,
        day_plan: Dict[str, Any],
        target_calories: float,
        target_proteins: float,
        target_fats: float,
        target_carbs: float
    ) -> None:
        """
        Post-оптимизация дня: если отклонения по КБЖУ слишком большие,
        пытаемся заменить одно блюдо на альтернативу
        
        Это soft-оптимизация для улучшения баланса макронутриентов
        """
        # Рассчитываем фактические КБЖУ за весь день
        day_totals = {"calories": 0, "proteins": 0, "fats": 0, "carbs": 0}
        for meal in day_plan["meals"]:
            day_totals["calories"] += meal.get("actual_calories", 0)
            day_totals["proteins"] += meal.get("actual_proteins", 0)
            day_totals["fats"] += meal.get("actual_fats", 0)
            day_totals["carbs"] += meal.get("actual_carbs", 0)
        
        # Проверяем отклонения
        tolerance = 0.15  # 15% допуск
        
        calories_deviation = abs(day_totals["calories"] - target_calories) / target_calories
        proteins_deviation = abs(day_totals["proteins"] - target_proteins) / target_proteins if target_proteins > 0 else 0
        fats_deviation = abs(day_totals["fats"] - target_fats) / target_fats if target_fats > 0 else 0
        carbs_deviation = abs(day_totals["carbs"] - target_carbs) / target_carbs if target_carbs > 0 else 0
        
        # Если отклонения в пределах допуска, оптимизация не нужна
        max_deviation = max(calories_deviation, proteins_deviation, fats_deviation, carbs_deviation)
        if max_deviation <= tolerance:
            return
        
        # Логируем отклонения для отладки (можно убрать в продакшене)
        logger.debug(
            f"День {day_plan['day']}: отклонения - "
            f"калории: {calories_deviation:.2%}, "
            f"белки: {proteins_deviation:.2%}, "
            f"жиры: {fats_deviation:.2%}, "
            f"углеводы: {carbs_deviation:.2%}"
        )
        
        # В будущем здесь можно добавить логику замены блюд для улучшения баланса
        # Например, если слишком много жиров - заменить одно жирное блюдо на менее жирное
        # Это требует более сложной логики с учетом всех ограничений

