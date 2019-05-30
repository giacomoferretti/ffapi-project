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

import json
import logging
from io import BytesIO

import qrcode
import requests
from mcdapi import coupon, endpoints
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from commands import base
from utils import templates

__offers_file__ = 'offers.json'


def generate_coupon(id):
    # Generate config
    android_id = coupon.get_random_device_id()
    vmob_uid = coupon.generate_vmob_uid(android_id)
    username = coupon.generate_username(android_id)
    password = coupon.generate_password(android_id)
    plexurek = coupon.generate_plexure_api_key(vmob_uid)

    headers = coupon.strip_unnecessary_headers(coupon.get_random_headers(vmob_uid, plexurek))

    r = requests.request(endpoints.DEVICE_REGISTRATION['method'], endpoints.DEVICE_REGISTRATION['url'],
                         data=endpoints.DEVICE_REGISTRATION['body'].format(username, password), headers=headers)

    if r.status_code == 200:
        # print('Successfully got a token.')
        js = json.loads(r.content)
        ACCESS_TOKEN = js['access_token']
        TOKEN_TYPE = js['token_type']
        # print('TOKEN: ' + ACCESS_TOKEN)
        headers['Authorization'] = 'bearer {}'.format(ACCESS_TOKEN)

    r = requests.post(endpoints.REDEEM_OFFER['url'], data=endpoints.REDEEM_OFFER['body'].format(id, id),
                      headers=headers)
    js = json.loads(r.content.decode())
    return js


class CouponHandler(base.Command):
    name = 'coupon'

    def home(self, update: Update, context: CallbackContext):
        body = self.__config__.get_template('home.md').format(name=update.effective_user['first_name'],
                                                              id=update.effective_user['id'], coupons='19')

        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("\U0001F354  Lista coupons", callback_data='{}_list'.format(self.name))
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send message
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('header.png', 'rb'),
                               reply_markup=reply_markup,
                               caption=body, parse_mode=ParseMode.MARKDOWN)

    def callback(self, update: Update, context: CallbackContext):
        __logger__ = logging.getLogger(__name__)

        query = update.callback_query

        if query.data.startswith('{}_homepage'.format(self.name)):
            # Return to homepage
            self.home(update, context)

            if query.data.endswith('_r'):
                # Delete calling message
                context.bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
            else:
                # Remove keyboard from calling message
                context.bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                                      message_id=query.message.message_id,
                                                      reply_markup=None)

        elif self.check_callback(query.data, 'list'):
            # Delete calling message
            context.bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)

            # Populate keyboard
            # Load offers
            with open(__offers_file__) as f:
                offers = json.loads(f.read())

            keyboard = []
            for x in offers:
                keyboard.append([InlineKeyboardButton(x['customTitle'], callback_data='{}_id_{}'.format(self.name,
                                                                                                        x['id']))])
            keyboard.append([InlineKeyboardButton("\U0001F519  Menu principale",
                                                  callback_data='{}_homepage_r'.format(self.name))])
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send message
            context.bot.send_message(chat_id=query.message.chat.id, text="Seleziona un'offerta:",
                                     reply_markup=reply_markup)

        elif query.data.startswith('{}_id'.format(self.name)):
            # Edit message
            query.edit_message_text(text="Sto generando l'offerta...")

            # Load template
            body = templates.get_template('coupon.md')

            # Generate coupon
            js = generate_coupon(query.data.split('_')[2])
            code = js['redemptionText']

            # Generate QR code
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=15, border=10)
            qr.add_data(code)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("\U0001F519  Menu principale", callback_data='{}_homepage'.format(self.name))
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Read QR code bytes
            bio = BytesIO()
            img.save(bio, 'PNG')
            bio.seek(0)

            # Send QR code
            context.bot.send_photo(chat_id=query.message.chat.id, photo=bio,
                                   caption=body.format(js['title'], js['description'], code, js['id']),
                                   parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

            context.bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)
