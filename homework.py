"""
Это Бот-ассистент, который позволяет узнавать статус домашней работы.

Функция:
- отправляет сообщение в чат о статусе проверяемой работы

"""

import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Any, Dict, List, Optional

import requests
import telegram
from dotenv import load_dotenv
from exceptions import EndPointError, EndpointStatusError, SendMessageError

load_dotenv()

# Конфигурация корневого логгера: вывод DEBUG-сообщений в файл debug.log
logging.basicConfig(level=logging.DEBUG, filename="debug.log", filemode="w")

# Создание экземпляра логгера для текущего модуля
logger = logging.getLogger(__name__)

# Установка уровня логирования для логгера на INFO,
# т.е. он будет выводить сообщения с уровнем INFO и выше
logger.setLevel(logging.INFO)

# Создание обработчика (handler) для вывода сообщений в консоль
handler = logging.StreamHandler(stream=sys.stdout)

# Создание форматтера для задания формата сообщений
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Установка форматтера на обработчик
handler.setFormatter(formatter)

# Добавление обработчика в логгер
logger.addHandler(handler)


PRACTICUM_TOKEN: Optional[str] = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN: Optional[str] = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD: int = 600
ENDPOINT: str = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS: dict = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

HOMEWORK_VERDICTS: dict = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения.

    Проверяет, что обязательные переменные окружения PRACTICUM_TOKEN,
    TELEGRAM_TOKEN и TELEGRAM_CHAT_ID заполнены.

    """
    token_data = [
        ("PRACTICUM_TOKEN", PRACTICUM_TOKEN),
        ("TELEGRAM_TOKEN", TELEGRAM_TOKEN),
        ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID),
    ]
    tokens_filled = all(value is not None for _, value in token_data)

    if tokens_filled:
        return tokens_filled


def send_message(bot: telegram.Bot, message: str) -> None:
    """
    Отправляет сообщение в указанный чат в Telegram.

    Args:
        bot (telegram.Bot): Объект бота, который отправляет сообщение.
        TELEGRAM_CHAT_ID (str): Идентификатор чата,
                                куда будет отправлено сообщение.
        message (str): Сообщение, которое будет отправлено.

    Raises:
        SendMessageError: Если сообщение не удалось отправить.

    """
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f"Отправлено сообщение: {message}")
    except telegram.error.TelegramError as e:
        logging.error(
            f"Сообщение не удалось отправить: {message}. Причина: {e}"
        )
        raise SendMessageError(f"Не удалось отправить сообщение: {e}")


def get_api_answer(timestamp: int) -> Dict:
    """
    Получает ответ от API для указанного временного штампа.

    Args:
        timestamp (str): Временной штамп в формате ISO 8601.

    Raises:
        EndpointStatusError: Если эндпоинт недоступен или возвращает ошибку.
        KeyError: Если отсутствуют ожидаемые ключи.
        EndPointError: Если произошла ошибка доступа к эндпоинту.

    Returns:
        dict: Словарь, содержащий ответ от API в формате .json.

    """
    payload = {"from_date": timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
        if response.status_code != HTTPStatus.OK:
            message = (
                f"Не удалось получить ответ от {ENDPOINT} "
                f"с параметрами {payload.values()}. "
                f"Код запроса - {response.status_code}."
            )
            logger.error(message)
            raise EndpointStatusError(message)

        return response.json()

    except requests.RequestException as e:
        message = f"Ошибка выполнения запроса к {ENDPOINT}: {e}"
        logging.error(message, exc_info=True)
        raise EndPointError(message)

    except ConnectionError as e:
        message = (
            f"Не удалось установить соединение с {ENDPOINT}:"
            f" {e}. Проверьте интернет-соединение."
        )
        logger.error(message, exc_info=True)
        raise ConnectionError(message)


def check_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Проверяет корректность ответа от API.

    - проверяет, что полученный объект является словарем;
    - проверяет, что значение по ключу "homeworks" является списком словарей;
    - проверяет, что значение по ключу "current_date" является целым числом;
    - проверяет, что ключ "homeworks" в словаре не отсутствует;

    Args:
        response (dict): Принимает ответ от API в виде словаря.

    Raises:
        TypeError: Если полученный тип данных не соответствует ожидаемому.
        KeyError: Если отсутствуют ожидаемые ключи / появились лишние.

    Returns:
        List[Dict[str, Any]]: Если ответ корректный, то возвращает список
        словарей с данными по домашним заданиям.
    """
    if not isinstance(response, dict):
        logger.error(f"Ожидаемый тип данных - dict, получен {type(response)}.")
        raise TypeError("Тип данных не является словарем.")

    if "homeworks" not in response:
        logger.error("Ответ API не содержит ключа 'homeworks'")
        raise KeyError("Ответ API не содержит ключа 'homeworks'")

    homeworks = response["homeworks"]
    current_date = response["current_date"]

    if not isinstance(homeworks, list):
        logger.error(f"Ожидаемый тип данных - list, получен {type(response)}.")
        raise TypeError("Тип данных не является списком словарей.")

    elif not all(isinstance(item, dict) for item in homeworks):
        logger.error("Ожидаемый тип данных - list of dict.")
        raise TypeError("Тип данных не является списком словарей.")

    elif not isinstance(current_date, int):
        logger.error(f"Ожидаемый тип данных - int, получен {type(response)}.")
        raise TypeError("Тип данных не является целым числом.")

    return homeworks


def parse_status(homework: Dict[str, str]) -> str:
    """
    Возвращает статус проверяемой работы.

    Args:
        homework: Словарь, содержащий ключи "homework_name" и "status":
            - "homework_name" (str) - название работы,
            - "status" (str) - статус проверки работы.

    Returns:
        str: Сообщение о статусе проверки работы.

    Raises:
        KeyError: Если в словаре `homework` отсутствует ключ "homework_name"
        или "status", либо статус неизвестен.

    """
    required_keys = {"homework_name", "status"}
    if not required_keys.issubset(homework):
        missing_keys = required_keys - set(homework.keys())
        logger.error(f"Отсутствуют ключи {missing_keys} в словаре 'homework'")
        raise KeyError(
            f"Отсутствуют ключи {missing_keys} в словаре 'homework'"
        )

    homework_status = homework["status"]
    if homework_status not in HOMEWORK_VERDICTS:
        logger.error(f"Неизвестный статус - {homework_status}")
        raise KeyError(f"Неизвестный статус - {homework_status}")

    verdict = HOMEWORK_VERDICTS[homework_status]

    message = (
        f"Изменился статус проверки работы "
        f'"{homework["homework_name"]}". {verdict}'
    )
    logger.info(message)
    return message


def main():
    """Основная логика работы бота."""
    if check_tokens():
        logger.info("Переменные окружения заполнены.")
    else:
        logger.info("Отсутствуют обязательные переменные окружения.")
        logging.critical("Отсутствуют обязательные переменные окружения.")
        sys.exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_status = ""

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                homework_status = parse_status(homework[0])
                if homework_status != last_status:
                    send_message(bot, homework_status)
                    last_status = homework_status
            elif last_status == "":
                logger.info("Работ на проверке нет.")
                send_message(bot, "Работ на проверке нет.")

        except Exception as e:
            message = f"Сбой в работе программы: {e}"
            logger.error(message, exc_info=True)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
