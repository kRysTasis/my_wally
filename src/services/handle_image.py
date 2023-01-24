from dataclasses import dataclass

from linebot.models import (
    MessageEvent, TextSendMessage, ImageSendMessage
)


@dataclass
class HandleImageService:
    
    @classmethod
    def create_reply_message(
            cls,
            event: MessageEvent):
        """リプライの内容を生成する"""

        msg_id = event.message.id
        print('msg_id', msg_id)

        # reply = TextSendMessage(
        #     text='画像ありがと'
        # )

        # reply = ImageSendMessage(
        #     original_content_url='https://example.com/original.jpg',
        #     preview_image_url='https://example.com/preview.jpg'
        # )

        reply = TemplateSendMessage(
            alt_text='ImageCarousel template',
            template=ImageCarouselTemplate(
                columns=[
                    ImageCarouselColumn(
                        image_url='https://example.com/item1.jpg',
                        action=PostbackAction(
                            label='postback1',
                            display_text='postback text1',
                            data='action=buy&itemid=1'
                        )
                    ),
                    ImageCarouselColumn(
                        image_url='https://example.com/item2.jpg',
                        action=PostbackAction(
                            label='postback2',
                            display_text='postback text2',
                            data='action=buy&itemid=2'
                        )
                    )
                ]
            )
        )

        return reply