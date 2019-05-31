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

from telegram import Update, ParseMode
from telegram.error import Unauthorized, BadRequest
from telegram.ext import CallbackContext, run_async

from commands import base

__broadcast_message__ = 'Reply to this message to send a broadcast'


class AdminManager(base.Command):
    name = 'admin'
    admins_only = True

    def __init__(self, __config__, __users__):
        super().__init__(__config__)
        self.__users__ = __users__

    @run_async
    def broadcast(self, update: Update, context: CallbackContext):
        if self.can_run(update, context):
            context.bot.send_message(chat_id=update.effective_chat.id, text=__broadcast_message__)

    @run_async
    def send_broadcast(self, update: Update, context: CallbackContext):
        if self.can_run(update, context):
            __logger__ = logging.getLogger(__name__)

            if update.to_dict()['message']['reply_to_message']['text'] == __broadcast_message__ and \
                    update.to_dict()['message']['reply_to_message']['from']['id'] == context.bot.id:
                body = self.__config__.get_template('broadcast.md').format(message=update.message.text,
                                                                           name=update.effective_user['username'],
                                                                           id=update.effective_user['id'])

                for user in list(self.__users__.get_users()):
                    try:
                        context.bot.send_message(chat_id=user, text=body, parse_mode=ParseMode.MARKDOWN)
                    except (Unauthorized, BadRequest):
                        __logger__.error('Cannot send message to {}. Removing it from list...'.format(user))
                        self.__users__.remove_user(user)

                context.bot.send_message(chat_id=update.message.chat.id, message_id=update.message.message_id,
                                         text='The message was sent to {} users.'
                                         .format(len(self.__users__.get_users())))

    @run_async
    def send_message(self, update: Update, context: CallbackContext):
        if self.can_run(update, context):
            __logger__ = logging.getLogger(__name__)

            args = update.message.text.split(' ', 2)

            if len(args) == 1:
                # Show usage
                context.bot.send_message(chat_id=update.effective_chat.id, text='Usage: /send [id] [message]')
            elif len(args) == 2:
                # Error
                context.bot.send_message(chat_id=update.effective_chat.id, text='You need to enter a message.')
            elif len(args) == 3:
                # Send message
                try:
                    id_ = int(update.message.text.split(' ', 2)[1])
                    message = update.message.text.split(' ', 2)[2]
                    context.bot.send_message(chat_id=id_, text=message)
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text='The message has been sent to the user')
                except ValueError:
                    context.bot.send_message(chat_id=update.effective_chat.id, text='You need to enter a chat id.')
                except (Unauthorized, BadRequest):
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text='There was an error sending the message.')
