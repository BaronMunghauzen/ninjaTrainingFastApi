"""
Сервис для автоматического создания программы питания

Новая логика (без указания количества приёмов пищи):
1. Обязательные приёмы пищи: breakfast, lunch, dinner (всегда создаются)
2. Опциональные приёмы пищи: snack1, snack2, snack3 (добавляются при необходимости)
3. Система автоматически определяет количество приёмов пищи на основе целевых КБЖУ
4. Максимум 6 приёмов пищи в день
5. Жёсткие правила категорий блюд
6. Роли блюд: MAIN (основное), SIDE (добавка), FILLER (добор калорий)
7. Batch cooking для breakfast, lunch, dinner (готовка на 2 дня)
"""
from typing import List, Dict, Any, Optional
import random
import json
from itertools import product
from app.recipes.dao import RecipeDAO
from app.recipes.models import Recipe
from app.logger import logger


class MealPlanService:
    """Сервис для генерации программ питания"""
    
    # Распределение КБЖУ по обязательным приёмам пищи (в процентах от дневной нормы)
    # Эти значения используются как начальные цели, затем корректируются
    MEAL_DISTRIBUTION = {
        "breakfast": 0.30,  # Завтрак - 30%
        "lunch": 0.35,      # Обед - 35%
        "dinner": 0.25      # Ужин - 25%
        # Остальные 10% идут на snack-приёмы
    }
    
    # Таблица допустимости категорий блюд для каждого приёма пищи
    # Ключ - приём пищи, значение - список разрешённых типов рецептов
    MEAL_TYPE_ALLOWED = {
        "breakfast": ["breakfast", "dessert"],  # breakfast, dessert(light)
        "lunch": ["main", "salad"],              # lunch, dinner + salad
        "dinner": ["main", "salad"],             # dinner + salad
        "snack": ["snack", "salad", "dessert"]   # snack, salad, dessert(light), soup(light)
    }
    
    # Таблица допустимости категорий (category) для каждого приёма пищи
    # Жёсткая валидация - category должен соответствовать meal_type
    MEAL_CATEGORY_ALLOWED = {
        "breakfast": ["завтрак", "breakfast", "десерт", "dessert"],
        "lunch": ["обед", "lunch", "ужин", "dinner", "салат", "salad"],
        "dinner": ["ужин", "dinner", "салат", "salad"],
        "snack": ["перекус", "snack", "салат", "salad", "десерт", "dessert", "завтрак", "breakfast"]
    }
    
    # Роли блюд
    ROLE_MAIN = "MAIN"      # Основное блюдо приёма пищи
    ROLE_SIDE = "SIDE"      # Добавка (салат, гарнир)
    ROLE_FILLER = "FILLER"  # Добор калорий (десерт, перекус)
    
    @classmethod
    async def generate_meal_plan(
        cls,
        user_id: int,
        days_count: int,
        allowed_recipe_uuids: Optional[List[str]],
        target_calories: float,
        target_proteins: float,
        target_fats: float,
        target_carbs: float
    ) -> Dict[str, Any]:
        """
        Генерация программы питания
        
        Args:
            user_id: ID пользователя
            days_count: Количество дней программы
            allowed_recipe_uuids: Список разрешенных рецептов (None = все)
            target_calories: Целевой уровень калорий
            target_proteins: Целевой уровень белков
            target_fats: Целевой уровень жиров
            target_carbs: Целевой уровень углеводов
            
        Returns:
            Словарь с программой питания
        """
        # Получаем доступные рецепты
        recipes = await cls._get_available_recipes(user_id, allowed_recipe_uuids)
        
        if not recipes:
            raise ValueError("Нет доступных рецептов для создания программы питания")
        
        # Преобразуем рецепты в словари
        recipes_dict = cls._recipes_to_dict(recipes)
        
        # Целевые КБЖУ для дня
        target_nutrition = {
            "calories": target_calories,
            "proteins": target_proteins,
            "fats": target_fats,
            "carbs": target_carbs
        }
        
        # Создаём структуру дней с учётом batch cooking
        # Breakfast, lunch, dinner готовятся на 2 дня
        days = [None] * days_count  # Инициализируем список дней
        
        # Обрабатываем дни парами для batch cooking
        for day_start in range(0, days_count, 2):
            day_end = min(day_start + 1, days_count - 1)
            
            # Создаём батчи для breakfast, lunch, dinner
            breakfast_batch = cls._build_meal_slot(
                meal_type="breakfast",
                recipes_dict=recipes_dict,
                slot_target=cls._calculate_slot_target(target_nutrition, "breakfast"),
                day_idx=day_start,
                days_count=days_count
            )
            
            lunch_batch = cls._build_meal_slot(
                meal_type="lunch",
                recipes_dict=recipes_dict,
                slot_target=cls._calculate_slot_target(target_nutrition, "lunch"),
                day_idx=day_start,
                days_count=days_count
            )
            
            dinner_batch = cls._build_meal_slot(
                meal_type="dinner",
                recipes_dict=recipes_dict,
                slot_target=cls._calculate_slot_target(target_nutrition, "dinner"),
                day_idx=day_start,
                days_count=days_count
            )
            
            # Создаём планы для обоих дней в батче
            for day_idx in [day_start, day_end]:
                if day_idx < days_count:
                    day_plan = cls._build_day_plan_with_batches(
                        day_idx=day_idx,
                        recipes_dict=recipes_dict,
                        target_nutrition=target_nutrition,
                        days_count=days_count,
                        breakfast_batch=breakfast_batch,
                        lunch_batch=lunch_batch,
                        dinner_batch=dinner_batch
                    )
                    days[day_idx] = day_plan
        
        return {
            "days": days
        }
    
    @classmethod
    def _build_day_plan_with_batches(
        cls,
        day_idx: int,
        recipes_dict: List[Dict[str, Any]],
        target_nutrition: Dict[str, float],
        days_count: int,
        breakfast_batch: Optional[List[Dict[str, Any]]],
        lunch_batch: Optional[List[Dict[str, Any]]],
        dinner_batch: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Построить план одного дня с использованием батчей для основных приёмов пищи
        """
        day_plan = {
            "day": day_idx + 1,
            "meals": [],
            "target_nutrition": target_nutrition.copy(),
            "actual_nutrition": {"calories": 0.0, "proteins": 0.0, "fats": 0.0, "carbs": 0.0}
        }
        
        # Используем батчи для основных приёмов пищи
        if breakfast_batch:
            day_plan["meals"].append({
                "meal_type": "breakfast",
                "recipes": breakfast_batch.copy(),
                "role": cls.ROLE_MAIN
            })
        else:
            # Если батч не предоставлен, создаём заново
            breakfast_meals = cls._build_meal_slot(
                meal_type="breakfast",
                recipes_dict=recipes_dict,
                slot_target=cls._calculate_slot_target(target_nutrition, "breakfast"),
                day_idx=day_idx,
                days_count=days_count
            )
            if breakfast_meals:
                day_plan["meals"].append({
                    "meal_type": "breakfast",
                    "recipes": breakfast_meals,
                    "role": cls.ROLE_MAIN
                })
        
        if lunch_batch:
            day_plan["meals"].append({
                "meal_type": "lunch",
                "recipes": lunch_batch.copy(),
                "role": cls.ROLE_MAIN
            })
        else:
            lunch_meals = cls._build_meal_slot(
                meal_type="lunch",
                recipes_dict=recipes_dict,
                slot_target=cls._calculate_slot_target(target_nutrition, "lunch"),
                day_idx=day_idx,
                days_count=days_count
            )
            if lunch_meals:
                day_plan["meals"].append({
                    "meal_type": "lunch",
                    "recipes": lunch_meals,
                    "role": cls.ROLE_MAIN
                })
        
        if dinner_batch:
            day_plan["meals"].append({
                "meal_type": "dinner",
                "recipes": dinner_batch.copy(),
                "role": cls.ROLE_MAIN
            })
        else:
            dinner_meals = cls._build_meal_slot(
                meal_type="dinner",
                recipes_dict=recipes_dict,
                slot_target=cls._calculate_slot_target(target_nutrition, "dinner"),
                day_idx=day_idx,
                days_count=days_count
            )
            if dinner_meals:
                day_plan["meals"].append({
                    "meal_type": "dinner",
                    "recipes": dinner_meals,
                    "role": cls.ROLE_MAIN
                })
        
        # Посчитываем текущие итоги дня
        current_totals = cls._calculate_day_totals(day_plan["meals"])
        
        # Решаем, нужны ли доп. приёмы пищи (snack)
        # Динамически добавляем snack пока есть дефицит
        snack_idx = 0
        max_snacks = 6 - len(day_plan["meals"])  # Максимум 6 приёмов в день
        
        while snack_idx < max_snacks:
            remaining_calories = target_nutrition["calories"] - current_totals["calories"]
            remaining_proteins = target_nutrition["proteins"] - current_totals["proteins"]
            remaining_fats = target_nutrition["fats"] - current_totals["fats"]
            remaining_carbs = target_nutrition["carbs"] - current_totals["carbs"]
            
            # Проверяем, нужно ли добавлять snack
            # Добавляем если: калории > 250 ИЛИ белки > 20
            if remaining_calories <= 250 and remaining_proteins <= 20:
                break
            
            # Определяем целевые КБЖУ для snack
            snack_target = {
                "calories": max(150, remaining_calories / (max_snacks - snack_idx)),
                "proteins": max(10, remaining_proteins / (max_snacks - snack_idx)),
                "fats": max(0, remaining_fats / (max_snacks - snack_idx)),
                "carbs": max(0, remaining_carbs / (max_snacks - snack_idx))
            }
            
            # Подбираем snack
            snack_meals = cls._build_meal_slot(
                meal_type="snack",
                recipes_dict=recipes_dict,
                slot_target=snack_target,
                day_idx=day_idx,
                days_count=days_count,
                is_snack=True
            )
            
            if snack_meals:
                day_plan["meals"].append({
                    "meal_type": f"snack{snack_idx + 1}",
                    "recipes": snack_meals,
                    "role": cls.ROLE_FILLER
                })
                
                # Пересчитываем итоги
                current_totals = cls._calculate_day_totals(day_plan["meals"])
                snack_idx += 1
            else:
                # Если не удалось подобрать snack, прекращаем
                break
        
        # Финальная коррекция порций для всего дня
        cls._final_day_correction(day_plan, target_nutrition)
        
        # Пересчитываем итоговые КБЖУ дня
        day_plan["actual_nutrition"] = cls._calculate_day_totals(day_plan["meals"])
        
        # Форматируем выходные данные
        formatted_meals = []
        snack_count_final = len([m for m in day_plan["meals"] if m.get("meal_type", "").startswith("snack")])
        
        for meal in day_plan["meals"]:
            meal_totals = cls._calculate_meal_totals(meal["recipes"])
            meal_target = cls._get_meal_target(meal["meal_type"], target_nutrition, snack_count_final)
            formatted_meals.append({
                "meal_type": meal["meal_type"],
                "recipes": meal["recipes"],
                "target_calories": meal_target.get("calories", 0),
                "target_proteins": meal_target.get("proteins", 0),
                "target_fats": meal_target.get("fats", 0),
                "target_carbs": meal_target.get("carbs", 0),
                "actual_calories": meal_totals["calories"],
                "actual_proteins": meal_totals["proteins"],
                "actual_fats": meal_totals["fats"],
                "actual_carbs": meal_totals["carbs"]
            })
        
        day_plan["meals"] = formatted_meals
        
        return day_plan
    
    @classmethod
    def _build_day_plan(
        cls,
        day_idx: int,
        recipes_dict: List[Dict[str, Any]],
        target_nutrition: Dict[str, float],
        days_count: int
    ) -> Dict[str, Any]:
        """
        Построить план одного дня
        
        Алгоритм:
        1. Создать обязательные приёмы пищи (breakfast, lunch, dinner)
        2. Подобрать ОСНОВНЫЕ блюда (MAIN)
        3. Добавить SIDE (салаты/гарниры) если нужно
        4. Посчитать текущие итоги дня
        5. Решить, нужны ли доп. приёмы пищи (snack)
        6. Подобрать snack-приёмы
        7. Финальная коррекция порций
        """
        day_plan = {
            "day": day_idx + 1,
            "meals": [],
            "target_nutrition": target_nutrition.copy(),
            "actual_nutrition": {"calories": 0.0, "proteins": 0.0, "fats": 0.0, "carbs": 0.0}
        }
        
        # Шаг 1: Создаём обязательные приёмы пищи
        # Breakfast
        breakfast_meals = cls._build_meal_slot(
            meal_type="breakfast",
            recipes_dict=recipes_dict,
            slot_target=cls._calculate_slot_target(target_nutrition, "breakfast"),
            day_idx=day_idx,
            days_count=days_count
        )
        
        # Lunch
        lunch_meals = cls._build_meal_slot(
            meal_type="lunch",
            recipes_dict=recipes_dict,
            slot_target=cls._calculate_slot_target(target_nutrition, "lunch"),
            day_idx=day_idx,
            days_count=days_count
        )
        
        # Dinner
        dinner_meals = cls._build_meal_slot(
            meal_type="dinner",
            recipes_dict=recipes_dict,
            slot_target=cls._calculate_slot_target(target_nutrition, "dinner"),
            day_idx=day_idx,
            days_count=days_count
        )
        
        # Добавляем обязательные приёмы в план дня
        if breakfast_meals:
            day_plan["meals"].append({
                "meal_type": "breakfast",
                "recipes": breakfast_meals,
                "role": cls.ROLE_MAIN
            })
        
        if lunch_meals:
            day_plan["meals"].append({
                "meal_type": "lunch",
                "recipes": lunch_meals,
                "role": cls.ROLE_MAIN
            })
        
        if dinner_meals:
            day_plan["meals"].append({
                "meal_type": "dinner",
                "recipes": dinner_meals,
                "role": cls.ROLE_MAIN
            })
        
        # Шаг 2-3: Добавляем SIDE к lunch и dinner если нужно
        # (уже учтено в _build_meal_slot)
        
        # Шаг 4: Посчитываем текущие итоги дня
        current_totals = cls._calculate_day_totals(day_plan["meals"])
        
        # Шаг 5: Решаем, нужны ли доп. приёмы пищи (snack)
        remaining_calories = target_nutrition["calories"] - current_totals["calories"]
        
        # Определяем количество snack-приёмов
        snack_count = cls._determine_snack_count(remaining_calories, len(day_plan["meals"]))
        
        # Шаг 6: Подбираем snack-приёмы
        if snack_count > 0:
            snack_target_per_meal = {
                "calories": remaining_calories / snack_count,
                "proteins": (target_nutrition["proteins"] - current_totals["proteins"]) / snack_count,
                "fats": (target_nutrition["fats"] - current_totals["fats"]) / snack_count,
                "carbs": (target_nutrition["carbs"] - current_totals["carbs"]) / snack_count
            }
            
            for snack_idx in range(snack_count):
                snack_meals = cls._build_meal_slot(
                    meal_type="snack",
                    recipes_dict=recipes_dict,
                    slot_target=snack_target_per_meal,
                    day_idx=day_idx,
                    days_count=days_count,
                    is_snack=True
                )
                
                if snack_meals:
                    day_plan["meals"].append({
                        "meal_type": f"snack{snack_idx + 1}",
                        "recipes": snack_meals,
                        "role": cls.ROLE_FILLER
                    })
        
        # Шаг 7: Финальная коррекция порций для всего дня
        cls._final_day_correction(day_plan, target_nutrition)
        
        # Пересчитываем итоговые КБЖУ дня
        day_plan["actual_nutrition"] = cls._calculate_day_totals(day_plan["meals"])
        
        # Форматируем выходные данные
        formatted_meals = []
        snack_count_final = len([m for m in day_plan["meals"] if m.get("meal_type", "").startswith("snack")])
        
        for meal in day_plan["meals"]:
            meal_totals = cls._calculate_meal_totals(meal["recipes"])
            meal_target = cls._get_meal_target(meal["meal_type"], target_nutrition, snack_count_final)
            formatted_meals.append({
                "meal_type": meal["meal_type"],
                "recipes": meal["recipes"],
                "target_calories": meal_target.get("calories", 0),
                "target_proteins": meal_target.get("proteins", 0),
                "target_fats": meal_target.get("fats", 0),
                "target_carbs": meal_target.get("carbs", 0),
                "actual_calories": meal_totals["calories"],
                "actual_proteins": meal_totals["proteins"],
                "actual_fats": meal_totals["fats"],
                "actual_carbs": meal_totals["carbs"]
            })
        
        day_plan["meals"] = formatted_meals
        
        return day_plan
    
    @classmethod
    def _get_meal_target(cls, meal_type: str, target_nutrition: Dict[str, float], snack_count: int) -> Dict[str, float]:
        """Получить целевые КБЖУ для приёма пищи"""
        if meal_type in ["breakfast", "lunch", "dinner"]:
            return cls._calculate_slot_target(target_nutrition, meal_type)
        elif meal_type.startswith("snack"):
            # Равномерно распределяем остаток на все snack-приёмы
            remaining = {
                "calories": target_nutrition["calories"] * 0.10,  # Примерно 10% на snack
                "proteins": target_nutrition["proteins"] * 0.10,
                "fats": target_nutrition["fats"] * 0.10,
                "carbs": target_nutrition["carbs"] * 0.10
            }
            if snack_count > 0:
                return {
                    "calories": remaining["calories"] / snack_count,
                    "proteins": remaining["proteins"] / snack_count,
                    "fats": remaining["fats"] / snack_count,
                    "carbs": remaining["carbs"] / snack_count
                }
        return {"calories": 0, "proteins": 0, "fats": 0, "carbs": 0}
    
    @classmethod
    def _determine_snack_count(
        cls,
        remaining_calories: float,
        remaining_proteins: float,
        current_meals_count: int
    ) -> int:
        """
        Определить количество snack-приёмов пищи
        
        Правила:
        - Добавляем snack если remaining_calories > 250 ИЛИ remaining_proteins > 20
        - < 150 ккал остаток И remaining_proteins < 10 → не добавляем
        - 150-350 ккал ИЛИ remaining_proteins 10-20 → 1 snack
        - 350-650 ккал ИЛИ remaining_proteins 20-40 → 2 snack
        - > 650 ккал ИЛИ remaining_proteins > 40 → 3 snack (но total_meals ≤ 6)
        """
        # Если дефицит по белкам значительный - добавляем snack
        if remaining_proteins > 20:
            if remaining_proteins > 40:
                snack_count = 3
            elif remaining_proteins > 20:
                snack_count = 2
            else:
                snack_count = 1
        # Если дефицит по калориям
        elif remaining_calories > 250:
            if remaining_calories < 350:
                snack_count = 1
            elif remaining_calories < 650:
                snack_count = 2
            else:
                snack_count = 3
        # Если небольшой дефицит
        elif remaining_calories > 150 or remaining_proteins > 10:
            snack_count = 1
        else:
            snack_count = 0
        
        # Максимум 6 приёмов пищи в день
        max_snacks = 6 - current_meals_count
        return min(snack_count, max_snacks)
    
    @classmethod
    def _build_meal_slot(
        cls,
        meal_type: str,
        recipes_dict: List[Dict[str, Any]],
        slot_target: Dict[str, float],
        day_idx: int,
        days_count: int,
        is_snack: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Построить один приём пищи
        
        Логика:
        1. Фильтруем рецепты по допустимым категориям
        2. Подбираем основное блюдо (MAIN)
        3. Опционально добавляем SIDE (салат/гарнир) если калорий не хватает
        4. Оптимизируем порции
        """
        # Фильтруем рецепты по допустимым категориям
        allowed_recipes = cls._filter_by_allowed_category(recipes_dict, meal_type)
        
        if not allowed_recipes:
            logger.warning(f"Нет доступных рецептов для {meal_type} после фильтрации")
            return []
        
        # Подбираем основное блюдо
        main_dish = cls._pick_main_dish(allowed_recipes, meal_type, slot_target)
        
        if not main_dish:
            logger.warning(f"Не удалось подобрать основное блюдо для {meal_type}")
            return []
        
        meals = [main_dish]
        
        # Проверяем, нужно ли добавить SIDE (салат/гарнир)
        current_totals = cls._calculate_totals(meals)
        
        if current_totals["calories"] < slot_target["calories"] * 0.9:
            # Пробуем добавить салат или гарнир
            side_dish = cls._pick_side_dish(allowed_recipes, meal_type, slot_target, meals)
            if side_dish:
                meals.append(side_dish)
        
        # Оптимизируем порции
        optimized_meals = cls._optimize_slot(meals, slot_target)
        
        return optimized_meals
    
    @classmethod
    def _pick_main_dish(
        cls,
        allowed_recipes: List[Dict[str, Any]],
        meal_type: str,
        slot_target: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """Подобрать основное блюдо (MAIN) с учётом категории"""
        # Для breakfast - ищем breakfast-тип
        if meal_type == "breakfast":
            main_candidates = [
                r for r in allowed_recipes
                if r.get("type") == "breakfast"
                and (not r.get("category") or r.get("category", "").lower() in ["завтрак", "breakfast"])
            ]
        # Для lunch - ищем main-тип, но категория должна быть "обед" или "ужин" (не только "ужин")
        elif meal_type == "lunch":
            main_candidates = [
                r for r in allowed_recipes
                if r.get("type") == "main"
                and (not r.get("category") or r.get("category", "").lower() in ["обед", "lunch", "ужин", "dinner"])
            ]
        # Для dinner - ищем main-тип, но категория должна быть "ужин" (не "обед")
        elif meal_type == "dinner":
            main_candidates = [
                r for r in allowed_recipes
                if r.get("type") == "main"
                and (not r.get("category") or r.get("category", "").lower() in ["ужин", "dinner"])
            ]
        # Для snack - любой подходящий тип
        else:
            main_candidates = allowed_recipes.copy()
        
        if not main_candidates:
            return None
        
        # Выбираем блюдо, наиболее близкое к целевым КБЖУ
        # Приоритет белкам для snack
        best_dish = None
        best_score = float('inf')
        
        for dish in main_candidates:
            # Оцениваем близость к целевым КБЖУ
            score = cls._evaluate_dish_fit(dish, slot_target)
            # Для snack приоритет белковым блюдам
            if meal_type == "snack" and dish.get("proteins_per_portion", 0) > 15:
                score *= 0.8  # Снижаем score для белковых блюд
            if score < best_score:
                best_score = score
                best_dish = dish
        
        if best_dish:
            return best_dish.copy()
        
        return None
    
    @classmethod
    def _pick_side_dish(
        cls,
        allowed_recipes: List[Dict[str, Any]],
        meal_type: str,
        slot_target: Dict[str, float],
        existing_meals: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Подобрать дополнительное блюдо (SIDE) - салат или гарнир"""
        # Исключаем уже использованные блюда
        used_uuids = {m.get("uuid") for m in existing_meals}
        available = [r for r in allowed_recipes if r.get("uuid") not in used_uuids]
        
        # Ищем салаты
        salad_candidates = [r for r in available if r.get("type") == "salad"]
        
        if not salad_candidates:
            return None
        
        # Выбираем салат, который лучше всего дополнит существующие блюда
        current_totals = cls._calculate_totals(existing_meals)
        remaining_target = {
            "calories": max(0, slot_target["calories"] - current_totals["calories"]),
            "proteins": max(0, slot_target["proteins"] - current_totals["proteins"]),
            "fats": max(0, slot_target["fats"] - current_totals["fats"]),
            "carbs": max(0, slot_target["carbs"] - current_totals["carbs"])
        }
        
        best_side = None
        best_score = float('inf')
        
        for side in salad_candidates:
            score = cls._evaluate_dish_fit(side, remaining_target)
            if score < best_score:
                best_score = score
                best_side = side
        
        if best_side:
            return best_side.copy()
        
        return None
    
    @classmethod
    def _evaluate_dish_fit(cls, dish: Dict[str, Any], target: Dict[str, float]) -> float:
        """Оценить, насколько блюдо подходит к целевым КБЖУ"""
        cal_diff = abs((dish.get("calories_per_portion", 0) or 0) - target["calories"]) * 1.0
        prot_diff = abs((dish.get("proteins_per_portion", 0) or 0) - target["proteins"]) * 1.5
        fat_diff = abs((dish.get("fats_per_portion", 0) or 0) - target["fats"]) * 1.2
        carb_diff = abs((dish.get("carbs_per_portion", 0) or 0) - target["carbs"]) * 1.0
        
        return cal_diff + prot_diff + fat_diff + carb_diff
    
    @classmethod
    def _final_day_correction(cls, day_plan: Dict[str, Any], target_nutrition: Dict[str, float]):
        """Финальная коррекция порций для всего дня"""
        current_totals = cls._calculate_day_totals(day_plan["meals"])
        
        # Если калорий больше чем нужно - уменьшаем порции fillers
        if current_totals["calories"] > target_nutrition["calories"] * 1.05:
            for meal in day_plan["meals"]:
                if meal.get("role") == cls.ROLE_FILLER:
                    for recipe in meal["recipes"]:
                        if recipe.get("portions", 1) > 1:
                            recipe["portions"] -= 1
                            # Пересчитываем и проверяем
                            new_totals = cls._calculate_day_totals(day_plan["meals"])
                            if new_totals["calories"] <= target_nutrition["calories"] * 1.05:
                                break
        
        # Если калорий меньше чем нужно - увеличиваем порции fillers или добавляем десерт
        elif current_totals["calories"] < target_nutrition["calories"] * 0.95:
            for meal in day_plan["meals"]:
                if meal.get("role") == cls.ROLE_FILLER:
                    for recipe in meal["recipes"]:
                        if recipe.get("portions", 1) < 5:
                            recipe["portions"] += 1
                            # Пересчитываем и проверяем
                            new_totals = cls._calculate_day_totals(day_plan["meals"])
                            if new_totals["calories"] >= target_nutrition["calories"] * 0.95:
                                break
    
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
        user_recipes = await RecipeDAO.find_all(user_id=user_id, actual=True)
        
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
    def _map_category_to_type(cls, category: str) -> str:
        """Маппинг категории на тип рецепта"""
        if not category:
            return "main"  # По умолчанию
        
        category_lower = category.lower()
        
        # Маппинг категорий на типы
        category_mapping = {
            "завтрак": "breakfast",
            "breakfast": "breakfast",
            "обед": "main",
            "lunch": "main",
            "ужин": "main",
            "dinner": "main",
            "суп": "main",
            "soup": "main",
            "салат": "salad",
            "salad": "salad",
            "десерт": "dessert",
            "dessert": "dessert",
            "перекус": "snack",
            "snack": "snack"
        }
        
        return category_mapping.get(category_lower, "main")
    
    @classmethod
    def _recipes_to_dict(cls, recipes: List[Recipe]) -> List[Dict[str, Any]]:
        """Преобразовать рецепты в словари"""
        result = []
        for recipe in recipes:
            # Определяем тип рецепта
            recipe_type = (recipe.type or "").lower().strip()
            
            # Если type пустой или не в списке разрешённых, используем category
            valid_types = ["breakfast", "main", "salad", "snack", "dessert"]
            if not recipe_type or recipe_type not in valid_types:
                recipe_type = cls._map_category_to_type(recipe.category or "")
            
            result.append({
                "uuid": str(recipe.uuid),
                "name": recipe.name or "",
                "type": recipe_type,
                "category": recipe.category or "",
                "calories_per_portion": recipe.calories_per_portion or 0.0,
                "proteins_per_portion": recipe.proteins_per_portion or 0.0,
                "fats_per_portion": recipe.fats_per_portion or 0.0,
                "carbs_per_portion": recipe.carbs_per_portion or 0.0,
                "portions": 1  # Начальное количество порций
            })
        return result
    
    @classmethod
    def _filter_by_allowed_category(
        cls,
        recipes: List[Dict[str, Any]],
        meal_type: str
    ) -> List[Dict[str, Any]]:
        """
        Фильтровать рецепты по допустимым категориям для приёма пищи
        
        Жёсткая валидация - проверяем И type И category
        """
        allowed_types = cls.MEAL_TYPE_ALLOWED.get(meal_type, [])
        allowed_categories = cls.MEAL_CATEGORY_ALLOWED.get(meal_type, [])
        
        if not allowed_types:
            logger.warning(f"Нет разрешённых типов для {meal_type}")
            return []
        
        filtered = []
        for recipe in recipes:
            recipe_type = recipe.get("type", "").lower().strip()
            recipe_category = (recipe.get("category", "") or "").lower().strip()
            
            # Проверяем type
            type_match = recipe_type in allowed_types
            
            # Проверяем category (если указан)
            category_match = True
            if recipe_category:
                # Для lunch разрешаем и "обед" и "ужин"
                if meal_type == "lunch":
                    category_match = recipe_category in allowed_categories
                # Для dinner - только "ужин", не "обед"
                elif meal_type == "dinner":
                    category_match = recipe_category in allowed_categories and recipe_category not in ["обед", "lunch"]
                # Для breakfast - только "завтрак"
                elif meal_type == "breakfast":
                    category_match = recipe_category in allowed_categories and recipe_category not in ["обед", "lunch", "ужин", "dinner"]
                else:
                    category_match = recipe_category in allowed_categories
            
            if type_match and category_match:
                filtered.append(recipe)
        
        if not filtered:
            logger.warning(
                f"Нет рецептов с подходящими типами/категориями для {meal_type}. "
                f"Разрешённые типы: {allowed_types}, категории: {allowed_categories}"
            )
        
        return filtered
    
    @classmethod
    def _calculate_slot_target(
        cls,
        target_nutrition: Dict[str, float],
        meal_type: str
    ) -> Dict[str, float]:
        """Рассчитать целевые КБЖУ для слота"""
        share = cls.MEAL_DISTRIBUTION.get(meal_type, 0.0)
        
        return {
            "calories": target_nutrition["calories"] * share,
            "proteins": target_nutrition["proteins"] * share,
            "fats": target_nutrition["fats"] * share,
            "carbs": target_nutrition["carbs"] * share
        }
    
    @classmethod
    def _optimize_slot(
        cls,
        meals: List[Dict[str, Any]],
        slot_target: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Оптимизировать один приём пищи с использованием macro-penalty
        
        Алгоритм:
        1. Начинаем с portions = 1 для всех блюд
        2. Итеративно оптимизируем порции, минимизируя macro-penalty
        3. Проверяем валидность слота (90-110% калории, 85-115% БЖУ)
        """
        if not meals:
            return []
        
        # Инициализируем portions = 1
        for meal in meals:
            meal["portions"] = 1
        
        # Оптимизируем порции итеративно
        max_iterations = 50
        best_config = None
        best_score = float('inf')
        
        for iteration in range(max_iterations):
            totals = cls._calculate_totals(meals)
            score = cls._calculate_macro_penalty(totals, slot_target)
            
            if score < best_score:
                best_score = score
                best_config = [(m["uuid"], m["portions"]) for m in meals]
            
            # Если слот валиден, можем остановиться
            if cls._is_slot_valid(totals, slot_target):
                break
            
            # Пытаемся улучшить, изменяя порции
            improved = False
            
            # Приоритет 1: Балансируем макросы
            if not cls._is_slot_valid(totals, slot_target):
                improved = cls._balance_macros_iterative(meals, slot_target)
            
            # Приоритет 2: Корректируем калории
            if not improved:
                if totals["calories"] < slot_target["calories"] * 0.90:
                    best_meal = cls._find_best_meal_to_increase(meals, slot_target, totals)
                    if best_meal and best_meal["portions"] < 5:
                        best_meal["portions"] += 1
                        improved = True
                
                elif totals["calories"] > slot_target["calories"] * 1.10:
                    best_meal = cls._find_best_meal_to_decrease(meals, slot_target, totals)
                    if best_meal and best_meal["portions"] > 1:
                        best_meal["portions"] -= 1
                        improved = True
            
            if not improved:
                break
        
        # Восстанавливаем лучшую конфигурацию, если нашли
        if best_config:
            for meal, (uuid, portions) in zip(meals, best_config):
                if meal["uuid"] == uuid:
                    meal["portions"] = portions
        
        # Формируем финальный список с правильной структурой
        result = []
        for meal in meals:
            result.append({
                "uuid": meal["uuid"],
                "name": meal["name"],
                "category": meal.get("category", ""),
                "calories": meal["calories_per_portion"] * meal["portions"],
                "proteins": meal["proteins_per_portion"] * meal["portions"],
                "fats": meal["fats_per_portion"] * meal["portions"],
                "carbs": meal["carbs_per_portion"] * meal["portions"],
                "portions": meal["portions"]
            })
        
        return result
    
    @classmethod
    def _find_best_meal_to_increase(
        cls,
        meals: List[Dict[str, Any]],
        slot_target: Dict[str, float],
        current_totals: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """Найти лучшее блюдо для увеличения порции"""
        best_meal = None
        best_delta_score = float('inf')
        current_score = cls._calculate_macro_penalty(current_totals, slot_target)
        
        for meal in meals:
            if meal["portions"] < 5:
                meal["portions"] += 1
                new_totals = cls._calculate_totals(meals)
                new_score = cls._calculate_macro_penalty(new_totals, slot_target)
                delta_score = new_score - current_score
                
                if delta_score < best_delta_score:
                    best_delta_score = delta_score
                    best_meal = meal
                
                meal["portions"] -= 1
        
        return best_meal
    
    @classmethod
    def _find_best_meal_to_decrease(
        cls,
        meals: List[Dict[str, Any]],
        slot_target: Dict[str, float],
        current_totals: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """Найти лучшее блюдо для уменьшения порции"""
        best_meal = None
        best_delta_score = float('inf')
        current_score = cls._calculate_macro_penalty(current_totals, slot_target)
        
        for meal in meals:
            if meal["portions"] > 1:
                meal["portions"] -= 1
                new_totals = cls._calculate_totals(meals)
                new_score = cls._calculate_macro_penalty(new_totals, slot_target)
                delta_score = new_score - current_score
                
                if delta_score < best_delta_score:
                    best_delta_score = delta_score
                    best_meal = meal
                
                meal["portions"] += 1
        
        return best_meal
    
    @classmethod
    def _calculate_macro_penalty(
        cls,
        actual: Dict[str, float],
        target: Dict[str, float]
    ) -> float:
        """
        Рассчитать macro-penalty score
        
        score = |cal_target - cal_actual| * 1.0 +
                |prot_target - prot_actual| * 1.5 +
                |fat_target - fat_actual| * 1.2 +
                |carb_target - carb_actual| * 1.0
        """
        cal_diff = abs(target["calories"] - actual["calories"]) * 1.0
        prot_diff = abs(target["proteins"] - actual["proteins"]) * 1.5
        fat_diff = abs(target["fats"] - actual["fats"]) * 1.2
        carb_diff = abs(target["carbs"] - actual["carbs"]) * 1.0
        
        return cal_diff + prot_diff + fat_diff + carb_diff
    
    @classmethod
    def _is_slot_valid(
        cls,
        actual: Dict[str, float],
        target: Dict[str, float]
    ) -> bool:
        """
        Проверить валидность слота
        
        Калории: 90-110% (более строго для breakfast)
        БЖУ: 85-115%
        """
        if target["calories"] == 0:
            return True
        
        cal_ratio = actual["calories"] / target["calories"]
        prot_ratio = actual["proteins"] / target["proteins"] if target["proteins"] > 0 else 1.0
        fat_ratio = actual["fats"] / target["fats"] if target["fats"] > 0 else 1.0
        carb_ratio = actual["carbs"] / target["carbs"] if target["carbs"] > 0 else 1.0
        
        # Для breakfast более строгие ограничения по калориям (95-105%)
        cal_min = 0.95 if target["calories"] < 700 else 0.90
        cal_max = 1.05 if target["calories"] < 700 else 1.10
        
        return (cal_min <= cal_ratio <= cal_max and
                0.85 <= prot_ratio <= 1.15 and
                0.85 <= fat_ratio <= 1.15 and
                0.85 <= carb_ratio <= 1.15)
    
    @classmethod
    def _balance_macros_iterative(
        cls,
        meals: List[Dict[str, Any]],
        slot_target: Dict[str, float]
    ) -> bool:
        """
        Итеративная балансировка макросов с приоритизацией
        
        Приоритет: белки → калории → углеводы → жиры
        
        Возвращает True, если было улучшение
        """
        totals = cls._calculate_totals(meals)
        current_score = cls._calculate_macro_penalty(totals, slot_target)
        
        # Проверяем отклонения для каждого макро с приоритетом
        macros_to_balance = []
        
        # Приоритет 1: Белки (самый важный)
        prot_ratio = totals["proteins"] / slot_target["proteins"] if slot_target["proteins"] > 0 else 0
        if prot_ratio < 0.85 or prot_ratio > 1.15:
            macros_to_balance.append(("proteins", "proteins_per_portion", prot_ratio < 0.85, 1))
        
        # Приоритет 2: Калории
        cal_ratio = totals["calories"] / slot_target["calories"] if slot_target["calories"] > 0 else 1.0
        if cal_ratio < 0.90 or cal_ratio > 1.10:
            macros_to_balance.append(("calories", "calories_per_portion", cal_ratio < 0.90, 2))
        
        # Приоритет 3: Углеводы
        carb_ratio = totals["carbs"] / slot_target["carbs"] if slot_target["carbs"] > 0 else 0
        if carb_ratio < 0.85 or carb_ratio > 1.15:
            macros_to_balance.append(("carbs", "carbs_per_portion", carb_ratio < 0.85, 3))
        
        # Приоритет 4: Жиры (последний)
        fat_ratio = totals["fats"] / slot_target["fats"] if slot_target["fats"] > 0 else 0
        if fat_ratio < 0.85 or fat_ratio > 1.15:
            macros_to_balance.append(("fats", "fats_per_portion", fat_ratio < 0.85, 4))
        
        # Сортируем по приоритету, затем по критичности отклонения
        macros_to_balance.sort(
            key=lambda x: (x[3], abs(1.0 - (totals[x[0]] / slot_target[x[0]] if slot_target[x[0]] > 0 else 0))),
            reverse=False
        )
        
        # Балансируем каждый макро по приоритету
        for macro_name, macro_key, need_increase, priority in macros_to_balance:
            if need_increase:
                # Нужно увеличить макро
                macro_rich = sorted(meals, key=lambda m: m.get(macro_key, 0), reverse=True)
                for meal in macro_rich:
                    if meal["portions"] < 5:
                        meal["portions"] += 1
                        new_totals = cls._calculate_totals(meals)
                        new_score = cls._calculate_macro_penalty(new_totals, slot_target)
                        if new_score < current_score:
                            return True
                        meal["portions"] -= 1
            else:
                # Нужно уменьшить макро
                macro_rich = sorted(meals, key=lambda m: m.get(macro_key, 0), reverse=True)
                for meal in macro_rich:
                    if meal["portions"] > 1:
                        meal["portions"] -= 1
                        new_totals = cls._calculate_totals(meals)
                        new_score = cls._calculate_macro_penalty(new_totals, slot_target)
                        if new_score < current_score:
                            return True
                        meal["portions"] += 1
        
        return False
    
    @classmethod
    def _calculate_totals(cls, meals: List[Dict[str, Any]]) -> Dict[str, float]:
        """Рассчитать суммарные КБЖУ"""
        totals = {
            "calories": 0.0,
            "proteins": 0.0,
            "fats": 0.0,
            "carbs": 0.0
        }
        
        for meal in meals:
            # Проверяем, какая структура данных (до или после оптимизации)
            if "calories" in meal:
                # После оптимизации - уже посчитано с учётом portions
                totals["calories"] += meal.get("calories", 0) or 0
                totals["proteins"] += meal.get("proteins", 0) or 0
                totals["fats"] += meal.get("fats", 0) or 0
                totals["carbs"] += meal.get("carbs", 0) or 0
            else:
                # До оптимизации - нужно умножить на portions
                portions = meal.get("portions", 1)
                totals["calories"] += (meal.get("calories_per_portion", 0) or 0) * portions
                totals["proteins"] += (meal.get("proteins_per_portion", 0) or 0) * portions
                totals["fats"] += (meal.get("fats_per_portion", 0) or 0) * portions
                totals["carbs"] += (meal.get("carbs_per_portion", 0) or 0) * portions
        
        return totals
    
    @classmethod
    def _calculate_day_totals(cls, meals: List[Dict[str, Any]]) -> Dict[str, float]:
        """Рассчитать суммарные КБЖУ за день"""
        totals = {
            "calories": 0.0,
            "proteins": 0.0,
            "fats": 0.0,
            "carbs": 0.0
        }
        
        for meal in meals:
            meal_totals = cls._calculate_meal_totals(meal.get("recipes", []))
            totals["calories"] += meal_totals["calories"]
            totals["proteins"] += meal_totals["proteins"]
            totals["fats"] += meal_totals["fats"]
            totals["carbs"] += meal_totals["carbs"]
        
        return totals
    
    @classmethod
    def _calculate_meal_totals(cls, recipes: List[Dict[str, Any]]) -> Dict[str, float]:
        """Рассчитать суммарные КБЖУ для одного приёма пищи"""
        totals = {
            "calories": 0.0,
            "proteins": 0.0,
            "fats": 0.0,
            "carbs": 0.0
        }
        
        for recipe in recipes:
            totals["calories"] += recipe.get("calories", 0) or 0
            totals["proteins"] += recipe.get("proteins", 0) or 0
            totals["fats"] += recipe.get("fats", 0) or 0
            totals["carbs"] += recipe.get("carbs", 0) or 0
        
        return totals
