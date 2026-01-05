from typing import Dict, Any
from app.calorie_calculator.schemas import GoalEnum, GenderEnum, ActivityCoefficientEnum


class CalorieCalculatorService:
    """Сервис для расчета калорий и БЖУ"""
    
    # Проценты для БЖУ по целям
    WEIGHT_LOSS_MACROS = {
        "proteins_percent": 30,
        "fats_percent": 27.5,  # Среднее между 25 и 30
        "carbs_percent": 42.5  # Среднее между 40 и 45
    }
    
    MUSCLE_GAIN_MACROS = {
        "proteins_percent": 27.5,  # Среднее между 25 и 30
        "fats_percent": 22.5,  # Среднее между 20 и 25
        "carbs_percent": 50  # Среднее между 45 и 55
    }
    
    MAINTENANCE_MACROS = {
        "proteins_percent": 22.5,  # Среднее между 20 и 25
        "fats_percent": 27.5,  # Среднее между 25 и 30
        "carbs_percent": 50  # Среднее между 45 и 55
    }
    
    # Корректировки по целям
    WEIGHT_LOSS_ADJUSTMENT = -0.175  # Среднее между -15% и -20%
    MUSCLE_GAIN_ADJUSTMENT = 0.15  # Среднее между +10% и +20%
    
    # Калорийность макронутриентов (ккал на грамм)
    CALORIES_PER_PROTEIN = 4
    CALORIES_PER_FAT = 9
    CALORIES_PER_CARB = 4
    
    @classmethod
    def calculate_bmr(cls, gender: GenderEnum, weight: float, height: float, age: int) -> float:
        """
        Расчет базового метаболизма (BMR) по формуле Миффлина-Сан Жеора
        
        Для мужчин: 10×вес(кг)+6.25×рост(см)−5×возраст+5
        Для женщин: 10×вес(кг)+6.25×рост(см)−5×возраст−161
        """
        base_bmr = 10 * weight + 6.25 * height - 5 * age
        
        if gender == GenderEnum.male:
            bmr = base_bmr + 5
        else:  # female
            bmr = base_bmr - 161
        
        return round(bmr, 2)
    
    @classmethod
    def calculate_tdee(cls, bmr: float, activity_coefficient: ActivityCoefficientEnum) -> float:
        """
        Расчет суточной нормы калорий (TDEE) = BMR × коэффициент активности
        """
        coefficient = float(activity_coefficient.value)
        tdee = bmr * coefficient
        return round(tdee, 2)
    
    @classmethod
    def calculate_calories_for_goal(cls, tdee: float, goal: GoalEnum) -> float:
        """
        Расчет калорий с учетом цели
        
        - Похудение: TDEE - 15-20%
        - Набор мышц: TDEE + 10-20%
        - Поддержание: TDEE
        """
        if goal == GoalEnum.weight_loss:
            calories = tdee * (1 + cls.WEIGHT_LOSS_ADJUSTMENT)
        elif goal == GoalEnum.muscle_gain:
            calories = tdee * (1 + cls.MUSCLE_GAIN_ADJUSTMENT)
        else:  # maintenance
            calories = tdee
        
        return round(calories, 2)
    
    @classmethod
    def calculate_macros(cls, calories: float, goal: GoalEnum) -> Dict[str, float]:
        """
        Расчет БЖУ в граммах для заданного количества калорий и цели
        
        Returns:
            Словарь с ключами: calories, proteins, fats, carbs (все в граммах)
        """
        # Получаем проценты для цели
        if goal == GoalEnum.weight_loss:
            macros_percent = cls.WEIGHT_LOSS_MACROS
        elif goal == GoalEnum.muscle_gain:
            macros_percent = cls.MUSCLE_GAIN_MACROS
        else:  # maintenance
            macros_percent = cls.MAINTENANCE_MACROS
        
        # Рассчитываем калории на каждый макронутриент
        proteins_calories = calories * (macros_percent["proteins_percent"] / 100)
        fats_calories = calories * (macros_percent["fats_percent"] / 100)
        carbs_calories = calories * (macros_percent["carbs_percent"] / 100)
        
        # Рассчитываем граммы
        proteins_grams = round(proteins_calories / cls.CALORIES_PER_PROTEIN, 2)
        fats_grams = round(fats_calories / cls.CALORIES_PER_FAT, 2)
        carbs_grams = round(carbs_calories / cls.CALORIES_PER_CARB, 2)
        
        return {
            "calories": round(calories, 2),
            "proteins": proteins_grams,
            "fats": fats_grams,
            "carbs": carbs_grams
        }
    
    @classmethod
    def calculate_all(cls, gender: GenderEnum, weight: float, height: float, age: int,
                     activity_coefficient: ActivityCoefficientEnum, goal: GoalEnum) -> Dict[str, Any]:
        """
        Полный расчет всех показателей
        
        Returns:
            Словарь с результатами расчетов
        """
        # Базовые расчеты
        bmr = cls.calculate_bmr(gender, weight, height, age)
        tdee = cls.calculate_tdee(bmr, activity_coefficient)
        
        # Расчеты для разных целей
        calories_weight_loss = cls.calculate_calories_for_goal(tdee, GoalEnum.weight_loss)
        calories_gain = cls.calculate_calories_for_goal(tdee, GoalEnum.muscle_gain)
        calories_maintenance = cls.calculate_calories_for_goal(tdee, GoalEnum.maintenance)
        
        # Расчет БЖУ для каждой цели
        macros_weight_loss = cls.calculate_macros(calories_weight_loss, GoalEnum.weight_loss)
        macros_gain = cls.calculate_macros(calories_gain, GoalEnum.muscle_gain)
        macros_maintenance = cls.calculate_macros(calories_maintenance, GoalEnum.maintenance)
        
        return {
            "bmr": bmr,
            "tdee": tdee,
            "calories_for_weight_loss": macros_weight_loss,
            "calories_for_gain": macros_gain,
            "calories_for_maintenance": macros_maintenance
        }

