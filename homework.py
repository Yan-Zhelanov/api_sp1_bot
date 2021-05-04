# import unittest
import logging
import os
import time
from logging.handlers import TimedRotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException
from telegram.error import TelegramError

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_API_URL = ('https://praktikum.yandex.ru/api/user_api/'
                     'homework_statuses/')
PRAKTIKUM_AUTHORIZATION_HEADER = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
LOG_FILE_NAME = 'bot.log'
ERROR_CODES = ['error', 'code']
STATUSES_AND_VERDICTS = {
    'reviewing': 'Работу "{homework_name}" ещё не проверили.',
    'rejected': ('У вас проверили работу "{homework_name}".\n'
                 'К сожалению в работе нашлись ошибки.'),
    'approved': ('У вас проверили работу "{homework_name}".\n'
                 'Ревьюеру всё понравилось, '
                 'можно приступать к следующему уроку.'),
}
UNEXPECTED_VALUE_STATUS = 'Неизвестное значение ключа "status": {status}!'
REQUEST_EXCEPTION = (
    'RequestException: {exception}.\n'
    'URL: {url}, '
    'headers: {headers}, '
    'params: {params}.'
)
JSON_EXCEPTION = 'Json вернул код ошибки: {error}'
ERROR = 'Бот столкнулся с ошибкой!\n{exception}'
SEND_EXCEPTION = 'Не удалось отправить сообщение: {error}'
BOT_RUN = 'Бот запущен!'
SEND_MESSAGE = ('Отправляю сообщение: "{message}", '
                'пользователю: {chat_id}.')


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    status = homework['status']
    if status in STATUSES_AND_VERDICTS:
        return STATUSES_AND_VERDICTS[status].format(
            homework_name=homework_name)
    else:
        raise ValueError(UNEXPECTED_VALUE_STATUS.format(status=status))


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            PRAKTIKUM_API_URL,
            headers=PRAKTIKUM_AUTHORIZATION_HEADER,
            params=params,
        )
    except RequestException as exception:
        raise RequestException(REQUEST_EXCEPTION.format(
            exception=exception,
            url=PRAKTIKUM_API_URL,
            headers=PRAKTIKUM_AUTHORIZATION_HEADER,
            params=params,
        ))
    json = response.json()
    for error_code in ERROR_CODES:
        if error_code in json:
            raise ValueError(JSON_EXCEPTION.format(error=json[error_code]))
    return json


def send_message(message, bot_client):
    logging.info(SEND_MESSAGE.format(message=message, chat_id=CHAT_ID))
    return bot_client.send_message(CHAT_ID, message)


def main():
    logging.debug(BOT_RUN)
    bot = telegram.Bot(TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot
                )
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(5)
        except Exception as exception:
            error = ERROR.format(exception=exception)
            logging.error(error)
            try:
                send_message(error, bot)
            except TelegramError as telegram_error:
                raise TelegramError(SEND_EXCEPTION.format(
                    error=telegram_error))
            time.sleep(5)


if __name__ == '__main__':
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    handler = TimedRotatingFileHandler(
        LOG_FILE_NAME,
        when='midnight',
        interval=1,
        encoding='utf-8',
    )
    handler.suffix = '%Y%m%d'
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    ))
    root_logger.addHandler(handler)
    main()
    # from unittest import TestCase, mock
    # ReqEx = requests.RequestException
    # JSON = {'homew1orks': 'wat'}

    # class TestReq(TestCase):
    #     @mock.patch('requests.get')
    #     def test_raised(self, rq_get):
    #         response = mock.Mock()
    #         response.json = mock.Mock(
    #             return_value=JSON
    #         )
    #         rq_get.return_value = response
    #         main()
    # unittest.main()
