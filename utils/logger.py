# -*- coding: utf-8 -*-

#  Copyright 2019 Giacomo Ferretti
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler

from telegram.ext import run_async


class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in [logging.DEBUG, logging.INFO]


def init():
    global __logger__

    __log_folder = 'logs'
    __app_log_file = 'app.log'
    __error_log_file = 'error.log'
    __log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if not os.path.isdir(__log_folder):
        os.makedirs(__log_folder)

    __log_formatter = logging.Formatter(__log_format)
    __root_logger = logging.getLogger()
    __root_logger.setLevel(level=logging.INFO)

    __app_file_handler = TimedRotatingFileHandler(os.path.join(__log_folder, __app_log_file), when='midnight',
                                                  interval=1)
    __app_file_handler.setLevel(level=logging.DEBUG)
    __app_file_handler.suffix = '%Y%m%d'
    __app_file_handler.setFormatter(__log_formatter)
    __app_file_handler.addFilter(InfoFilter())
    __root_logger.addHandler(__app_file_handler)

    __error_file_handler = TimedRotatingFileHandler(os.path.join(__log_folder, __error_log_file), when='midnight',
                                                    interval=1)
    __error_file_handler.setLevel(level=logging.WARNING)
    __error_file_handler.suffix = '%Y%m%d'
    __error_file_handler.setFormatter(__log_formatter)
    __root_logger.addHandler(__error_file_handler)

    __console_out_handler = logging.StreamHandler(sys.stdout)
    __console_out_handler.setLevel(level=logging.DEBUG)
    __console_out_handler.setFormatter(__log_formatter)
    __console_out_handler.addFilter(InfoFilter())
    __root_logger.addHandler(__console_out_handler)

    __console_err_handler = logging.StreamHandler(sys.stderr)
    __console_err_handler.setLevel(level=logging.WARNING)
    __console_err_handler.setFormatter(__log_formatter)
    __root_logger.addHandler(__console_err_handler)

    __logger__ = logging.getLogger(__name__)


@run_async
def log_message(update, context):
    __logger__.info('[{}] {}: {}'.format(update.effective_user['id'], update.effective_user['first_name'],
                                         update.message.text))


@run_async
def log_callback(update, context):
    __logger__.info('[{}] {} => {}'.format(update.callback_query['message']['chat']['id'],
                                           update.callback_query['message']['chat']['first_name'],
                                           update.callback_query.data))
