from flask import Flask, render_template, request
import os
import json
import requests
import datetime
import hashlib
import hmac
import base64
import re
import configparser
import urllib.parse

YOUR_CHANNEL_ACCESS_TOKEN = os.environ['YOUR_CHANNEL_ACCESS_TOKEN']
YOUR_CHANNEL_SECRET = os.environ['YOUR_CHANNEL_SECRET']

reply_url = 'https://api.line.me/v2/bot/message/reply'

app = Flask(__name__)

@app.route('/')
def index():
    return "index"

@app.route('/callback', methods=['POST'])
def callback():
    body = request.body
    text_body = body.read().decode('UTF-8')

    # チャンネルシークレットを秘密鍵に、
    # HMAC-SHA256アルゴリズムでリクエストボディのダイジェスト値取得
    hash = hmac.new(
        YOUR_CHANNEL_SECRET.encode('utf-8'),
        text_body.encode('utf-8'),
        hashlib.sha256).digest()


    # ダイジェスト値をBase64エンコードしてUTF-8でデコード
    signature = base64.b64encode(hash).decode('utf-8')


    # リクエストヘッダーとsignatureの値が正しいか判定し、
    # line以外からのアクセスの場合強制終了させる
    if signature != request.get_header('X-Line-signature'):
        abort(400)
    # -------------------------------------------

    print(request)
    print(request.json)
    print(request.body)

    return {'statusCode': 200, 'body': '{}'}

# if __name__ == '__main__':
#     app.run()