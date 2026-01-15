import httpx
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from app.logger import logger


class FoodRecognitionService:
    """Сервис для работы с внешним API распознавания еды"""
    
    BASE_URL = "http://185.125.201.189"
    ENDPOINT = "/recognize-food"
    AUTH_TOKEN = "secret"
    
    @classmethod
    async def recognize_food(
        cls,
        file_content: bytes,
        filename: str,
        content_type: str,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Отправляет запрос на распознавание еды по фото
        
        Args:
            file_content: Содержимое файла в байтах
            filename: Имя файла
            content_type: MIME-тип файла
            comment: Комментарий для уточнения (необязательный)
            
        Returns:
            Словарь с результатами распознавания
        """
        try:
            url = f"{cls.BASE_URL}{cls.ENDPOINT}"
            headers = {
                "Authorization": f"Bearer {cls.AUTH_TOKEN}"
            }
            
            # Подготовка данных для multipart/form-data
            files_data = {
                "file": (filename, file_content, content_type or "image/jpeg")
            }
            
            data = {}
            if comment:
                data["comment"] = comment
            
            logger.info(f"Отправка запроса на распознавание еды: {url}")
            logger.info(f"Файл: {filename}, размер: {len(file_content)}")
            logger.info(f"Комментарий: {comment}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    files=files_data,
                    data=data
                )
                
                logger.info(f"Ответ от сервиса: статус {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"Ошибка от сервиса: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Ошибка сервиса распознавания: {response.status_code}"
                    )
                
                result = response.json()
                logger.info(f"Результат распознавания: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                return result
                
        except httpx.TimeoutException:
            logger.error("Таймаут при запросе к сервису распознавания")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Превышено время ожидания ответа от сервиса распознавания"
            )
        except httpx.RequestError as e:
            logger.error(f"Ошибка при запросе к сервису: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Ошибка подключения к сервису распознавания: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка при распознавании: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка при распознавании: {str(e)}"
            )
    
    @classmethod
    def parse_response(cls, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Парсит ответ от сервиса и извлекает данные из recognized_foods[0]
        
        Args:
            response: Ответ от сервиса
            
        Returns:
            Словарь с распарсенными данными
        """
        parsed = {
            "json_response": json.dumps(response, ensure_ascii=False),
            "message": response.get("message"),
            "processing_time_seconds": response.get("processing_time_seconds")
        }
        
        recognized_foods = response.get("recognized_foods", [])
        if recognized_foods and len(recognized_foods) > 0:
            food = recognized_foods[0]
            
            # Основные данные
            parsed["name"] = food.get("name")
            parsed["confidence"] = food.get("confidence")
            
            # nutrition_per_100g
            nutrition = food.get("nutrition_per_100g", {})
            parsed["calories_per_100g"] = nutrition.get("calories")
            parsed["proteins_per_100g"] = nutrition.get("proteins")
            parsed["fats_per_100g"] = nutrition.get("fats")
            parsed["carbs_per_100g"] = nutrition.get("carbs")
            
            # portion_estimate
            portion = food.get("portion_estimate", {})
            parsed["weight_g"] = portion.get("weight_g")
            parsed["volume_ml"] = portion.get("volume_ml")
            parsed["estimated_portion_size"] = portion.get("estimated_portion_size")
            
            # total_nutrition
            total = food.get("total_nutrition", {})
            parsed["calories_total"] = total.get("calories")
            parsed["proteins_total"] = total.get("proteins")
            parsed["fats_total"] = total.get("fats")
            parsed["carbs_total"] = total.get("carbs")
            
            # ingredients (сохраняем полностью как JSON)
            ingredients = food.get("ingredients", [])
            parsed["ingredients"] = json.dumps(ingredients, ensure_ascii=False) if ingredients else None
            
            # recommendations (разделяем на tip и alternative)
            recommendations = food.get("recommendations", [])
            tips = [r for r in recommendations if r.get("type") == "tip"]
            alternatives = [r for r in recommendations if r.get("type") == "alternative"]
            parsed["recommendations_tip"] = json.dumps(tips, ensure_ascii=False) if tips else None
            parsed["recommendations_alternative"] = json.dumps(alternatives, ensure_ascii=False) if alternatives else None
            
            # micronutrients (сохраняем полностью как JSON)
            micronutrients = food.get("micronutrients", [])
            parsed["micronutrients"] = json.dumps(micronutrients, ensure_ascii=False) if micronutrients else None
        
        return parsed

