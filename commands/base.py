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

from telegram import Update
from telegram.ext import CallbackContext

from utils import config


class Command:
    name = ''
    admins_only = False
    groups_allowed = False
    bots_allowed = False

    def __init__(self, __config__: config.Config):
        self.__config__ = __config__

    def check_callback(self, query, command):
        return query == '{}_{}'.format(self.name, command)

    def can_run(self, update: Update, context: CallbackContext):
        if self.__config__.get_maintenance() and not self.__config__.is_admin(update.effective_user['id']):
            self.reply_maintenance(update, context)
            return False

        if self.admins_only and not self.__config__.is_admin(update.effective_user['id']):
            return False

        if not self.bots_allowed and update.effective_user['is_bot']:
            return False

        return True

    def reply_maintenance(self, update: Update, context: CallbackContext):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='\u26d4 Il bot è in manutenzione.\n'
                                      'Manutenzione iniziata {}'.format(self.__config__.get_maintenance_time()))
