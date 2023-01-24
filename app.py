from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy

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

from datetime import timedelta 

import os
import requests


YOUR_CHANNEL_ACCESS_TOKEN = os.environ['YOUR_CHANNEL_ACCESS_TOKEN']
YOUR_CHANNEL_SECRET = os.environ['YOUR_CHANNEL_SECRET']

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


reply_url = 'https://api.line.me/v2/bot/message/reply'

app = Flask(__name__)
app.secret_key = os.environ['YOUR_SECRET_KEY']
app.permanent_session_lifetime = timedelta(minutes=5)


db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


class target(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer)
    target = db.Column(db.Integer)
	
	def __init__(self, user_id, target):
		self.user_id = user_id
        self.target = target



# class MyLineBotApi(LineBotApi):

#     def reply_message(self, reply_token, messages, notification_disabled=False, timeout=None):
#         if not isinstance(messages, (list, tuple)):
#             messages = [messages]

#         data = {
#             'replyToken': reply_token,
#             'messages': [message.as_json_dict() for message in messages],
#             'notificationDisabled': notification_disabled,
#         }

#         self._post(
#             '/v2/bot/message/reply', data=json.dumps(data), timeout=timeout
#         )


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
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print('handle_message', event)

    

    t = target(event.source.user_id)

    db.session.add(t)
	db.session.commit()

    reply = HandleMessageService.create_reply_message(event)
    line_bot_api.reply_message(
        event.reply_token,
        reply,
    )

    

    # session.permanent = True  
    # if 'key' in session:
    #     session['key'] = session['key'] + 1
    # else:
    #     session['key'] = 0

    # print('sessioテスト', session['key'])

    # messages = {
    #     "type": "uri",
    #     "label": "画像を選択",
    #     "uri": "https://line.me/R/nv/cameraRoll/single"
    # }
    
    # replyToken = event.reply_token 

    # reply = {
    #     'replyToken': replyToken,
    #     'messages': messages
    # }

    # headers = {
    #     'Content-Type': 'application/json',
    #     'Authorization': 'Bearer {}'.format(YOUR_CHANNEL_ACCESS_TOKEN)
    # }

    # requests.post(
    #     reply_url,
    #     data=json.dumps(reply),
    #     headers=headers
    # )

# handle message from LINE
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    print('handle_image', event)

    reply = HandleImageService.create_reply_message(event)
    line_bot_api.reply_message(
        event.reply_token,
        reply,
    )


# handle message from LINE
@handler.add(PostbackEvent, message=TextMessage)
def handle_postback(event):
    print('handle_postback', event)

    reply = HandlePostbackService.create_reply_message(event)
    line_bot_api.reply_message(
        event.reply_token,
        reply,
    )


if __name__ == "__main__":
	app.run()