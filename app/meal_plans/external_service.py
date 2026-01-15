import httpx
import json
from typing import List, Dict, Any
from fastapi import HTTPException, status
from app.logger import logger


class MealPlanExternalService:
    """Сервис для работы с внешним API генерации программ питания"""
    
    BASE_URL = "http://185.125.201.189"
    ENDPOINT = "/create-meal-plan"
    AUTH_TOKEN = "secret"
    
    @classmethod
    async def create_meal_plan(
        cls,
        meals_per_day: int,
        days_count: int,
        target_nutrition: Dict[str, float],
        allowed_recipes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Отправляет запрос на создание программы питания во внешний сервис
        
        Args:
            meals_per_day: Количество приемов пищи в день
            days_count: Количество дней программы
            target_nutrition: Словарь с целевыми КБЖУ (calories, proteins, fats, carbs)
            allowed_recipes: Список рецептов с информацией (uuid, name, category, calories, proteins, fats, carbs)
            
        Returns:
            Словарь с результатом генерации программы питания
        """
        try:
            url = f"{cls.BASE_URL}{cls.ENDPOINT}"
            headers = {
                "Authorization": f"Bearer {cls.AUTH_TOKEN}",
                "Content-Type": "application/json",
                "accept": "application/json"
            }
            
            payload = {
                "meals_per_day": meals_per_day,
                "days_count": days_count,
                "target_nutrition": target_nutrition,
                "allowed_recipes": allowed_recipes
            }
            
            logger.info(f"Отправка запроса на создание программы питания: {url}")
            logger.info(f"Параметры: meals_per_day={meals_per_day}, days_count={days_count}")
            logger.debug(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:  # Увеличенный таймаут для генерации
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload
                )
                
                logger.info(f"Ответ от сервиса: статус {response.status_code}")
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Ошибка от сервиса: {error_text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Ошибка сервиса генерации программ питания: {response.status_code}. {error_text}"
                    )
                
                result = response.json()
                logger.info(f"Результат генерации получен успешно")
                logger.debug(f"Результат: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                return result
                
        except httpx.TimeoutException:
            logger.error("Таймаут при запросе к сервису генерации программ питания")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Таймаут при запросе к сервису генерации программ питания"
            )
        except httpx.RequestError as e:
            logger.error(f"Ошибка при запросе к сервису генерации программ питания: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ошибка подключения к сервису генерации программ питания: {str(e)}"
            )
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON ответа от сервиса: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Некорректный ответ от сервиса генерации программ питания"
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка при запросе к сервису генерации программ питания: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка при запросе к сервису: {str(e)}"
            )













