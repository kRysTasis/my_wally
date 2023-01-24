from flask import session
from dataclasses import dataclass

from linebot.models import (
    MessageEvent,
    TextSendMessage,
    ImageSendMessage,
    TemplateSendMessage,
    FlexSendMessage,
)


@dataclass
class HandlePostbackService:
    
    @classmethod
    def create_reply_message(
            cls,
            event: MessageEvent):
        """eventによりリプライの内容を生成する"""

        msg_id = event.message.id
        print('msg_id', msg_id)
        data = event.events[0].postback.data
        print('data', data)

        reply = line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='test message')
        )

        # reply = TemplateSendMessage(
        #     alt_text='Buttons template',
        #     template=ButtonsTemplate(
        #         thumbnail_image_url='https://example.com/image.jpg',
        #         title='Menu',
        #         text='Please select',
        #         actions=[
        #             PostbackAction(
        #                 label='postback',
        #                 display_text='postback text',
        #                 data='action=buy&itemid=1'
        #             ),
        #             MessageAction(
        #                 label='message',
        #                 text='message text'
        #             ),
        #             URIAction(
        #                 label='uri',
        #                 uri='http://example.com/'
        #             )
        #         ]
        #     )
        # )

        return reply