"""
The MIT License (MIT)

Copyright (c) 2023-present RuslanUC

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import asyncio
import re
from io import BytesIO
from json import JSONDecodeError, loads
from typing import Optional, Any, Union

import httpx
from django.http import HttpResponse, JsonResponse, HttpRequest
from pydantic import ValidationError
from pyrogram import Client
from pyrogram.types import Message, Document, Audio, Thumbnail, Photo, Video, VideoNote, Voice, Animation

from proxy.exceptions import RequestEntityTooLargeException, NoMediaException
from proxy.models import BotSession


def check_token(token: str) -> Optional[HttpResponse]:
    resp = httpx.get(f"https://api.telegram.org/bot{token}/getMe")
    if resp.status_code != 200:
        try:
            j = resp.json()
        except JSONDecodeError:
            j = {"description": "Unknown error."}
        return JsonResponse({"ok": False, "error_code": resp.status_code,
                             "description": f"Telegram Bot Api server returned an error: {j['description']}"},
                            status=resp.status_code)


def find_dict(d: Any, found: dict, *models: type) -> None:
    if isinstance(d, dict):
        for model in models:
            if model not in found: found[model] = []
            try:
                _ = model(**d)
                found[model].append(d)
            except ValidationError:
                pass
        return find_dict(list(d.values()), found, *models)
    elif isinstance(d, list):
        for item in d:
            find_dict(item, found, *models)


def get_file_url(url: str) -> Optional[BytesIO]:
    resp = httpx.get(url)
    if resp.headers.get("Content-Lenght", 0) > 100 * 1024 * 1024:
        raise RequestEntityTooLargeException(413, "Request Entity Too Large")
    io = BytesIO(resp.content)
    setattr(io, "name", url.split("/")[-1])
    return io


URL_REGEX = r'^(https?:\/\/)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/\/=]*)$'

def get_file(request: HttpRequest, name: str) -> Optional[BytesIO]:
    file = request.GET.get(name)
    if file:
        if re.match(URL_REGEX, file):
            return get_file_url(file)
        return file
    if request.method != "POST" or name not in request.FILES:
        return
    file = request.FILES[name]
    if file.size > 100 * 1024 * 1024:
        raise RequestEntityTooLargeException(413, "Request Entity Too Large")
    io = BytesIO(file.read())
    setattr(io, "name", file.name)
    return io


class MessageUtils:
    def __init__(self, message: Message):
        self._message = message
        self._result: dict = None

    def _set_base_data(self) -> None:
        message = self._message
        self._result: dict = {
            "message_id": message.id,
            "date": int(message.date.timestamp()),
            "raw_message": loads(str(message))
        }
        if message.chat.type.value == "private":
            self._result["chat"] = {
                "id": message.chat.id,
                "first_name": message.chat.first_name,
                "username": message.chat.username,
                "type": "private",
            }
        elif message.chat.type.value in ("group", "supergroup", "channel"):
            self._result["chat"] = {
                "id": message.chat.id,
                "title": message.chat.title,
                "type": message.chat.type.value,
            }
            if message.chat.username:
                self._result["chat"]["username"] = message.chat.username

        if message.from_user:
            self._result["from"] = {
                "id": message.from_user.id,
                "is_bot": message.from_user.is_bot,
                "first_name": message.from_user.first_name,
                "username": message.from_user.username
            }
        if message.sender_chat:
            self._result["sender_chat"] = self._result["chat"]
        if message.caption:
            self._result["caption"] = message.caption

    def _set_thumb(self, thumb: Union[Thumbnail, Photo]) -> dict:
        return {
            "file_id": thumb.file_id,
            "file_unique_id": thumb.file_unique_id,
            "width": thumb.width,
            "height": thumb.height,
            "file_size": thumb.file_size,
        }

    def _set_document(self, document: Union[Document, Audio, Photo, Video, VideoNote, Voice, Animation],
                      base: dict=None) -> None:
        if base is None:
            base = self._result["document"]
        if document.file_name: base["file_name"] = document.file_name
        if document.file_size: base["file_size"] = document.file_size
        if document.mime_type: base["mime_type"] = document.mime_type
        if document.thumbs: base["thumbnail"] = self._set_thumb(document.thumbs[0])

    def _set_audio(self, audio: Audio) -> None:
        self._result["audio"]["duration"] = audio.duration
        self._set_document(audio, self._result["audio"])

    def _set_photo(self, photo: Photo) -> None:
        self._result["photo"] = []
        for ph in [photo] + (photo.thumbs if photo.thumbs else []):
            self._result["photo"].append(self._set_thumb(ph))

    def _set_video(self, video: Video) -> None:
        self._result["video"]["width"] = video.width
        self._result["video"]["height"] = video.height
        self._result["video"]["duration"] = video.duration
        self._set_document(video, self._result["video"])

    def _set_video_note(self, video_note: VideoNote) -> None:
        self._result["video_note"]["length"] = video_note.length
        self._result["video_note"]["duration"] = video_note.duration
        self._set_document(video_note, self._result["video_note"])

    def _set_voice(self, voice: Voice) -> None:
        self._result["voice"]["duration"] = voice.duration
        self._set_document(voice, self._result["voice"])

    def _set_animation(self, animation: Animation) -> None:
        self._result["animation"]["width"] = animation.width
        self._result["animation"]["height"] = animation.height
        self._result["animation"]["duration"] = animation.duration
        self._set_document(animation, self._result["animation"])

    def to_json(self, media: str) -> Optional[dict]:
        if self._result is not None: return self._result
        self._set_base_data()
        if self._result is None: return
        message = self._message
        if not (m := getattr(message, media)) or media not in ("document", "photo", "audio", "video", "video_note",
                                                               "voice", "animation"):
            return self._result

        self._result[media] = {
            "file_id": m.file_id,
            "file_unique_id": m.file_unique_id
        }
        func = getattr(self, f"_set_{media}")
        func(m)

        return self._result


class PyrogramBot:
    def __init__(self, token: str, api_id: int, api_hash: str):
        self._token = token
        self._api_id = api_id
        self._api_hash = api_hash

    def _upload(self, media: str, args: dict) -> Optional[dict]:
        asyncio.set_event_loop(asyncio.new_event_loop())
        bot_id = self._token.split(":")[0]
        client_args = {
            "bot_token": self._token,
            "api_id": self._api_id,
            "api_hash": self._api_hash,
            "no_updates": True,
            "name": bot_id,
            "in_memory": True,
        }
        bot_session = BotSession.objects.filter(bot_id=bot_id).first()
        create_session = True
        if bot_session is not None:
            create_session = False
            client_args["session_string"] = bot_session.session_string
        with Client(**client_args) as bot:
            if create_session:
                BotSession.update_or_create_objects(
                    "bot_id",
                    [{"bot_id": self._token.split(":")[0], "session_string": bot.export_session_string()}],
                    lambda d: d
                )
            func = getattr(bot, f"send_{media}")
            message: Message = func(**args)
            return MessageUtils(message).to_json(media)

    def _req_to_json(self, request: HttpRequest) -> dict:
        return {
            "chat_id": int(request.GET.get("chat_id")),
            "disable_notification": request.GET.get("disable_notification", None),
            "reply_to_message_id": request.GET.get("message_thread_id", request.GET.get("reply_to_message_id", None)),
            "schedule_date": None,
            "protect_content": request.GET.get("protect_content", None),
            "reply_markup": loads(request.GET.get("reply_markup", None)) if request.GET.get("reply_markup",
                                                                                            None) else None,
        }

    def sendDocument(self, request: HttpRequest) -> Optional[dict]:
        if not (document := get_file(request, "document")):
            raise NoMediaException(400, "Bad Request: there is no document in the request")
        thumb = get_file(request, "thumbnail")
        args = self._req_to_json(request)
        args["document"] = document
        args["thumb"] = thumb
        args["caption"] = request.GET.get("caption", None)
        args["parse_mode"] = request.GET.get("parse_mode", None)
        return self._upload("document", args)

    def sendAudio(self, request: HttpRequest) -> Optional[dict]:
        if not (audio := get_file(request, "audio")):
            raise NoMediaException(400, "Bad Request: there is no audio in the request")
        thumb = get_file(request, "thumbnail")
        args = self._req_to_json(request)
        args["audio"] = audio
        args["thumb"] = thumb
        args["caption"] = request.GET.get("caption", None)
        args["parse_mode"] = request.GET.get("parse_mode", None)
        args["duration"] = request.GET.get("duration", None)
        args["performer"] = request.GET.get("performer", None)
        args["title"] = request.GET.get("title", None)
        return self._upload("audio", args)

    def sendPhoto(self, request: HttpRequest) -> Optional[dict]:
        if not (photo := get_file(request, "photo")):
            raise NoMediaException(400, "Bad Request: there is no photo in the request")
        args = self._req_to_json(request)
        args["photo"] = photo
        args["caption"] = request.GET.get("caption", None)
        args["parse_mode"] = request.GET.get("parse_mode", None)
        args["has_spoiler"] = request.GET.get("has_spoiler", None)
        return self._upload("photo", args)

    def sendVideo(self, request: HttpRequest) -> Optional[dict]:
        if not (video := get_file(request, "video")):
            raise NoMediaException(400, "Bad Request: there is no video in the request")
        thumb = get_file(request, "thumbnail")
        args = self._req_to_json(request)
        args["video"] = video
        args["thumb"] = thumb
        args["caption"] = request.GET.get("caption", None)
        args["parse_mode"] = request.GET.get("parse_mode", None)
        args["duration"] = request.GET.get("duration", None)
        args["width"] = request.GET.get("width", None)
        args["height"] = request.GET.get("height", None)
        args["title"] = request.GET.get("title", None)
        args["has_spoiler"] = request.GET.get("has_spoiler", None)
        return self._upload("video", args)

    def sendVideoNote(self, request: HttpRequest) -> Optional[dict]:
        if not (video_note := get_file(request, "video_note")):
            raise NoMediaException(400, "Bad Request: there is no video_note in the request")
        thumb = get_file(request, "thumbnail")
        args = self._req_to_json(request)
        args["video_note"] = video_note
        args["thumb"] = thumb
        args["duration"] = request.GET.get("duration", None)
        args["length"] = request.GET.get("length", None)
        return self._upload("video_note", args)

    def sendVoice(self, request: HttpRequest) -> Optional[dict]:
        if not (voice := get_file(request, "voice")):
            raise NoMediaException(400, "Bad Request: there is no voice in the request")
        args = self._req_to_json(request)
        args["voice"] = voice
        args["caption"] = request.GET.get("caption", None)
        args["parse_mode"] = request.GET.get("parse_mode", None)
        args["duration"] = request.GET.get("duration", None)
        return self._upload("voice", args)

    def sendAnimation(self, request: HttpRequest) -> Optional[dict]:
        if not (animation := get_file(request, "animation")):
            raise NoMediaException(400, "Bad Request: there is no animation in the request")
        thumb = get_file(request, "thumbnail")
        args = self._req_to_json(request)
        args["animation"] = animation
        args["thumb"] = thumb
        args["caption"] = request.GET.get("caption", None)
        args["parse_mode"] = request.GET.get("parse_mode", None)
        args["duration"] = request.GET.get("duration", None)
        args["width"] = request.GET.get("width", None)
        args["height"] = request.GET.get("height", None)
        args["has_spoiler"] = request.GET.get("has_spoiler", None)
        return self._upload("animation", args)
