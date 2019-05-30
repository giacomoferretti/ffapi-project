[![Version](https://badge.fury.io/py/mcdapi.svg)](https://pypi.org/project/mcdapi/)
![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/giacomoferretti/mcdapi.svg?color=blue&label=Stable)
![GitHub tag (latest SemVer pre-release)](https://img.shields.io/github/tag-pre/giacomoferretti/mcdapi.svg?label=Testing)
[![GitHub license](https://img.shields.io/github/license/giacomoferretti/mcdapi-telegram-bot.svg?color=informational)](https://github.com/giacomoferretti/McDonaldsApi/blob/master/LICENSE)

# mcdapi-telegram-bot
`mcdapi-telegram-bot` is a simple bot written in Python that can generate valid coupons and promocodes that you can use at McDonald's.

You can see a running example here: [@mcdapi_bot](https://telegram.me/mcdapi_bot)

## Requirements
* Python 3

## Installation
Copy or rename `config.base.json` to `config.json` and edit it following this guide:

```
token: You have to create a bot and get the token from @botfather on Telegram
ownerId: Your Telegram ID (Not necessary)
ownerUsername: Your Telegram username (Not necessary)
adminIds: [id, ...] (Not necessary)
templatesFolder: The name of the folder containing the templates
```

## Disclaimer
This repository is not affiliated with Mcdonald's Corp in any way. "McDonald's" and "McDonald's Logo" are registered trademarks of Mcdonald's Corp.
