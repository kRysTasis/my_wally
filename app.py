from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

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

from io import BytesIO
from datetime import timedelta
# from PIL import Image

import os
import requests
import json

YOUR_CHANNEL_ACCESS_TOKEN = os.environ['YOUR_CHANNEL_ACCESS_TOKEN']
YOUR_CHANNEL_SECRET = os.environ['YOUR_CHANNEL_SECRET']

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


reply_url = 'https://api.line.me/v2/bot/message/reply'
image_url = 'https://api-data.line.me/v2/bot/message/{msg_id}/content'

app = Flask(__name__)
# app.secret_key = os.environ['YOUR_SECRET_KEY']
# app.permanent_session_lifetime = timedelta(minutes=5)


# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Migrate(app, db)


class target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Text, default=0)
    target = db.Column(db.Text, default=0)

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

    print('send_reply', reply)

    # jsonでbotに返す
    requests.post(
        reply_url,
        data=json.dumps(reply),
        headers=headers
    )

def get_image(msg_id):

    url = image_url.format(msg_id=msg_id)

    # ヘッダー作成
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(YOUR_CHANNEL_ACCESS_TOKEN)
    }

    return requests.get(
        url,
        headers=headers
    )


@app.route('/')
def index():
    return "index"


@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body_text = request.get_data(as_text=True)
    app.logger.info("Request body: " + body_text)
    
    body = request.json
    print('request', body)

    print("body['events']", body['events'])

    # handle webhook body
    for event in body['events']:
        replyToken = event['replyToken']
        event_type = event['type']
        source = event['source']
        if source['type'] == 'user':
            user_id = source['user_id']

        print('replyToken', replyToken)
        print('event_type', event_type)

        if event_type == 'message':
            message = event['message']
            msg_id = message['id']
            if message['type']  == 'image':
                
                print('画像取得しにいく')
                image = get_image(msg_id)
                print('image', image, type(image))
                
                t = target(user_id, msg_id)
                db.session.add(t)
                db.session.commit()

        messages = {
            "type": "flex",
            "altText": "flexmenu",
            "contents": {
                "type": "carousel",
                "contents": {
                    "type": "bubble",
                    # "hero": {
                    #     "type": "image",
                    #     "url": "https://www.shinchan-social.jp/wp-content/uploads/2020/07/o0921115114470951509.jpg",
                    #     "size": "full",
                    #     "aspectMode": "cover",
                    #     "aspectRatio": "320:213"
                    # },
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
                    }
                    # "footer": {
                    #     "type": "box",
                    #     "layout": "horizontal",
                    #     "contents": [
                    #         {
                    #             "type": "button",
                    #             "style": "primary",
                    #             "color": "#00bfff",
                    #             "action": {
                    #                 "type": "postback",
                    #                 "label": "Manipulate",
                    #                 "data": "action=run&person=tete"
                    #             }
                    #         }
                    #     ]
                    # }
                }
            }
        }

        send_reply(replyToken, messages)

    return {'statusCode': 200, 'body': '{}'}


if __name__ == "__main__":
	app.run()
    db.create_all()