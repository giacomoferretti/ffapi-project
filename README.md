[![Codacy Badge](https://api.codacy.com/project/badge/Grade/72f3eec1c1a3426d82c979397577e8ac)](https://app.codacy.com/app/giacomoferretti/mcdapi-telegram-bot?utm_source=github.com&utm_medium=referral&utm_content=giacomoferretti/mcdapi-telegram-bot&utm_campaign=Badge_Grade_Dashboard)
![GitHub tag (latest SemVer)](https://img.shields.io/github/tag/giacomoferretti/mcdapi-telegram-bot.svg?color=blue&label=Stable)
![GitHub tag (latest SemVer pre-release)](https://img.shields.io/github/tag-pre/giacomoferretti/mcdapi-telegram-bot.svg?label=Testing)
[![GitHub license](https://img.shields.io/github/license/giacomoferretti/mcdapi-telegram-bot.svg?color=informational)](https://github.com/giacomoferretti/mcdapi-telegram-bot/blob/master/LICENSE)

# mcdapi-telegram-bot
`mcdapi-telegram-bot` is a simple bot written in Python that can generate valid coupons and promocodes that you can use at McDonald's.

You can see a running example here: [@mcdapi_bot](https://telegram.me/mcdapi_bot)

## Requirements
* Python 3

## Setting the bot up
Copy or rename `config.base.json` to `config.json` and edit it following this guide:

```text
token: You have to create a bot and get the token from @botfather on Telegram
ownerId: Your Telegram ID (Not necessary)
ownerUsername: Your Telegram username (Not necessary)
adminIds: [id, ...] (Not necessary)
templatesFolder: The name of the folder containing the templates
proxyEnabled: Enables and disables generating coupons through a proxy
proxyUrl: URL of the proxy, if enabled
```

You can download `offers.json` already scraped and parsed with `mcdapi-tools` [here](https://gist.github.com/giacomoferretti/a24797299041692613c155cac79b8127).

## Running the bot
You can run the bot using one of these three methods

### Docker
| Image     | Build time (without cache) | Size   |
|-----------|----------------------------|--------|
| torproxy  | ~13 seconds                | ~17MB  |
| mcdapibot | ~2 minutes and 30 seconds  | ~111MB |

If you have Docker Compose simply run `docker-compose up`.

If not use this commands:
```bash
docker build . -t torproxy -f .docker/torproxy-Dockerfile --build-arg socks_port=9050 --build-arg control_password="password" --build-arg control_port=9051
docker build . -t mcdapibot -f .docker/mcdapibot-Dockerfile

docker run -d --name=torproxy torproxy
docker run -d --name=mcdapibot --link=torproxy -v $(pwd)/images:/app/images -v $(pwd)/logs:/app/logs -v $(pwd)/templates:/app/templates -v $(pwd)/config.json:/app/config.json -v $(pwd)/users.json:/app/users.json -v $(pwd)/offers.json:/app/offers.json mcdapibot
```

### Python 3
```bash
pip3 install -r requirements.txt
python3 main.py
```

## Disclaimer
This repository is against McDonald's ToS.

This repository is not affiliated with McDonald's Corp in any way. "McDonald's" and "McDonald's Logo" are registered trademarks of McDonald's Corp.
