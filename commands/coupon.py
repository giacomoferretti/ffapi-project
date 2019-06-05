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
import os
import re
import socket
from datetime import timedelta
from io import BytesIO

import qrcode
import requests
from PIL import Image, ImageDraw
from mcdapi import coupon, endpoints
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import CallbackContext, run_async

from commands import base
from utils import config

__image_folder__ = 'images'


def round_corner(radius, fill):
    """Draw a round corner"""
    corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
    draw = ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill)
    return corner


def round_rectangle(size, radius, fill):
    """Draw a rounded rectangle"""
    width, height = size
    rectangle = Image.new('RGBA', size, fill)
    corner = round_corner(radius, fill)
    rectangle.paste(corner, (0, 0))
    rectangle.paste(corner.rotate(90), (0, height - radius))  # Rotate the corner and paste it
    rectangle.paste(corner.rotate(180), (width - radius, height - radius))
    rectangle.paste(corner.rotate(270), (width - radius, 0))
    return rectangle


def get_days(l):
    days = []
    for x in l:
        if x == 0:
            days.append('Domenica')
        elif x == 1:
            days.append('Lunedì')
        elif x == 2:
            days.append('Martedì')
        elif x == 3:
            days.append('Mercoledì')
        elif x == 4:
            days.append('Giovedì')
        elif x == 5:
            days.append('Venerdì')
        elif x == 6:
            days.append('Sabato')
    return ' - '.join(days)


def parse_url(url):
    p = '(?:.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'

    m = re.search(p, url)
    return m.group('host'), int(m.group('port'))


def is_port_open(url):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(parse_url(url))
        s.shutdown(2)
        return True
    except ConnectionRefusedError:
        return False


def get_headers(config_):
    # Get session
    session = get_session(config_)

    # Generate
    android_id = coupon.get_random_device_id()
    vmob_uid = coupon.generate_vmob_uid(android_id)
    username = coupon.generate_username(android_id)
    password = coupon.generate_password(android_id)
    plexure = coupon.generate_plexure_api_key(vmob_uid)

    headers = coupon.strip_unnecessary_headers(coupon.get_random_headers(vmob_uid, plexure))

    r = session.request(endpoints.DEVICE_REGISTRATION['method'], endpoints.DEVICE_REGISTRATION['url'],
                        data=endpoints.DEVICE_REGISTRATION['body'].format(username=username, password=password),
                        headers=headers)

    if r.status_code == 200:
        js = json.loads(r.content)
        token = js['access_token']
        headers['Authorization'] = 'bearer {}'.format(token)

    return headers


def get_session(config_):
    __logger__ = logging.getLogger(__name__)

    # Get session
    session = requests.session()

    if is_port_open(config_.get_proxy_url()):
        if config_.is_proxy_enabled():
            session.proxies = {
                'http': config_.get_proxy_url(),
                'https': config_.get_proxy_url()
            }
    else:
        __logger__.warning('Cannot connect to proxy.')

    return session


def generate_coupon(id_, __config__: config.Config):
    __logger__ = logging.getLogger(__name__)

    # Get session
    session = get_session(__config__)

    # Generate
    android_id = coupon.get_random_device_id()
    vmob_uid = coupon.generate_vmob_uid(android_id)
    username = coupon.generate_username(android_id)
    password = coupon.generate_password(android_id)
    plexure = coupon.generate_plexure_api_key(vmob_uid)

    headers = coupon.strip_unnecessary_headers(coupon.get_random_headers(vmob_uid, plexure))

    r = session.request(endpoints.DEVICE_REGISTRATION['method'], endpoints.DEVICE_REGISTRATION['url'],
                        data=endpoints.DEVICE_REGISTRATION['body'].format(username=username, password=password),
                        headers=headers)

    if r.status_code == 200:
        js = json.loads(r.content)
        token = js['access_token']
        headers['Authorization'] = 'bearer {}'.format(token)

    r = session.post(endpoints.REDEEM_OFFER['url'], data=endpoints.REDEEM_OFFER['body'].format(id=id_),
                     headers=headers)

    if r.status_code == 200:
        __logger__.info('Successfully generated the coupon.')
    else:
        __logger__.error('There was an error generating the coupon: {}'.format(r.content))

    return json.loads(r.content.decode())


