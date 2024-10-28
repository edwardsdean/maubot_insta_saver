import os
import re
from typing import Type
import urllib.parse
from mautrix.types import EventType, TextMessageEventContent, MessageType
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import event


instagram_pattern = re.compile(r"((?:https?:)\/\/)?((?:www)\.)?((?:instagram\.com))\/?([a-zA-Z0-9\.\_\-]+)?\/(p|reel|tv|stories)+?\/([a-zA-Z0-9\-\_\.]+)\/?([0-9]+)?")


def remove_prefixs(text, prefixs):
    for prefix in prefixs:
        if text.lower().startswith(prefix):
            text = text[len(prefix):]
    return text


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("local_http_path")
        helper.copy("domain")
        helper.copy("x-rapidapi-host")
        helper.copy("x-rapidapi-key")


class InstaSaverPlugin(Plugin):
    async def start(self) -> None:
        await super().start()
        self.config.load_and_update()

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config

    @event.on(EventType.ROOM_MESSAGE)
    async def on_message(self, evt: MessageEvent) -> None:
        if evt.content.msgtype != MessageType.TEXT or evt.sender == '@stralia1_bot:matrix.org' or evt.sender == '@cummiesbot:matrix.org':
            return

        if evt.content.body.startswith("!") or evt.content.body.startswith("."):
            return

        for url_tup in instagram_pattern.findall(evt.content.body):
            await evt.mark_read()

            api_key = self.config["x-rapidapi-key"]

            self.log.info(url_tup)
            content_type = url_tup[4]
            self.log.info(content_type)

            short_code = url_tup[5]
            self.log.info(short_code)

            if content_type == 'reel':
                print("reel")

                url = f'https://{self.config["x-rapidapi-host"]}/v1/post_info?code_or_id_or_url={short_code}'
                headers = {
                    'x-rapidapi-host': self.config["x-rapidapi-host"],
                    'x-rapidapi-key': self.config["x-rapidapi-key"]
                }

                try:
                    response = await self.http.get(url, headers=headers)
                    resp_json = await response.json()
                except Exception as e:
                    await evt.respond(f"request failed: {e.message}")
                    return None
                try:
                    self.log.info(resp_json)
                    video_url = resp_json['data']['video_versions'][0]['url']
                    self.log.info(video_url)

                    # save to local disk
                    self.log.info(os.listdir(self.config["local_http_path"]))

                    file_path = self.config["local_http_path"] + short_code + '.mp4'
                    link = self.config["domain"] + short_code + '.mp4'

                    urllib.request.urlretrieve(video_url, file_path)

                    message = link

                    await evt.reply(content=TextMessageEventContent(msgtype=MessageType.TEXT, body=message))

                except Exception as e:
                    message = "No results, failed to parse API results"
                    await evt.reply(content=TextMessageEventContent(msgtype=MessageType.TEXT, body=message))
                    self.log.exception(e)
                    return None
# Photo reels
            elif content_type == 'p':
                print('photos')
                url = f'https://{self.config["x-rapidapi-host"]}/v1/post_info?code_or_id_or_url={short_code}'
                headers = {
                    'x-rapidapi-host': self.config["x-rapidapi-host"],
                    'x-rapidapi-key': self.config["x-rapidapi-key"]
                }

                try:
                    response = await self.http.get(url, headers=headers)
                    resp_json = await response.json()
                except Exception as e:
                    await evt.respond(f"request failed: {e.message}")
                    return None
                try:
                    self.log.info(resp_json)
                    pictures = resp_json['data']['carousel_media']
                    self.log.info(pictures)

                    pic_num = 1
                    message = ''
                    for picture in pictures:
                        picture_url = picture['image_versions']['items'][0]['url']
                        # save to local disk
                        self.log.info(os.listdir(self.config["local_http_path"]))

                        file_path = self.config["local_http_path"] + short_code + '_' + str(pic_num) + '.jpg'
                        link = self.config["domain"] + short_code + '_' + str(pic_num) + '.jpg'

                        urllib.request.urlretrieve(picture_url, file_path)

                        if pic_num != int(resp_json['data']['carousel_media_count']):
                            message = message + link + '\n'
                        else:
                            message = message + link

                        pic_num += 1

                    await evt.reply(content=TextMessageEventContent(msgtype=MessageType.TEXT, body=message))

                except Exception as e:
                    message = "No results, failed to parse API results"
                    await evt.reply(content=TextMessageEventContent(msgtype=MessageType.TEXT, body=message))
                    self.log.exception(e)
                    return None
            else:
                print("unknown type")
                message = "Unknown type, failed to parse API results"
                await evt.reply(content=TextMessageEventContent(msgtype=MessageType.TEXT, body=message))
