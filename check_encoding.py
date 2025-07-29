#!/usr/bin/env python3
"""
Скрипт для проверки кодировки файлов в проекте
"""

import os
import chardet
from pathlib import Path

def check_file_encoding(file_path):
    """Проверяет кодировку файла"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            
        if not raw_data:
            return "empty"
            
        result = chardet.detect(raw_data)
        return result['encoding'], result['confidence']
    except Exception as e:
        return f"error: {str(e)}"

def scan_project():
    """Сканирует проект на предмет проблем с кодировкой"""
    project_root = Path(".")
    
    # Расширения файлов для проверки
    text_extensions = {'.py', '.txt', '.md', '.ini', '.yml', '.yaml', '.json'}
    
    print("🔍 Проверка кодировки файлов в проекте...")
    print("=" * 60)
    
    problematic_files = []
    
    for file_path in project_root.rglob("*"):
        if file_path.is_file() and file_path.suffix in text_extensions:
            # Пропускаем виртуальное окружение и git
            if any(part.startswith('.') for part in file_path.parts):
                continue
                
            encoding_info = check_file_encoding(file_path)
            
            if isinstance(encoding_info, tuple):
                encoding, confidence = encoding_info
                if encoding and encoding.lower() != 'utf-8':
                    print(f"⚠️  {file_path}: {encoding} (confidence: {confidence:.2f})")
                    problematic_files.append((file_path, encoding, confidence))
                elif not encoding:
                    print(f"❓ {file_path}: неопределенная кодировка")
                    problematic_files.append((file_path, "unknown", 0))
            else:
                print(f"❌ {file_path}: {encoding_info}")
                problematic_files.append((file_path, "error", 0))
    
    print("=" * 60)
    print(f"📊 Найдено проблемных файлов: {len(problematic_files)}")
    
    if problematic_files:
        print("\n🔧 Рекомендации:")
        print("1. Перекодируйте файлы в UTF-8")
        print("2. Проверьте настройки редактора")
        print("3. Убедитесь, что все файлы сохранены в UTF-8")
    else:
        print("✅ Все файлы имеют корректную кодировку UTF-8")

if __name__ == "__main__":
    scan_project() 