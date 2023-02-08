import logging
import os
import sys
import time
from http import HTTPStatus
from json.decoder import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (APIUnavailableError,
                        EnvVariableError,
                        MissingKeyError,
                        NotJSONResponseError,
                        UnexpectedStatusError)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def init_logger() -> logging.Logger:
    """Инициализация логгера."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(handler)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    return logger


logger = init_logger()


def check_tokens() -> None:
    """Проверка наличия обязательных переменных окружения."""
    env_variables = {
        PRACTICUM_TOKEN: 'PRACTICUM_TOKEN',
        TELEGRAM_TOKEN: 'TELEGRAM_TOKEN',
        TELEGRAM_CHAT_ID: 'TELEGRAM_CHAT_ID',
    }
    for env_variable, env_variable_name in env_variables.items():
        if env_variable is None:
            raise EnvVariableError(
                'Отсутствует обязательная переменная окружения: '
                f'{env_variable_name}. Программа принудительно остановлена.'
            )


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в telegram."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug(f'Бот отправил сообщение {message}')
    except telegram.error.TelegramError as error:
        logger.error(f'Не удалось отправить сообщение по причине: {error}')


def get_api_answer(timestamp: int) -> dict:
    """Выполнение запроса к API."""
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except requests.RequestException as error:
        raise APIUnavailableError(f'Эндпоинт {ENDPOINT} недоступен. {error}')

    if response.status_code != HTTPStatus.OK:
        raise APIUnavailableError(
            f'Эндпоинт {ENDPOINT} недоступен. '
            f'Код ответа API: {response.status_code}'
        )
    try:
        return response.json()
    except JSONDecodeError:
        raise NotJSONResponseError(
            f'API {ENDPOINT} вернул ответ не в json формате.'
        )


def check_response(response: dict) -> None:
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError(
            'В ответе API структура данных не соответствует ожиданиям. '
            f'Получен тип {type(response)}. Ожидается: dict'
        )
    current_date = response.get('current_date')
    homeworks = response.get('homeworks')
    if current_date is None:
        raise MissingKeyError('В ответе API отсутствует ключ current_date')
    if homeworks is None:
        raise MissingKeyError('В ответе API отсутствует ключ homeworks')
    if not isinstance(current_date, int):
        raise TypeError(
            'В ответе API значение ключа current_date '
            f'имеет некорректный тип {type(current_date)}. Ожидается: int'
        )
    if not isinstance(homeworks, list):
        raise TypeError(
            'В ответе API значение ключа homeworks '
            f'имеет некорректный тип {type(homeworks)}. Ожидается: list'
        )


def parse_status(homework: dict) -> str:
    """Извлечение информации о статусе домашней работы."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if homework_name is None:
        raise MissingKeyError('В ответе API отсутствует ключ homework_name')
    if status is None:
        raise MissingKeyError('В ответе API отсутствует ключ status')
    try:
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        raise UnexpectedStatusError(
            f'Неожиданный статус домашней работы в ответе API: {status}'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_error_message = ''

    while True:
        try:
            check_tokens()
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response.get('homeworks')
            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
                send_message(bot=bot, message=message)
            else:
                logger.debug('Новый статус отсутствует')
            timestamp = response.get('current_date')
            last_error_message = ''
        except EnvVariableError as error:
            logger.critical(error)
            sys.exit()
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != last_error_message:
                send_message(bot=bot, message=message)
                last_error_message = message

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
