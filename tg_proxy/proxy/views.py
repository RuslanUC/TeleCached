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

from json import JSONDecodeError, dumps, loads

import httpx
from django.conf import settings
from django.http import HttpResponse, HttpRequest, JsonResponse
from pydantic import ValidationError

from . import pydantic_models
from .models import Message, Chat, User
from .pydantic_models import GetMessageParams, GetMessagesParams, GetChatsParams, GetUserParams
from .utils import check_token, find_dict, PyrogramBot


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
    return JsonResponse({"ok": True, "result": loads(message.serialized_message)})


def get_messages_view(request: HttpRequest, bot_token: str) -> HttpResponse:
    try:
        args = GetMessagesParams(**request.GET.dict())
    except ValidationError:
        return JsonResponse({"ok": False, "error_code": 400, "description": f"Bad Request: invalid parameters"}, status=400)
    if (resp := check_token(bot_token)) is not None:
        return resp
    messages = Message.objects.filter(
        chat_id=args.chat_id, bot_id=bot_token.split(":")[0], message_id__gt=args.after, message_id__lt=args.before
    ).order_by("-message_id")[:args.limit]
    messages_json = [loads(message.serialized_message) for message in messages]
    return JsonResponse({"ok": True, "result": messages_json}, safe=False)


def get_chats_view(request: HttpRequest, bot_token: str) -> HttpResponse:
    try:
        args = GetChatsParams(**request.GET.dict())
    except ValidationError:
        return JsonResponse({"ok": False, "error_code": 400, "description": f"Bad Request: invalid parameters"}, status=400)
    if (resp := check_token(bot_token)) is not None:
        return resp
    chats = Chat.objects.filter(
        bot_id=bot_token.split(":")[0], id__gt=args.after, id__lt=args.before, **{"type": args.type} if args.type else {}
    ).order_by("-id")[:args.limit]
    chats_json = [loads(chat.serialized_chat) for chat in chats]
    return JsonResponse({"ok": True, "result": chats_json}, safe=False)


def get_user_view(request: HttpRequest, bot_token: str) -> HttpResponse:
    try:
        args = GetUserParams(**request.GET.dict())
    except ValidationError:
        return JsonResponse({"ok": False, "error_code": 400, "description": f"Bad Request: invalid parameters"}, status=400)
    if (resp := check_token(bot_token)) is not None:
        return resp
    user = User.objects.filter(id=args.user_id).first()
    return JsonResponse({"ok": True, "result": loads(user.serialized_user) if user is not None else None}, safe=False)


def set_webhook_view(request: HttpRequest, bot_token: str) -> HttpResponse:
    return JsonResponse({"ok": False, "error_code": 501, "description": "This method is not implemented yet."}, status=501)


def get_webhook_view(request: HttpRequest) -> HttpResponse:
    return JsonResponse({"ok": False, "error_code": 501, "description": "This method is not implemented yet."}, status=501)


def del_webhook_view(request: HttpRequest) -> HttpResponse:
    return JsonResponse({"ok": False, "error_code": 501, "description": "This method is not implemented yet."}, status=501)


def proxy_view(request: HttpRequest, bot_token: str, method: str) -> HttpResponse:
    bot_id = int(bot_token.split(":")[0])
    if method.startswith("send") and hasattr(PyrogramBot, method) and (api_id := getattr(settings, "TG_API_ID", None)) \
            and (api_hash := getattr(settings, "TG_API_HASH", None)) and request.GET.get("is_big", "false") == "true":
        bot = PyrogramBot(bot_token, api_id, api_hash)
        func = getattr(bot, method)
        if message := func(request):
            raw_message = message["raw_message"]
            del message["raw_message"]
            Message.update_or_create_objects("message_id", bot_id, [message], lambda d: {
                "chat_id": d["chat"]["id"], "bot_id": bot_token.split(":")[0],
                "message_thread_id": d.get("message_thread_id", None),
                "reply_to_message_id": d.get("reply_to_message", {}).get("message_id"),
                "from_peer": d.get("from", {}).get("id"), "serialized_message": dumps(d),
            })
            response = {"ok": True, "result": message}
            if request.GET.get("with_raw", "false") == "true":
                response["raw"] = raw_message
            return JsonResponse(response)

    headers = {}
    for header in ("User-Agent", "Content-Type", "Accept"):
        if header in request.headers:
            headers[header] = request.headers[header]
    try:
        if request.method == "GET":
            resp = httpx.get(f"https://api.telegram.org/bot{bot_token}/{method}", params=request.GET,
                             headers=headers)
        elif request.method == "POST":
            resp = httpx.post(f"https://api.telegram.org/bot{bot_token}/{method}", params=request.GET, data=request.body,
                              headers=headers)
        else:
            return JsonResponse({"ok": False, "error_code": 405, "description": f"Method {request.method} is not allowed."}, status=405)
    except Exception as e:
        return JsonResponse({"ok": False, "error_code": 500, "description": f"Failed to make request to origin server: {e}"}, status=500)

    headers = dict(resp.headers)
    found = {}
    try:
        find_dict(resp.json(), found, pydantic_models.Message, pydantic_models.Chat, pydantic_models.User)
    except JSONDecodeError:
        pass
    for model, dicts in found.items():
        if model is pydantic_models.Message:
            Message.update_or_create_objects("message_id", bot_id, dicts, lambda d: {
                "chat_id": d["chat"]["id"], "bot_id": bot_id,
                "message_thread_id": d.get("message_thread_id", None),
                "reply_to_message_id": d.get("reply_to_message", {}).get("message_id"),
                "from_peer": d.get("from", {}).get("id"), "serialized_message": dumps(d),
            })
        elif model is pydantic_models.Chat:
            Chat.update_or_create_objects("id", bot_id, dicts, lambda d: {
                "bot_id": bot_id, "type": d["type"], "serialized_chat": dumps(d),
            })
        elif model is pydantic_models.User:
            User.update_or_create_objects("id", bot_id, dicts, lambda d: {
                "username": d.get("username", None), "first_name": d["first_name"],
                "last_name": d.get("last_name", None), "serialized_user": dumps(d),
            })

    for hbh_header in ("connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers",
                       "transfer-encoding", "upgrade"):  # Remove hop-by-hop headers
        if hbh_header in headers: del headers[hbh_header]
    return HttpResponse(resp.content, status=resp.status_code, headers=headers)
