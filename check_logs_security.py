#!/usr/bin/env python3
"""
Скрипт для проверки файлов логов на безопасность
Проверяет файлы на наличие подозрительного содержимого, повреждения и вирусов
"""
import os
import zipfile
import re
from pathlib import Path
from typing import List, Dict

# Подозрительные паттерны, которые могут указывать на вредоносный код
SUSPICIOUS_PATTERNS = [
    r'eval\s*\(',
    r'exec\s*\(',
    r'__import__',
    r'base64\.b64decode',
    r'base64\.b64encode',
    r'pickle\.loads',
    r'pickle\.load',
    r'\.exe',
    r'\.bat',
    r'\.sh',
    r'\.ps1',
    r'powershell',
    r'cmd\.exe',
    r'/bin/sh',
    r'/bin/bash',
    r'<script',
    r'javascript:',
    r'onerror=',
    r'onload=',
    r'\.php\?',
    r'\.asp\?',
    r'\.jsp\?',
    r'union\s+select',
    r'drop\s+table',
    r'delete\s+from',
    r'insert\s+into',
    r'<iframe',
    r'<object',
    r'<embed',
]

def check_file_content(file_path: Path) -> Dict:
    """
    Проверяет содержимое файла на подозрительные паттерны
    """
    results = {
        'file': str(file_path),
        'size': file_path.stat().st_size,
        'suspicious_lines': [],
        'errors': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                for pattern in SUSPICIOUS_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        results['suspicious_lines'].append({
                            'line': line_num,
                            'pattern': pattern,
                            'content': line.strip()[:200]  # Первые 200 символов
                        })
    except Exception as e:
        results['errors'].append(f"Ошибка чтения файла: {e}")
    
    return results

def check_zip_file(file_path: Path) -> Dict:
    """
    Проверяет ZIP архив на целостность и подозрительное содержимое
    """
    results = {
        'file': str(file_path),
        'size': file_path.stat().st_size,
        'is_valid_zip': False,
        'files_in_archive': [],
        'suspicious_files': [],
        'errors': []
    }
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            results['is_valid_zip'] = True
            results['files_in_archive'] = zip_ref.namelist()
            
            # Проверяем имена файлов в архиве
            for filename in zip_ref.namelist():
                # Проверяем на подозрительные расширения
                suspicious_extensions = ['.exe', '.bat', '.sh', '.ps1', '.vbs', '.js', '.jar']
                if any(filename.lower().endswith(ext) for ext in suspicious_extensions):
                    results['suspicious_files'].append(filename)
                
                # Проверяем содержимое файлов в архиве
                try:
                    content = zip_ref.read(filename)
                    # Проверяем первые 1000 байт на подозрительные паттерны
                    content_str = content[:1000].decode('utf-8', errors='replace')
                    for pattern in SUSPICIOUS_PATTERNS:
                        if re.search(pattern, content_str, re.IGNORECASE):
                            results['suspicious_files'].append(f"{filename} (pattern: {pattern})")
                except Exception:
                    pass  # Игнорируем бинарные файлы
                    
    except zipfile.BadZipFile:
        results['errors'].append("Файл не является валидным ZIP архивом")
    except Exception as e:
        results['errors'].append(f"Ошибка проверки ZIP: {e}")
    
    return results

def main():
    """
    Основная функция проверки
    """
    logs_dir = Path("logs")
    
    if not logs_dir.exists():
        print(f"❌ Директория {logs_dir} не найдена")
        return
    
    print("🔍 Проверка файлов логов на безопасность...\n")
    
    log_files = []
    zip_files = []
    
    # Собираем все файлы
    for file_path in logs_dir.iterdir():
        if file_path.is_file():
            if file_path.suffix == '.log':
                log_files.append(file_path)
            elif file_path.suffix == '.zip':
                zip_files.append(file_path)
    
    print(f"Найдено {len(log_files)} файлов .log и {len(zip_files)} файлов .zip\n")
    
    # Проверяем .log файлы
    if log_files:
        print("=" * 80)
        print("ПРОВЕРКА .LOG ФАЙЛОВ")
        print("=" * 80)
        
        for file_path in sorted(log_files):
            print(f"\n📄 {file_path.name} ({file_path.stat().st_size} bytes)")
            results = check_file_content(file_path)
            
            if results['suspicious_lines']:
                print(f"  ⚠️  Найдено {len(results['suspicious_lines'])} подозрительных строк:")
                for item in results['suspicious_lines'][:5]:  # Показываем первые 5
                    print(f"    - Строка {item['line']}: паттерн '{item['pattern']}'")
                    print(f"      {item['content'][:100]}...")
            else:
                print("  ✅ Подозрительных паттернов не найдено")
            
            if results['errors']:
                print(f"  ❌ Ошибки: {', '.join(results['errors'])}")
    
    # Проверяем .zip файлы
    if zip_files:
        print("\n" + "=" * 80)
        print("ПРОВЕРКА .ZIP АРХИВОВ")
        print("=" * 80)
        
        for file_path in sorted(zip_files):
            print(f"\n📦 {file_path.name} ({file_path.stat().st_size} bytes)")
            results = check_zip_file(file_path)
            
            if not results['is_valid_zip']:
                print(f"  ❌ Файл поврежден или не является валидным ZIP архивом")
                if results['errors']:
                    print(f"     Ошибки: {', '.join(results['errors'])}")
            else:
                print(f"  ✅ Архив валиден")
                print(f"  📁 Файлов в архиве: {len(results['files_in_archive'])}")
                
                if results['suspicious_files']:
                    print(f"  ⚠️  Найдено {len(results['suspicious_files'])} подозрительных файлов:")
                    for item in results['suspicious_files'][:5]:  # Показываем первые 5
                        print(f"    - {item}")
                else:
                    print("  ✅ Подозрительных файлов не найдено")
    
    print("\n" + "=" * 80)
    print("✅ Проверка завершена")
    print("=" * 80)
    
    # Рекомендации
    print("\n💡 Рекомендации:")
    print("1. Если найдены подозрительные паттерны, проверьте логи вручную")
    print("2. Если ZIP архивы повреждены, возможно проблема в процессе архивации")
    print("3. Используйте антивирус для полной проверки файлов на сервере")
    print("4. Проверьте права доступа к директории logs/")

if __name__ == "__main__":
    main()



























