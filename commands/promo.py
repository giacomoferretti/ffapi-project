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

from mcdapi import promo
from telegram import Update, ParseMode
from telegram.ext import CallbackContext, run_async

from commands import base


class PromoCommand(base.Command):
    name = 'promo'

    @run_async
    def handler(self, update: Update, context: CallbackContext):
        if self.can_run(update, context):
            body = self.__config__.get_template('promo.html').format(promo.generate_random_promocode())
            context.bot.send_message(chat_id=update.effective_chat.id, text=body, parse_mode=ParseMode.HTML)

    @run_async
    def callback_handler(self, update: Update, context: CallbackContext):
        __logger__ = logging.getLogger(__name__)

        query = update.callback_query

        if self.check_callback(query.data, 'generate'):
            body = self.__config__.get_template('promo.html').format(promo.generate_random_promocode())
            context.bot.answer_callback_query(query.id, text='Promocode generato.')
            context.bot.send_message(chat_id=update.effective_chat.id, text=body, parse_mode=ParseMode.HTML)