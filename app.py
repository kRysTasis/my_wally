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
import urllib.parse

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
    # id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Text, primary_key=True)
    person = db.Column(db.Text)
    target = db.Column(db.Text)

    def __init__(self, user_id, person = '', target = ''):
        self.user_id = user_id
        self.person = person
        self.target = target


class Status(db.Model):
    """ユーザーの状態を表す
    
    status: 
        0 => 初期
        1 => 検索人物設定
        2 => 検索対象設定
    """

    __tablename__ = 'Status'
    user_id = db.Column(db.Text, primary_key=True)
    status = db.Column(db.Integer, default=0)

    def __init__(self, user_id, status):
        self.user_id = user_id
        self.status = status



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


def create_text_res_format(text):
    
    return {
        "type": "text",
        "text": text,
    }


def create_search_confirm():

    return {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
            "type": "confirm",
            "text": "検索します。よろしいでしょうか？",
            "actions": [
                {
                    "type": "postback",
                    "label": "はい",
                    "data": "action=2"
                },
                {
                    "type": "postback",
                    "label": "キャンセル",
                    "data": "action=99"
                }
            ]
        }
    }


def create_menu():
    
    return {
        "type": "flex",
        "altText": "flexmenu",
        "contents": {
            "type": "carousel",
            "contents": [
                {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#00bfff",
                                "action": {
                                    "type": "postback",
                                    "label": "検索人物設定",
                                    "data": "action=0"
                                }
                            }
                        ]
                    }
                },
                {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#8CFFB4",
                                "action": {
                                    "type": "postback",
                                    "label": "検索画像設定",
                                    "data": "action=1"
                                }
                            }
                        ]
                    }
                },
                {
                    "type": "bubble",
                    "body": {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#FF8800",
                                "action": {
                                    "type": "postback",
                                    "label": "初期化",
                                    "data": "action=99"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }


def set_search_person_status(user_id):
    
    print('set_search_person_status')

    s = db.session.query(Status).get(user_id)
    if s == None:
        s = Status(user_id, 0)
    s.status = 1
    db.session.add(s)
    db.session.commit()

    return [
        create_text_res_format("検索したい人物の画像を送信してください"),
    ]


def set_search_target_image_status(user_id):

    print('set_search_target_image_status')
    
    s = db.session.query(Status).get(user_id)
    if s == None:
        s = Status(user_id, 0)
    
    s.status = 2
    db.session.add(s)
    db.session.commit()

    return [
        create_text_res_format("検索したい画像を送信してください"),
    ]


def search(user_id):

    print('search')

    s = db.session.query(Status).get(user_id)
    if s == None:
        s = Status(user_id, 0)
    
    s.status = 0
    
    t = db.session.query(Target).get(user_id)

    if t != None:
        db.session.delete(t)

    db.session.add(s)
    db.session.commit()

    return [
        create_text_res_format("検索を行います"),
    ]


def init_status(user_id):

    print('init_status')
    
    s = db.session.query(Status).get(user_id)
    if s != None:
        s.status = 0
        db.session.add(s)
        db.session.commit()

    t = db.session.query(Target).get(user_id)

    if t != None:
        db.session.delete(t)
        db.session.commit()
    
    return [
        create_text_res_format("初期化を行います"),
    ]


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

        user_id = source['userId']

        if event_type == 'message':
            message = event['message']
            msg_id = message['id']
            print(f'★Message: {message}')
            
            if message['type'] == 'text':
                text = message['text']
                print(f'★MessageText: {text}')

                messages = [
                    create_text_res_format("メニューを開きます。"),
                    create_menu()
                ]

                # create_text_res_format("こんな事が出来ますよ"),

                send_reply(replyToken, messages)

            elif message['type']  == 'image':
                print('画像取得しにいく', msg_id, user_id)
                image = get_image(msg_id)
                print('image', image, type(image))

                s = db.session.query(Status).get(user_id)
                if s != None:
                    if s.status == 1:
                        # 対象人物に設定してstatus=2に

                        t = db.session.query(Target).get(user_id)
                        if t == None:
                            print('ターゲットないから作成')
                            t = Target(user_id)
                        
                        s.status = 2
                        t.person = msg_id

                        # メニューを表示して操作してねと
                        messages = [
                            create_text_res_format("対象画像を送信してください")
                        ]

                        db.session.add(s)
                        db.session.add(t)

                        send_reply(replyToken, messages)
                        
                    elif s.status == 2:
                        # 対象画像に設定して人物が設定してあれば検索するかの案内

                        t = db.session.query(Target).get(user_id)
                        if t == None:
                            print('ターゲットないから作成')
                            t = Target(user_id)

                        print('★★t.person', t.person)
                        
                        s.status = 3
                        t.target = msg_id
                        db.session.add(s)
                        db.session.add(t)

                        messages = [
                            create_search_confirm()
                            # create_text_res_format("検索します。よろしいでしょうか？")
                        ]

                        send_reply(replyToken, messages)

                        
                    elif s.status == 0:
                        # メニューを表示して操作してねと
                        messages = [
                            create_menu(),
                            create_text_res_format("メニューを操作してね")
                        ]

                        send_reply(replyToken, messages)

                    db.session.commit()

        elif event_type == 'postback':
            print('★ポストバックの処理')
            data = event['postback']['data']
            qs = {k:v[0] for k, v in urllib.parse.parse_qs(data).items()}
            action = qs['action']
            
            d = {
                '0': set_search_person_status,
                '1': set_search_target_image_status,
                '2': search,
                '99': init_status,
            }

            messages = d[action](user_id)
            
            if len(messages) != 0:
                send_reply(replyToken, messages)
            

            print('data', data)

    return {'statusCode': 200, 'body': '{}'}


if __name__ == "__main__":
	app.run()