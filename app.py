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

database_url = os.environ['DATABASE_URL']
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.root_path, 'db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Migrate(app, db)


@app.before_first_request
def init():
    db.create_all()


class Target(db.Model):
    __tablename__ = 'Target'
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

    # body_text = request.get_data(as_text=True)    
    body = request.json

    print(f'★body: {body}')
    print()

    # handle webhook body
    for event in body['events']:
        replyToken = event['replyToken']
        event_type = event['type']
        source = event['source']

        print(f'★EventType : {event_type}')
        
        if source['type'] == 'user':
            user_id = source['userId']
        else:
            print('×userIdがない')
            return

        if event_type == 'message':
            message = event['message']
            msg_id = message['id']
            print(f'★Message: {message}')
            if message['type'] == 'message':
                text = message['text']
                print(f'★MessageText: {text}')

            elif message['type']  == 'image':
                
                print('画像取得しにいく', msg_id, user_id)
                image = get_image(msg_id)
                print('image', image, type(image))

                target = db.session.query(Target).filter_by(user_id=user_id)
                print(f'★Target取得結果: {target}  =>  ', target.count())
                
                if target.count() == 0:
                    print('ターゲットないから作成')
                    target = Target(user_id, msg_id)
                else:
                    print('既にターゲットが存在するので更新')
                    target.msg_id = msg_id

                db.session.add(target)
                db.session.commit()
        
        messages = [
            {
                "type": "text",
                "text": "Hello, world"
            }
        ]

        # messages = {
        #     'type': 'template',
        #     'altText': 'this is a timer test',
        #     'template': {
        #         'type': 'buttons',
        #         'actions': [
        #             {
        #                 "type":"datetimepicker",
        #                 "label":"入",
        #                 "data":"action=manipulate_timer&status=from&kadenId=" + selected_timer_kadenId,
        #                 "mode":"datetime"
        #             },
        #             {
        #                 "type":"datetimepicker",
        #                 "label":"切",
        #                 "data":"action=manipulate_timer&status=to&kadenId=" + selected_timer_kadenId,
        #                 "mode":"datetime"
        #             }
        #         ],
        #         'text': kaden_info[selected_timer_kadenId]['name'] + 'のタイマーを設定'
        #     }
        # }

        send_reply(replyToken, messages)

    return {'statusCode': 200, 'body': '{}'}


if __name__ == "__main__":
	app.run()