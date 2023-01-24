from flask import Flask, render_template, request

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent,
    PostbackEvent, 
    TextMessage,
    ImageMessage,
    TemplateSendMessage,
    FlexSendMessage,
)
from src.services import (
    HandleMessageService,
    HandleImageService,
    HandlePostbackService
)

import os


YOUR_CHANNEL_ACCESS_TOKEN = os.environ['YOUR_CHANNEL_ACCESS_TOKEN']
YOUR_CHANNEL_SECRET = os.environ['YOUR_CHANNEL_SECRET']

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


reply_url = 'https://api.line.me/v2/bot/message/reply'

app = Flask(__name__)


@app.route('/')
def index():
    return "index"


@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    print('callback', request)
    print('request', body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# handle message from LINE
@handler.add(MessageEvent, message=FlexSendMessage)
def handle_message(event):
    print('handle_message', event)

    reply = HandleMessageService.create_reply_message(event)
    line_bot_api.reply_message(
        event.reply_token,
        reply,
    )

# handle message from LINE
@handler.add(MessageEvent, message=TemplateSendMessage)
def handle_image(event):
    print('handle_image', event)

    reply = HandleImageService.create_reply_message(event)
    line_bot_api.reply_message(
        event.reply_token,
        reply,
    )


# handle message from LINE
@handler.add(PostbackEvent, message=TemplateSendMessage)
def handle_postback(event):
    print('handle_image', event)

    reply = HandlePostbackService.create_reply_message(event)
    line_bot_api.reply_message(
        event.reply_token,
        reply,
    )


if __name__ == "__main__":
	app.run()