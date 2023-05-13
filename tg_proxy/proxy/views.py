"""
The MIT License (MIT)

Copyright (c) 2021-present RuslanUC

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

from json import JSONDecodeError, dumps, loads
from typing import Any, Optional

import httpx
from django.http import HttpResponse, HttpRequest, JsonResponse
from pydantic import ValidationError

from . import pydantic_models
from .models import Message, Chat, User
from .pydantic_models import GetMessageParams, GetMessagesParams


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


def get_message_view(request: HttpRequest, bot_token: str) -> HttpResponse:
    try:
        args = GetMessageParams(**request.GET.dict())
    except ValidationError:
        return JsonResponse({"ok": False, "error_code": 400, "description": f"Bad Request: invalid parameters"}, status=400)
    if (resp := check_token(bot_token)) is not None:
        return resp
    message = Message.objects.filter(message_id=args.message_id, bot_id=bot_token.split(":")[0]).first()
    if message is None:
        return JsonResponse({"ok": False, "error_code": 400, "description": "Bad Request: message not found"},
                            status=404)
    return JsonResponse(loads(message.serialized_message))


def get_messages_view(request: HttpRequest, bot_token: str) -> HttpResponse:
    try:
        args = GetMessagesParams(**request.GET.dict())
    except ValidationError as e:
        return JsonResponse({"ok": False, "error_code": 400, "description": f"Bad Request: invalid parameters"}, status=400)
    if (resp := check_token(bot_token)) is not None:
        return resp
    messages = Message.objects.filter(
        chat_id=args.chat_id, bot_id=bot_token.split(":")[0], message_id__gt=args.after, message_id__lt=args.before
    ).order_by("-message_id")[:args.limit]
    messages_json = [loads(message.serialized_message) for message in messages]
    return JsonResponse(messages_json, safe=False)


def set_webhook_view(request: HttpRequest, bot_token: str) -> HttpResponse:
    return JsonResponse({"ok": False, "error_code": 501, "description": "This method is not implemented yet."}, status=501)


def get_webhook_view(request: HttpRequest) -> HttpResponse:
    return JsonResponse({"ok": False, "error_code": 501, "description": "This method is not implemented yet."}, status=501)


def del_webhook_view(request: HttpRequest) -> HttpResponse:
    return JsonResponse({"ok": False, "error_code": 501, "description": "This method is not implemented yet."}, status=501)


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


def proxy_view(request: HttpRequest, bot_token: str, method: str) -> HttpResponse:
    if request.method == "GET":
        resp = httpx.get(f"https://api.telegram.org/bot{bot_token}/{method}", params=request.GET)
        headers = dict(resp.headers)
        found = {}
        try:
            find_dict(resp.json(), found, pydantic_models.Message, pydantic_models.Chat, pydantic_models.User)
        except JSONDecodeError:
            pass
        for model, dicts in found.items():
            if model is pydantic_models.Message:
                Message.update_or_create_objects("message_id", dicts, lambda d: {
                    "chat_id": d["chat"]["id"], "bot_id": bot_token.split(":")[0],
                    "message_thread_id": d.get("message_thread_id", None),
                    "reply_to_message_id": d.get("reply_to_message", {}).get("message_id"),
                    "from_peer": d.get("from", {}).get("id"), "serialized_message": dumps(d),
                })
            elif model is pydantic_models.Chat:
                Chat.update_or_create_objects("id", dicts, lambda d: {
                    "bot_id": bot_token.split(":")[0], "type": d["type"], "serialized_chat": dumps(d),
                })
            elif model is pydantic_models.User:
                User.update_or_create_objects("id", dicts, lambda d: {
                    "username": d.get("username", None), "first_name": d["first_name"],
                    "last_name": d.get("last_name", None), "serialized_user": dumps(d),
                })

        for hbh_header in ("connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers",
                           "transfer-encoding", "upgrade"): # Remove hop-by-hop headers
            if hbh_header in headers: del headers[hbh_header]
        return HttpResponse(resp.content, status=resp.status_code, headers=headers)
    return HttpResponse()
