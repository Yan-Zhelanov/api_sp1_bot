import logging
import os
import time

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
ERROR_CODES = ['error', 'code']
VERDICTS = {
    'reviewing': 'Работу "{homework_name}" ещё не проверили.',
    'rejected': 'У вас проверили работу "{homework_name}".\n'
                'К сожалению в работе нашлись ошибки.',
    'approved': 'У вас проверили работу "{homework_name}".\n'
                'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.',
}
UNEXPECTED_VALUE_STATUS = 'Неизвестное значение ключа "status": {status}!'
REQUEST_EXCEPTION = (
    'Не удалось обработать запрос.\n'
    'RequestException: {exception}.\n'
    'URL: {url}, '
    'headers: {headers}, '
    'params: {params}.'
)
API_EXCEPTION = (
    'Запрос к API вернул код ошибки: {error}.\n'
    'URL: {url}, '
    'headers: {headers}, '
    'params: {params}.'
)
ERROR = 'Бот столкнулся с ошибкой!\n{exception}'
SEND_EXCEPTION = 'Не удалось отправить сообщение: {error}'
BOT_RUN = 'Бот запущен!'
SEND_MESSAGE = ('Отправляю сообщение: "{message}", '
                'пользователю: {chat_id}.')


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in VERDICTS:
        raise ValueError(UNEXPECTED_VALUE_STATUS.format(status=status))
    return VERDICTS[status].format(homework_name=homework_name)


def get_homework_statuses(current_timestamp):
    request_parameters = dict(
        url=PRAKTIKUM_API_URL,
        headers=PRAKTIKUM_AUTHORIZATION_HEADER,
        params={'from_date': current_timestamp}
    )
    try:
        response = requests.get(**request_parameters)
    except RequestException as exception:
        raise ConnectionError(REQUEST_EXCEPTION.format(
            exception=exception,
            **request_parameters,
        ))
    homeworks = response.json()
    for error_code in ERROR_CODES:
        if error_code in homeworks:
            raise ValueError(API_EXCEPTION.format(
                error=homeworks[error_code],
                **request_parameters,
            ))
    return homeworks


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
            time.sleep(300)
        except Exception as exception:
            error = ERROR.format(exception=exception)
            logging.error(error)
            try:
                send_message(error, bot)
            except TelegramError as telegram_error:
                logging.error(SEND_EXCEPTION.format(error=telegram_error))
            time.sleep(5)


if __name__ == '__main__':
    LOG_FILE_NAME = __file__ + '.log'
    logging.basicConfig(
        filename=LOG_FILE_NAME,
        filemode='a',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        encoding='utf-8',
    )
    main()
    # import unittest
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
