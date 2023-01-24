from dataclasses import dataclass

from linebot.models import (
    MessageEvent,
    TextSendMessage,
    ImageSendMessage,
    TemplateSendMessage
)


@dataclass
class HandleMessageService:
    
    @classmethod
    def create_reply_message(
            cls,
            event: MessageEvent):
        """eventによりリプライの内容を生成する"""

        msg_id = event.message.id
        print('msg_id', msg_id)

        # reply = line_bot_api.reply_message(
        #     event.reply_token,
        #     TextSendMessage(text='test message')
        # )

        # reply = ImageSendMessage(
        #     original_content_url='https://example.com/original.jpg',
        #     preview_image_url='https://example.com/preview.jpg'
        # )


        reply = TemplateSendMessage(
            alt_text='Carousel template',
            template=CarouselTemplate(
                columns=[
                    CarouselColumn(
                        thumbnail_image_url='https://example.com/item1.jpg',
                        title='this is menu1',
                        text='description1',
                        actions=[
                            PostbackAction(
                                label='postback1',
                                display_text='postback text1',
                                data='action=buy&itemid=1'
                            ),
                            MessageAction(
                                label='message1',
                                text='message text1'
                            ),
                            URIAction(
                                label='uri1',
                                uri='http://example.com/1'
                            )
                        ],
                        default_action=[
                            URIAction(
                                label="uri1".,
                                uri='http://example.com/1'
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://example.com/item2.jpg',
                        title='this is menu2',
                        text='description2',
                        actions=[
                            PostbackAction(
                                label='postback2',
                                display_text='postback text2',
                                data='action=buy&itemid=2'
                            ),
                            MessageAction(
                                label='message2',
                                text='message text2'
                            ),
                            URIAction(
                                label='uri2',
                                uri='http://example.com/2'
                            )
                        ],
                        default_action=[
                            URIAction(
                                label="uri1".,
                                uri='http://example.com/1'
                        ]
                    )
                ]
            )
        )

        return reply