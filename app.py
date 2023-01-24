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
# app.secret_key = os.environ['YOUR_SECRET_KEY']
# app.permanent_session_lifetime = timedelta(minutes=5)


# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



class target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, default=0)
    target = db.Column(db.Integer, default=0)

    def __init__(self, user_id, target):
        self.user_id = user_id
        self.target = target


def send_reply(reply_token, messages):
    reply = {
        'replyToken': reply_token,
        'messages': messages
    }

    # ヘッダー作成
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(YOUR_CHANNEL_ACCESS_TOKEN)
    }

    # jsonでbotに返す
    requests.post(
        reply_url,
        data=json.dumps(reply),
        headers=headers
    )


@app.route('/')
def index():
    return "index"


@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    print('request', body)

    handle webhook body
    for event in body['events']:
        replyToken = event['replyToken']
        event_type = event['type']

        # if event_type == 'message':
        #     message = event['text']
        #     if 

        messages = {
            "type": "flex",
            "altText": "flexmenu",
            "contents": {
                "type": "carousel",
                "contents": {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://www.shinchan-social.jp/wp-content/uploads/2020/07/o0921115114470951509.jpg",
                        "size": "full",
                        "aspectMode": "cover",
                        "aspectRatio": "320:213"
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "name:",
                                        "size": "xs",
                                        "margin": "md",
                                        "color": "#8c8c8c",
                                        "flex": 0
                                    },
                                    {
                                    "type": "text",
                                    "text": "テテ",
                                    "size": "xs",
                                    "margin": "md",
                                    "flex": 0
                                    }
                                ]
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#00bfff",
                                "action": {
                                    "type": "postback",
                                    "label": "Manipulate",
                                    "data": "action=run&person=tete"
                                }
                            }
                        ]
                    }
                }
            }
        }

        send_reply(replyToken, messages)



if __name__ == "__main__":
	app.run()