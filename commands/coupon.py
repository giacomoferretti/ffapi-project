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
from telegram.ext import CallbackContext, run_async

from commands import base

__offers_file__ = 'offers.json'

__proxy_enabled__ = True
__proxy_url__ = 'socks5://127.0.0.1:9050'


def generate_coupon(id_):
    __logger__ = logging.getLogger(__name__)

    # Get session
    session = requests.session()

    if __proxy_enabled__:
        session.proxies = {
            'http': __proxy_url__,
            'https': __proxy_url__
        }

    # Generate
    android_id = coupon.get_random_device_id()
    vmob_uid = coupon.generate_vmob_uid(android_id)
    username = coupon.generate_username(android_id)
    password = coupon.generate_password(android_id)
    plexure = coupon.generate_plexure_api_key(vmob_uid)

    headers = coupon.strip_unnecessary_headers(coupon.get_random_headers(vmob_uid, plexure))

    r = session.request(endpoints.DEVICE_REGISTRATION['method'], endpoints.DEVICE_REGISTRATION['url'],
                        data=endpoints.DEVICE_REGISTRATION['body'].format(username, password), headers=headers)

    if r.status_code == 200:
        js = json.loads(r.content)
        token = js['access_token']
        headers['Authorization'] = 'bearer {}'.format(token)

    r = session.post(endpoints.REDEEM_OFFER['url'], data=endpoints.REDEEM_OFFER['body'].format(id_, id_),
                     headers=headers)

    if r.status_code == 200:
        __logger__.info('Successfully generated the coupon.')
    else:
        __logger__.error('There was an error generating the coupon: {}'.format(r.content))

    return json.loads(r.content.decode())


class CouponHandler(base.Command):
    name = 'coupon'

    def home(self, update: Update, context: CallbackContext):
        body = self.__config__.get_template('home.md').format(name=update.effective_user['first_name'],
                                                              id=update.effective_user['id'], coupons='19')

        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("\U0001F354  Lista coupons", callback_data='{}_list'.format(self.name))
            ],
            [
                InlineKeyboardButton("Source Code", url='https://github.com/giacomoferretti/mcdapi-telegram-bot')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send message
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('header.png', 'rb'),
                               reply_markup=reply_markup,
                               caption=body, parse_mode=ParseMode.MARKDOWN)

    @run_async
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
                offer_title = x['title']
                if x['customTitle'] != '':
                    offer_title = x['customTitle']

                keyboard.append([InlineKeyboardButton(offer_title, callback_data='{}_id_{}'.format(self.name,
                                                                                                   x['id']))])
            keyboard.append([InlineKeyboardButton("\U0001F519  Menu principale",
                                                  callback_data='{}_homepage_r'.format(self.name))])
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send message
            context.bot.send_message(chat_id=query.message.chat.id, text="Seleziona un'offerta:",
                                     reply_markup=reply_markup)

        # TODO: Show a preview of the offer
        elif query.data.startswith('{}_info_id'.format(self.name)):
            # Edit message
            query.edit_message_text(text="Riprova più tardi. 5 min.")

            id_ = query.data.split('_')[2]

            # Load offers
            with open(__offers_file__) as f:
                offers = json.loads(f.read())
                offer_index = next((index for (index, d) in enumerate(offers) if d["id"] == id_), None)

            r = requests.request(endpoints.PROMO_IMAGE['method'], endpoints.PROMO_IMAGE['url']
                                 .format(size=512, path=offers[offer_index]['promoImagePath']))

            print(r.status_code)

        elif query.data.startswith('{}_id'.format(self.name)):
            # Edit message
            query.edit_message_text(text="Sto generando l'offerta...")

            # Load template
            body = self.__config__.get_template('coupon.md')

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
