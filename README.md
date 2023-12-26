# Homework_bot
Бот-ассистент для отслеживания статуса отправленной на ревью домашней работы в Яндекс Практикум.
Опрашивает API сервиса и при обнаружении изменения статуса домашней работы отправляет соответствующее уведомление в Telegram.

### Стек технологий использованный в проекте:
- Python 3.9
- python-telegram-bot
### Локальный запуск бота.
- Зарегистрировать Telegram бота и получить токен для Bot API
- Клонировать репозиторий на свой компьютер
 ```
      git clone https://github.com/avpech/homework_bot.git
```
- Создать и активировать виртуальное окружение (python версии 3.9)
```bash
      py -3.9 -m venv venv
```
```bash
      source venv/Scripts/activate
```
- Установить зависимости из requirements.txt
```bash
      python -m pip install --upgrade pip
```
- Создать в директории проекта файл .env с переменными:  
```PRACTICUM_TOKEN=```<токен для доступа к API Практикум.Домашка>  
```TELEGRAM_TOKEN=```<токен для работы с Bot API Telegram>  
```TELEGRAM_CHAT_ID=```<id Telegram-аккаунта для отправки сообщений>  
- Запустить homework.py
```
      python homework.py
```

##### Об авторе
Артур Печенюк
- :white_check_mark: [avpech](https://github.com/avpech)
