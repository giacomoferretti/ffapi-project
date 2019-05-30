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

__logger__ = logging.getLogger(__name__)

__users_file__ = 'users.json'


class Users:
    def __init__(self):
        self.__users__ = {}

        # Load saved users
        if os.path.isfile(__users_file__) and os.stat(__users_file__).st_size != 0:
            __logger__.info('Loading "{}"...'.format(__users_file__))
            with open(__users_file__) as f:
                self.__users__ = json.loads(f.read())
                __logger__.info('Loaded {} users.'.format(len(self.__users__)))
        else:
            __logger__.warning('"{}" not found or empty.'.format(__users_file__))

    def __save_users(self):
        with open(__users_file__, 'w') as f:
            f.write(json.dumps(self.__users__))

    def get_users(self):
        return self.__users__

    def add_user(self, user):
        self.__users__[str(user['id'])] = user
        self.__save_users()

    def remove_user(self, id_):
        self.__users__.pop(str(id_))
        self.__save_users()
