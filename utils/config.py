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
from datetime import datetime

__logger__ = logging.getLogger(__name__)

__config_file__ = 'config.json'
__offers_file__ = 'offers.json'


class Config:
    global __logger__

    def __init__(self):
        if os.path.isfile(__config_file__):
            __logger__.info('Loading "{}"...'.format(__config_file__))
            with open(__config_file__) as f:
                self.__config__ = json.loads(f.read())
        else:
            __logger__.error('E101: "{}" not found. Download "config.base.json" from '
                             'https://github.com/giacomoferretti/mcdapi-telegram-bot'.format(__config_file__))
            exit(101)

        if not os.path.isfile(__offers_file__):
            __logger__.error('E102: "{}" not found. Checkout https://github.com/giacomoferretti/mcdapi-tools '
                             'to see how to get the offers.'.format(__offers_file__))
            exit(102)

    def __save_config(self):
        with open(__config_file__, 'w') as f:
            f.write(json.dumps(self.__config__, indent=2))

    def __reload(self):
        self.__init__()

    def get_token(self):
        return self.__config__['token']

    def get_owner_id(self):
        return self.__config__['ownerId']

    def get_owner_username(self):
        return self.__config__['ownerUsername']

    def get_admins(self):
        return self.__config__['adminIds']

    def get_templates_folder(self):
        return self.__config__['templatesFolder']

    def is_proxy_enabled(self):
        return self.__config__['proxyEnabled']

    def get_proxy_url(self):
        return self.__config__['proxyUrl']

    def is_admin(self, id_):
        return id_ == self.__config__['ownerId'] or id_ in self.__config__['adminIds']

    def add_admin(self, id_):
        self.__config__['adminIds'].append(int(id_))
        self.__save_config()

    def remove_admin(self, id_):
        self.__config__['adminIds'].remove(int(id_))
        self.__save_config()

    def set_maintenance(self, active):
        self.__config__['maintenance'] = active
        if active:
            self.__config__['maintenanceStarted'] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        self.__save_config()

    def get_maintenance_time(self):
        return self.__config__['maintenanceStarted']

    def get_maintenance(self):
        return self.__config__['maintenance']

    def get_template(self, template):
        with open(os.path.join(self.get_templates_folder(), template)) as _f:
            return _f.read()

    def to_dict(self):
        return self.__config__
