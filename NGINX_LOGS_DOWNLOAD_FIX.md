# 🔧 Настройка Nginx для корректной работы скачивания логов

## Проблема

Если при скачивании файлов логов через API заголовок `Content-Disposition` не изменяется (файл все еще скачивается с расширением `.zip` вместо `.dat`), возможно, nginx переопределяет заголовки.

**ВАЖНО:** Если в заголовках ответа вы видите `etag` и `last-modified`, это означает, что nginx кэширует ответы или переопределяет заголовки. Нужно отключить кэширование для эндпоинтов `/logs/download`.

## Решение

### Вариант 1: Проверьте конфигурацию nginx

Убедитесь, что nginx не переопределяет заголовки `Content-Disposition`. В конфигурации nginx для вашего приложения должны быть следующие настройки:

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # ВАЖНО: Не переопределять заголовки Content-Disposition
    proxy_pass_header Content-Disposition;
    proxy_hide_header Content-Disposition;  # НЕ используйте это!
    
    # Разрешить передачу всех заголовков от бэкенда
    proxy_pass_request_headers on;
}
```

### Вариант 2: Явно разрешить передачу заголовка

Если проблема сохраняется, добавьте явное разрешение:

```nginx
location /logs/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Явно разрешаем передачу заголовка Content-Disposition
    proxy_pass_header Content-Disposition;
    proxy_pass_header Content-Type;
    proxy_pass_header X-Content-Type-Options;
}
```

### Вариант 3: Отключить кэширование и обработку заголовков для определенных путей

```nginx
location /logs/download {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Отключить кэширование
    proxy_cache off;
    proxy_buffering off;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    add_header Pragma "no-cache";
    add_header Expires "0";
    
    # Не обрабатывать заголовки - передавать как есть
    proxy_pass_request_headers on;
    proxy_ignore_headers "Set-Cookie";
    
    # Явно разрешить передачу заголовка Content-Disposition
    proxy_pass_header Content-Disposition;
    proxy_pass_header Content-Type;
}
```

## Проверка

После изменения конфигурации nginx:

1. Проверьте синтаксис:
   ```bash
   sudo nginx -t
   ```

2. Перезагрузите nginx:
   ```bash
   sudo systemctl reload nginx
   # или
   sudo service nginx reload
   ```

3. Проверьте заголовки ответа в браузере (F12 → Network → выберите запрос → Headers):
   - Должно быть: `content-disposition: attachment; filename="app_2026-01-02.log.dat"`
   - Не должно быть: `content-disposition: attachment; filename="app_2026-01-02.log.zip"`

## Если проблема сохраняется

1. **Убедитесь, что сервер перезапущен** после изменений в коде:
   ```bash
   # Если используете systemd
   sudo systemctl restart your-app-service
   
   # Если используете supervisor
   sudo supervisorctl restart your-app
   
   # Если запускаете вручную
   # Остановите процесс и запустите заново
   ```

2. **Проверьте логи nginx** на наличие ошибок:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. **Проверьте, что изменения применены на сервере**:
   ```bash
   # На сервере проверьте код
   grep -A 5 "_get_safe_headers" app/logs/router.py
   # Должно быть: elif filename.endswith('.zip'):
   #            download_filename = filename.replace('.zip', '.dat')
   ```

4. **Проверьте версию кода на сервере**:
   ```bash
   git log --oneline -5
   # Должен быть коммит: "Fix antivirus blocking for zip archives"
   ```

## Альтернативное решение

Если nginx продолжает переопределять заголовки, можно использовать прямой доступ к приложению (без nginx) для скачивания логов, или настроить отдельный эндпоинт, который возвращает файл через прямой поток без использования FileResponse.

