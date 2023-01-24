from dataclasses import dataclass

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
)


@dataclass
class HandleImage:
    
    @classmethod
    def create_reply_message(
            cls,
            event: MessageEvent):
        """リプライの内容を生成する"""

        msg_id = event.message.id
        print('msg_id', msg_id)

        reply = line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='画像ありがと')
        )

        # reply = ImageSendMessage(
        #     original_content_url='https://example.com/original.jpg',
        #     preview_image_url='https://example.com/preview.jpg'
        # )

        return reply