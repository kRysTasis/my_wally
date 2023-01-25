from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from insightface.app import FaceAnalysis
from insightface.data import get_image as ins_get_image

from io import BytesIO
from datetime import timedelta
from PIL import Image

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import base64
import os
import requests
import json
import urllib.parse
import cloudinary
import cloudinary.uploader
import cv2
import numpy as np
import insightface

YOUR_CHANNEL_ACCESS_TOKEN = os.environ['YOUR_CHANNEL_ACCESS_TOKEN']
YOUR_CHANNEL_SECRET = os.environ['YOUR_CHANNEL_SECRET']

cloudinary.config(
    cloud_name = os.environ['CLOUD_NAME'],
    api_key = os.environ['CLOUDINARY_API_KEY'],
    api_secret = os.environ['CLOUDINARY_API_SECRET']
)

reply_url = 'https://api.line.me/v2/bot/message/reply'
image_url = 'https://api-data.line.me/v2/bot/message/{msg_id}/content'

app = Flask(__name__)

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


def read_image(path):
    """画像ファイルを読み込む関数"""
    
    image = np.array(Image.open(path).convert('RGB'))
    return image[:, :, [2, 1, 0]]


def compute_similarity(embedding1, embedding2):
    """類似度を出力する関数"""
    
    return np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )


def encode_np(array):
    bio = io.BytesIO()
    np.save(bio, array)
    return base64.standard_b64encode(bio.getvalue())


def decode_np(text):
    bio = io.BytesIO(base64.standard_b64decode(text))
    return np.load(bio)


def add_bboxes_to_image_top_three(ax, image,
                        bboxes,
                        line_width = 2,
                        border_color=(0, 1, 0, 1)) -> None:
    """バウンディングボックス描画のためのaxを作成する関数

    param image: dtype=np.uint8
    param bbox: [(x1, y1, x2, y2)]
    param label: List[str] or None
    
    
    ・指定座標（左上と右下の2点）
    
    #     y1                     
    # x1 |----------------------|
    #    |                      |
    #    |                      |
    #    |                      |
    #    |----------------------| y2
    #                        x2 
    
    return: ax
    """
    ax.imshow(image)

    border_color_list = [
        (0, 0, 0, 1), (255, 255, 0, 1), (100, 0, 100, 1)
    ]

    for i, bbox in enumerate(bboxes):
        x1, y1, x2, y2 = bbox
        rect = patches.Rectangle(
            (x1, y1),
            x2 - x1, y2 - y1,
            linewidth=line_width,
            edgecolor=border_color_list,
            facecolor='none')
        ax.add_patch(rect)

    return ax


def get_target_index(similarities):
    
    res = []
    for obj in similarities:
        for val, indexes in obj.items():
            target_index = indexed['index2']
            if len(res) == 0:
                res.append({val: target_index})
            elif len(res) == 1:
                if list(res[0].keys())[0] < val:
                    res.insert(0, {val: target_index})
                else:
                    res.append({val: target_index})
            elif len(res) == 2:
                if list(res[0].keys())[0] < val:
                    res.insert(0, {val: target_index})
                elif list(res[1].keys())[0] < val:
                    res.insert(1, {val: target_index})
                else:
                    res.append({val: target_index})
            elif len(res) >= 3:
                if list(res[0].keys())[0] < val:
                    res.insert(0, {val: target_index})
                elif list(res[1].keys())[0] < val:
                    res.insert(1, {val: target_index})
                elif list(res[2].keys())[0] < val:
                    res.insert(2, {val: target_index})
                else:
                    res.append({val: target_index})
                res.pop()
    return [list(i.values())[0] for i in res]


def get_faces(image):
    
    print('インスタンス化')
    face_analysis = insightface.app.FaceAnalysis()
    print('prepareする')
    face_analysis.prepare(ctx_id=0, det_size=(640, 640))
    print('getする')
    faces = face_analysis.get(image)
    
    return {
        "width": image.shape[1],
        "height": image.shape[0],
        "totalFaces": len(faces),
        "faces": [{
            "score": face.det_score.astype(float),
            "attributes": {"sex": face.sex, "age": face.age},
            "boundingBox": {
                "x1": face.bbox[0].astype(float),
                "y1": face.bbox[1].astype(float),
                "x2": face.bbox[2].astype(float),
                "y2": face.bbox[3].astype(float),
            },
            "embedding": encode_np(face.embedding),
            "keyPoints": [{
                "x": xy[0].astype(float),
                "y": xy[1].astype(float)
            } for xy in face.kps
            ],
            "landmarks": {
                "3d_68": [{
                    "x": xyz[0].astype(float),
                    "y": xyz[1].astype(float),
                    "z": xyz[2].astype(float),
                    }
                    for xyz in face.landmark_3d_68
                ],
                "2d_106": [{
                    "x": xy[0].astype(float),
                    "y": xy[1].astype(float)
                    }
                    for xy in face.landmark_2d_106
                ],
            },
        } for face in faces
    ]}