class CouponHandler(base.Command):
    name = 'coupon'

    @run_async
    def home(self, update: Update, context: CallbackContext):
        body = self.__config__.get_template('home.html')\
            .format(id=update.effective_user['id'], coupons=len(self.__config__.__offers__))

        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("\U0001F354 Lista coupons", callback_data='{}_list'.format(self.name))
            ],
            [
                InlineKeyboardButton("Genera Promocode", callback_data='promo_generate')
            ],
            [
                InlineKeyboardButton("\u2753 F.A.Q.", callback_data='coupon_faq'),
                InlineKeyboardButton("Source Code", url='http://bit.ly/2XvxXey')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send message
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open('header.png', 'rb'),
                               reply_markup=reply_markup,
                               caption=body, parse_mode=ParseMode.HTML)

    @run_async
    def callback(self, update: Update, context: CallbackContext):
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
            keyboard = []
            for x in self.__config__.__offers__:
                offer_title = self.__config__.__offers__[x]['title']
                if self.__config__.__offers__[x]['customTitle'] != '':
                    offer_title = self.__config__.__offers__[x]['customTitle']

                if self.__config__.__offers__[x]['special']:
                    offer_title = '\U0001F552 ' + offer_title

                keyboard.append([InlineKeyboardButton(offer_title, callback_data='{}_info_id_{}'.format(self.name, x))])
            keyboard.append([InlineKeyboardButton("\u2b05 Menu principale",
                                                  callback_data='{}_homepage_r'.format(self.name))])
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send message
            context.bot.send_message(chat_id=query.message.chat.id, text="Seleziona un'offerta:",
                                     reply_markup=reply_markup)

        elif query.data.startswith('{}_info_id'.format(self.name)):
            # Answer callback
            context.bot.answer_callback_query(query.id, text='Sto caricando l\'offerta...')
            context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)

            # Get session
            session = get_session(self.__config__)

            # Delete calling message
            context.bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)

            id_ = query.data.split('_')[3]

            offer = self.__config__.__offers__[str(id_)]

            if os.path.isfile(os.path.join(__image_folder__, offer['promoImagePath'])):
                with open(os.path.join(__image_folder__, offer['promoImagePath']), 'rb') as f:
                    image = f.read()
            else:
                params = endpoints.PROMO_IMAGE['params']
                params['path'] = offer['promoImagePath']
                params['imageFormat'] = 'png'
                r = session.request(endpoints.PROMO_IMAGE['method'], endpoints.PROMO_IMAGE['url'].format(size=1080),
                                    params=params)

                if r.status_code == 200:
                    with open(os.path.join(__image_folder__, offer['promoImagePath']), 'wb') as f:
                        f.write(r.content)
                        image = r.content

            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton('\u2705 Va bene', callback_data='{}_id_{}'.format(self.name, id_)),
                    InlineKeyboardButton('\u2b05 Torna indietro', callback_data='{}_list'.format(self.name))
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            extra_content = ''
            if offer['special']:
                days = get_days(offer['daysOfWeek'])
                start_time = str(timedelta(minutes=offer['dailyStartTime']))[:-3]
                end_time = str(timedelta(minutes=offer['dailyEndTime']))[:-3]
                extra_content = '<b>Questa è un\'offerta speciale!</b>\n' \
                                'Può essere riscatta solo nei seguenti giorni: <i>{}</i>\n' \
                                'E solo nei seguenti orari: <i>{} - {}</i>'.format(days, start_time, end_time)

            body = self.__config__.get_template('coupon_preview.html')\
                .format(title=offer['title'], description=offer['description'], id=id_, start_date=offer['startDate'],
                        end_date=offer['endDate'], extra=extra_content)

            context.bot.send_photo(chat_id=query.message.chat.id, photo=BytesIO(image), caption=body,
                                   parse_mode=ParseMode.HTML, reply_markup=reply_markup)

        elif query.data.startswith('{}_id'.format(self.name)):
            # Edit message
            context.bot.answer_callback_query(query.id, text="Sto generando l'offerta...")

            # Remove keyboard from calling message
            context.bot.edit_message_reply_markup(chat_id=query.message.chat.id,
                                                  message_id=query.message.message_id,
                                                  reply_markup=None)

            context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)

            # Load template
            body = self.__config__.get_template('coupon.html')

            # Generate coupon
            js = generate_coupon(query.data.split('_')[2], self.__config__)

            # TODO: Temporary fix
            try:
                code = js['redemptionText']

                # Generate QR code
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=15, border=0)
                qr.add_data(code)
                qr.make(fit=True)
                qr_image = qr.make_image(fill_color="black", back_color="white")

                # Get offer background
                id_ = query.data.split('_')[2]
                offer = self.__config__.__offers__[str(id_)]

                offer_background = Image.open(os.path.join(__image_folder__, offer['promoImagePath']))
                qr_background = Image.open(os.path.join(__image_folder__, 'bg.png'))
                offset = (350, 350)

                image_width, image_height = offer_background.size
                final_image = Image.new('RGBA', (image_width, image_height), offer_background.getpixel((0, 0)))

                offer_background.putalpha(60)
                final_image = Image.alpha_composite(final_image, offer_background)
                final_image = Image.alpha_composite(final_image, qr_background)
                final_image.paste(qr_image, offset)

                # Create inline keyboard
                keyboard = [
                    [
                        InlineKeyboardButton("\u2b05 Menu principale", callback_data='{}_homepage'.format(self.name))
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Read QR code bytes
                bio = BytesIO()
                final_image.save(bio, 'PNG')
                bio.seek(0)

                # Send QR code
                context.bot.send_photo(chat_id=query.message.chat.id, photo=bio,
                                       caption=body.format(js['title'], js['description'], code, js['id']),
                                       parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            except KeyError:
                # Create inline keyboard
                keyboard = [
                    [
                        InlineKeyboardButton("\u2b05 Menu principale",
                                             callback_data='{}_homepage_r'.format(self.name))
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                context.bot.send_message(chat_id=query.message.chat.id,
                                         text='C\'è stato un errore. Riprova più tardi.', reply_markup=reply_markup)

            context.bot.delete_message(chat_id=query.message.chat.id, message_id=query.message.message_id)

        elif self.check_callback(query.data, 'faq'):
            context.bot.answer_callback_query(query.id)

            # Load template
            body = self.__config__.get_template('faq.html').format(id=self.__config__.get_owner_id(),
                                                                   name=self.__config__.get_owner_username())

            context.bot.send_message(chat_id=query.message.chat.id, text=body, parse_mode=ParseMode.HTML)
