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
from functools import wraps

from django.http import JsonResponse, HttpResponse
from django.urls import path

from proxy.exceptions import BaseProxyException
from proxy.views import set_webhook_view, del_webhook_view, get_webhook_view, proxy_view, get_message_view, \
    get_messages_view, get_chats_view, get_user_view


def handle_proxy_exception(view):
    @wraps(view)
    def exc_handler(*args, **kwargs) -> HttpResponse:
        try:
            return view(*args, **kwargs)
        except BaseProxyException as e:
            return JsonResponse({"ok": False, "error_code": e.code, "message": e.message}, status=e.code)
    return exc_handler


urlpatterns = [
    path("bot<str:bot_token>/getMessage", get_message_view),
    path("bot<str:bot_token>/getMessages", get_messages_view),
    path("bot<str:bot_token>/getChats", get_chats_view),
    path("bot<str:bot_token>/getUser", get_user_view),
    path("bot<str:bot_token>/setWebhook", set_webhook_view),
    path("bot<str:bot_token>/deleteWebhook", del_webhook_view),
    path("bot<str:bot_token>/getWebhookInfo", get_webhook_view),
    path("bot<str:bot_token>/<str:method>", handle_proxy_exception(proxy_view)),
]