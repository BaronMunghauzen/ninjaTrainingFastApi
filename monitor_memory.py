#!/usr/bin/env python3
"""
Скрипт для мониторинга использования памяти приложением
Помогает обнаружить утечки памяти

Использование:
    python monitor_memory.py --url http://localhost:8000 --interval 60
"""

import argparse
import requests
import time
import json
from datetime import datetime
from typing import Dict, List


def get_memory_stats(url: str) -> Dict:
    """Получает статистику памяти с сервера"""
    try:
        response = requests.get(f"{url}/health/memory", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка при получении данных: {e}")
        return None


def get_leak_detection(url: str) -> Dict:
    """Получает детальный анализ утечек памяти"""
    try:
        response = requests.get(f"{url}/health/memory/leak-detection", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка при получении анализа утечек: {e}")
        return None


def format_memory_mb(mb: float) -> str:
    """Форматирует MB в читаемый формат"""
    if mb >= 1024:
        return f"{mb/1024:.2f} GB"
    return f"{mb:.2f} MB"


def print_memory_report(data: Dict):
    """Выводит отчет об использовании памяти"""
    if not data or data.get("status") != "ok":
        print("❌ Не удалось получить данные")
        return
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*60}")
    print(f"📊 Отчет о памяти - {timestamp}")
    print(f"{'='*60}")
    
    # Память процесса
    proc_mem = data.get("process_memory", {})
    print(f"\n💻 Память процесса:")
    print(f"  RSS: {format_memory_mb(proc_mem.get('rss_mb', 0))}")
    print(f"  VMS: {format_memory_mb(proc_mem.get('vms_mb', 0))}")
    print(f"  Процент от системы: {proc_mem.get('percent', 0)}%")
    
    # Системная память
    sys_mem = data.get("system_memory", {})
    print(f"\n🖥️  Системная память:")
    print(f"  Всего: {format_memory_mb(sys_mem.get('total_mb', 0))}")
    print(f"  Использовано: {format_memory_mb(sys_mem.get('used_mb', 0))} ({sys_mem.get('percent', 0)}%)")
    print(f"  Доступно: {format_memory_mb(sys_mem.get('available_mb', 0))}")
    if sys_mem.get("warning"):
        print(f"  ⚠️  {sys_mem['warning']}")
    
    # Тренд
    trend = data.get("memory_trend", {})
    if trend.get("status") == "ok":
        print(f"\n📈 Тренд памяти:")
        print(f"  {trend.get('trend', 'N/A')}")
        print(f"  Изменение RSS: {trend.get('rss_change_mb', 0):+.2f} MB")
        print(f"  Измерений: {trend.get('measurements_count', 0)}")
    
    # Пул БД
    db_pool = data.get("db_pool", {})
    if "error" not in db_pool:
        print(f"\n🗄️  Пул соединений БД:")
        print(f"  Размер: {db_pool.get('size', 0)}")
        print(f"  Используется: {db_pool.get('checked_out', 0)}")
        print(f"  Свободно: {db_pool.get('checked_in', 0)}")
        print(f"  Overflow: {db_pool.get('overflow', 0)}")
    
    # Рекомендации
    recommendations = data.get("recommendations", [])
    if recommendations:
        print(f"\n💡 Рекомендации:")
        for rec in recommendations:
            print(f"  {rec}")


def print_leak_detection_report(data: Dict):
    """Выводит отчет об анализе утечек"""
    if not data or data.get("status") != "ok":
        print("❌ Не удалось получить данные анализа утечек")
        return
    
    print(f"\n{'='*60}")
    print(f"🔍 Детальный анализ утечек памяти")
    print(f"{'='*60}")
    
    current = data.get("current_memory", {})
    print(f"\n💻 Текущая память:")
    print(f"  RSS: {format_memory_mb(current.get('rss_mb', 0))}")
    print(f"  VMS: {format_memory_mb(current.get('vms_mb', 0))}")
    
    # Топ выделений памяти
    top_allocations = data.get("top_allocations", [])
    if top_allocations:
        print(f"\n📊 Топ мест выделения памяти:")
        for alloc in top_allocations[:5]:
            print(f"  {alloc['rank']}. {alloc['filename']}:{alloc['lineno']}")
            print(f"     Размер: {format_memory_mb(alloc['size_mb'])} ({alloc['count']} выделений)")
    
    # Топ типов объектов
    top_objects = data.get("top_object_types", [])
    if top_objects:
        print(f"\n📦 Топ типов объектов в памяти:")
        for obj in top_objects[:5]:
            print(f"  {obj['type']}: {obj['count']:,} объектов")
    
    # Рекомендации
    recommendations = data.get("recommendations", [])
    if recommendations:
        print(f"\n💡 Рекомендации:")
        for rec in recommendations:
            print(f"  {rec}")


def monitor_loop(url: str, interval: int, leak_detection: bool):
    """Основной цикл мониторинга"""
    print(f"🚀 Запуск мониторинга памяти")
    print(f"   URL: {url}")
    print(f"   Интервал: {interval} секунд")
    print(f"   Детальный анализ: {'Да' if leak_detection else 'Нет'}")
    print(f"\nНажмите Ctrl+C для остановки\n")
    
    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\n{'─'*60}")
            print(f"Итерация #{iteration}")
            print(f"{'─'*60}")
            
            # Получаем базовую статистику
            data = get_memory_stats(url)
            if data:
                print_memory_report(data)
            
            # Детальный анализ (каждые 5 итераций или по запросу)
            if leak_detection and (iteration % 5 == 0 or iteration == 1):
                print(f"\n{'─'*60}")
                leak_data = get_leak_detection(url)
                if leak_data:
                    print_leak_detection_report(leak_data)
            
            if iteration < float('inf'):  # Бесконечный цикл
                print(f"\n⏳ Ожидание {interval} секунд...")
                time.sleep(interval)
    
    except KeyboardInterrupt:
        print(f"\n\n✅ Мониторинг остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Мониторинг использования памяти приложением"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="URL приложения (по умолчанию: http://localhost:8000)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Интервал проверки в секундах (по умолчанию: 60)"
    )
    parser.add_argument(
        "--leak-detection",
        action="store_true",
        help="Включить детальный анализ утечек памяти"
    )
    
    args = parser.parse_args()
    
    monitor_loop(args.url, args.interval, args.leak_detection)


if __name__ == "__main__":
    main()


