class Target(db.Model):
    __tablename__ = 'Target'
    user_id = db.Column(db.Text, primary_key=True)
    person = db.Column(db.Text)
    target = db.Column(db.Text)
    person_uri = db.Column(db.Text)
    target_uri = db.Column(db.Text)

    def __init__(
        self, 
        user_id,
        person = '',
        target = '',
        person_uri = '',
        target_uri = ''
    ):
        self.user_id = user_id
        self.person = person
        self.target = target
        self.person_uri = person_uri
        self.target_uri = target_uri


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

    reply = {'replyToken': reply_token, 'messages': messages}

    # ヘッダー作成
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(YOUR_CHANNEL_ACCESS_TOKEN)
    }

    # jsonでbotに返す
    requests.post(
        reply_url, data=json.dumps(reply), headers=headers
    )


def get_image(msg_id):

    url = image_url.format(msg_id=msg_id)

    # ヘッダー作成
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(YOUR_CHANNEL_ACCESS_TOKEN)
    }

    return requests.get(
        url, headers=headers
    )


def create_text_res_format(text):
    
    return {"type": "text", "text": text}


def create_search_confirm():

    return {
        "type": "template",
        "altText": "this is a confirm template",
        "template": {
            "type": "confirm",
            "text": "これらの画像の照合をします。よろしいでしょうか？",
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


def create_image_res_format(uri):
    
    return {"type": "image", "originalContentUrl": uri, "previewImageUrl": uri}


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

    print('照合処理結果')
    
    t = db.session.query(Target).get(user_id)
    
    print('msgidから画像読み込み')
    image1 = Image.open(BytesIO(get_image(t.person).content)).convert('RGB')
    image2 = Image.open(BytesIO(get_image(t.target).content)).convert('RGB')

    # print('urlから画像読み込み')
    # image1 = read_image(t.person_uri)
    # image2 = read_image(t.target_uri)

    image1 = np.array(image1)[:, :, [2, 1, 0]]
    image2 = np.array(image2)[:, :, [2, 1, 0]]

    print('insightfaceで認識させる')
    response1 = get_faces(image1)
    response2 = get_faces(image2)

    print('結果まとめる')
    embeddings1 = [face['embedding'] for face in response1['faces']]
    embeddings2 = [face['embedding'] for face in response2['faces']]
    embeddings = embeddings1 + embeddings2

    pairs = [{'index1':0, 'index2':i+1}  for i in range(len(embeddings2))]

    similarities = [
        {
            compute_similarity(
                decoded_embeddings[pair['index1']], decoded_embeddings[pair['index2']]
            ): pairs[i]
        }
        for i, pair in enumerate(pairs)
    ]
    
    print('indexゲット')
    # 画像2から3人まで確率が高い順でindexゲットしbbox描画
    target_index = get_target_index(similarities)

    # 描画する3人までのbboxリスト
    bboxes_list = []
    im_l = []
    bboxes_list = []
    label_list = []

    print('bboxes作成')
    for t_index in target_index:
        face = response2['faces'][t_index]
        bboxes = tuple(face['boundingBox'].values())
        bboxes_list.append(bboxes)

        # 認識した顔領域で分割画像作成
        im = image2.crop(bboxes)
        im_l.append(im)

        label_list.append(face['score'])

    print('バウンディングボックス描画')
    fig, ax = plt.subplots()
    add_bboxes_to_image_top_three(ax, np.uint8(image2), bboxes_list, 1.5)
    
    print('Matplotlibで画像として一旦保存')
    result_img = plt.savefig('result_img.jpeg')

    print('cloudinaryに保存')
    result_response = cloudinary.uploader.upload(file='result_img.jpeg')

    return [
        create_image_res_format(result_response['secure_url']),
        # create_image_res_format(uri1),
        create_text_res_format("照合処理実行結果"),
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

    body = request.json
    for event in body['events']:
        replyToken = event['replyToken']
        event_type = event['type']
        source = event['source']
        print(f'★EventType : {event_type}')
        user_id = source['userId']

        if event_type == 'message':
            message = event['message']
            msg_id = message['id']
            
            if message['type'] == 'text':
                text = message['text']
                messages = [
                    create_text_res_format("メニューを開きます。"),
                    create_menu()
                ]
                send_reply(replyToken, messages)

            elif message['type']  == 'image':
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

                        person_msg_id = t.person
                        target_msg_id = msg_id

                        print('画像読み込み')
                        person_img = Image.open(BytesIO(get_image(person_msg_id).content))
                        target_img = Image.open(BytesIO(get_image(target_msg_id).content))

                        person_file_name = f'person-{person_msg_id}.png'
                        target_file_name = f'target-{target_msg_id}.png'

                        print('Pillowで画像として一旦保存')
                        person_img.save(person_file_name)
                        target_img.save(target_file_name)

                        print('cloudinaryに保存')
                        person_result = cloudinary.uploader.upload(file=person_file_name, public_id=person_msg_id)
                        target_result = cloudinary.uploader.upload(file=target_file_name, public_id=target_msg_id)

                        t.person_uri = person_result['secure_url']
                        t.target_uri = target_result['secure_url']

                        db.session.add(s)
                        db.session.add(t)
                        db.session.commit()

                        messages = [
                            create_image_res_format(person_result['secure_url']),
                            create_image_res_format(target_result['secure_url']),
                            create_search_confirm()
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

    return {'statusCode': 200, 'body': '{}'}


if __name__ == "__main__":
	app.run()