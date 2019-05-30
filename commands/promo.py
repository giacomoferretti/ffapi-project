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

from mcdapi import promo
from telegram import Update, ParseMode
from telegram.ext import CallbackContext

from commands import base
from utils import templates


class PromoCommand(base.Command):
    name = 'promo'

    def handler(self, update: Update, context: CallbackContext):
        if self.can_run(update, context):
            body = templates.get_template('promo.md').format(promo.generate_random_promocode())
            context.bot.send_message(chat_id=update.effective_chat.id, text=body, parse_mode=ParseMode.MARKDOWN)
