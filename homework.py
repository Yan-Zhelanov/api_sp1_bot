import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    status = homework['status']
    if status == 'reviewing':
        return f'Работу "{homework_name}" ещё не проверили!'
    if status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    homework_statuses = requests.get(
        'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'},
        params={'from_date': current_timestamp}
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info(f'Отправляю сообщение: "{message}", '
                 f'пользователю: {CHAT_ID}...')
    return bot_client.send_message(CHAT_ID, message)


def main():
    logging.debug('Бот запущен!')
    bot = telegram.Bot(TELEGRAM_TOKEN)
    current_timestamp = 0
    # current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot
                )
            # current_timestamp = new_homework.get('current_date',
            #                                      current_timestamp)
            time.sleep(300)
        except Exception as e:
            send_message(f'Бот столкнулся с ошибкой: {e}', bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
