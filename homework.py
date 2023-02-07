import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (APIUnavailableError,
                        EnvVariableError,
                        MissingKeyError,
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


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
handler.setFormatter(formatter)


def check_tokens() -> None:
    """Проверка наличия обязательных переменных окружения."""
    message = ('Отсутствует обязательная переменная окружения: {var}. '
               'Программа принудительно остановлена.')
    if PRACTICUM_TOKEN is None:
        raise EnvVariableError(message.format(var='PRACTICUM_TOKEN'))
    if TELEGRAM_TOKEN is None:
        raise EnvVariableError(message.format(var='TELEGRAM_TOKEN'))
    if TELEGRAM_CHAT_ID is None:
        raise EnvVariableError(message.format(var='TELEGRAM_CHAT_ID'))


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
        if response.status_code != 200:
            raise APIUnavailableError(
                f'Эндпоинт {ENDPOINT} недоступен. '
                f'Код ответа API: {response.status_code}'
            )
    except requests.RequestException as error:
        raise APIUnavailableError(f'Эндпоинт {ENDPOINT} недоступен. {error}')
    return response.json()


def check_response(response: dict) -> bool:
    """Проверка ответа API на соответствие документации."""
    if type(response) is not dict:
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
    if type(current_date) is not int:
        raise TypeError(
            'В ответе API значение ключа current_date '
            f'имеет некорректный тип {type(current_date)}. Ожидается: int'
        )
    if type(homeworks) is not list:
        raise TypeError(
            'В ответе API значение ключа homeworks '
            f'имеет некорректный тип {type(homeworks)}. Ожидается: list'
        )
    if not homeworks:
        logger.debug('Новый статус отсутствует')
        return False
    return True


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
            if check_response(response):
                homework = response.get('homeworks')[0]
                message = parse_status(homework)
                send_message(bot=bot, message=message)
                timestamp = response.get('current_date')
                last_error_message = ''
        except Exception as error:
            if type(error) is EnvVariableError:
                logger.critical(error)
                sys.exit()
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != last_error_message:
                send_message(bot=bot, message=message)
                last_error_message = message

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
