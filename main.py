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
import traceback

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    Filters, CallbackContext, CallbackQueryHandler

from commands import promo, coupon, admin
from utils import config, users, logger

__major__ = 0
__minor__ = 2
__patch__ = 0
__metadata__ = ''
__version__ = '{}.{}.{}{}'.format(__major__, __minor__, __patch__, __metadata__)


def setup():
    global __logger__, __users__, __config__
    logger.init()

    __logger__ = logging.getLogger(__name__)

    __logger__.info('Starting mcdapi-telegram-bot ({})...'.format(__version__))
    __users__ = users.Users()
    __config__ = config.Config()
    __logger__.info('Done loading!')


def error(update: Update, context: CallbackContext):
    __logger__.warning('Update "%s" caused error "%s"', update, context.error)
    traceback.print_exc()


def main():
    updater = Updater(__config__.get_token(), use_context=True)

    # Log all messages
    updater.dispatcher.add_handler(MessageHandler(Filters.text | Filters.command, logger.log_message), group=1)
    updater.dispatcher.add_handler(CallbackQueryHandler(logger.log_callback), group=1)

    # Commands
    __admin = admin.AdminManager(__config__, __users__)
    __promo = promo.PromoCommand(__config__)
    __coupon = coupon.CouponHandler(__config__)

    updater.dispatcher.add_handler(CommandHandler('start', __coupon.home))
    updater.dispatcher.add_handler(CallbackQueryHandler(__coupon.callback, pattern='{}.*'.format(__coupon.name)))

    # updater.dispatcher.add_handler(CommandHandler('admin', __admin.admin_handler))
    # updater.dispatcher.add_handler(CommandHandler('maintenance', __admin.maintenance_handler))
    updater.dispatcher.add_handler(CommandHandler('promo', __promo.handler))

    updater.dispatcher.add_handler(CommandHandler('broadcast', __admin.broadcast))
    updater.dispatcher.add_handler(MessageHandler(Filters.reply, __admin.send_broadcast))

    updater.dispatcher.add_handler(CommandHandler('send', __admin.send_message))
    # updater.dispatcher.add_handler(CallbackQueryHandler(keyboard_handler))

    # Error handler
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    setup()
    main()
