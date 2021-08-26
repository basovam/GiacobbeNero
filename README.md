# GiacobbeNero
This is a simple Blackjack bot for telegram.
You can try it: [@GiacobbeNero](https://telegram.dog/GiacobbeNero_bot)

## 1. Updating of config file.
Change `hostname` and `serverport` if it necessary.\
Replace `bot_token` with your bot token.\
Font file did not included in repository. It available via link:\
https://github.com/opensourcedesign/fonts/blob/master/gnu-freefont_freesans/FreeSansBold.ttf

## 2. Start bot
```python3 main.py```

## 3. Create a Webhook.
For example, with curl:\
```curl -F "url=https://<your url address>" https://api.telegram.org/bot<your bot token>/setWebhook```
