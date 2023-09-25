# Homework Bot

Homework Bot - это Telegram-бот, предназначенный для отслеживания статуса проверки домашних заданий на Яндекс.Практикум. Он отправляет уведомления, когда статус изменяется: когда задание отправлено на проверку, есть замечания или задание зачтено.

## Технологии:

- Python 3.9
- python-dotenv
- python-telegram-bot

## Как запустить проект:

1. Склонируйте репозиторий и перейдите в него в командной строке:

```bash
   git clone https://github.com/VlKazmin/homework_bot.git
   cd homework_bot
```

2. Создайте и активируйте виртуальное окружение:
```bash
    python3 -m venv env
    source env/bin/activate
```
3. Установите зависимости из файла requirements.txt:
```bash
    Copy code
    python3 -m pip install --upgrade pip
    pip install -r requirements.txt
```
4. Установите необходимые переменные окружения в файле .env:

* Токен профиля на Яндекс.Практикуме
* Токен Telegram-бота
* Ваш Telegram ID

5. Выполните миграции:

```bash
    python3 manage.py migrate
```
6. Запустите проект:
```bash
    python3 manage.py 
```
Это запустит ваш Homework Bot и позволит отслеживать и получать уведомления о статусе ваших домашних заданий 
на Яндекс.Практикум
