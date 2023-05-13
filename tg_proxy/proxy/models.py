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

from django.db import models

class BaseModel(models.Model):
    class Meta:
        abstract = True

    def __str__(self) -> str:
        return repr(self)

    @classmethod
    def update_or_create_objects(cls, id_field_name: str, objects: list[dict], defaults_func) -> None:
        pk_name = cls._meta.pk.name
        for obj in objects:
            cls.objects.update_or_create(**{pk_name: obj[id_field_name]}, defaults=defaults_func(obj))

class Message(BaseModel):
    message_id: int = models.BigIntegerField(primary_key=True)
    chat_id: int = models.BigIntegerField()
    bot_id: int = models.BigIntegerField()
    message_thread_id: int = models.BigIntegerField(default=None, null=True)
    reply_to_message_id: int = models.BigIntegerField(default=None, null=True)
    from_peer: int = models.BigIntegerField(default=None, null=True)
    serialized_message: str = models.TextField()

    def __repr__(self) -> str:
        return f"Message(message_id={self.message_id!r}, bot_id={self.bot_id!r}, chat_id={self.chat_id!r}, " \
               f"from_id={self.from_peer!r})"


class User(BaseModel):
    id: int = models.BigIntegerField(primary_key=True)
    username: str = models.CharField(max_length=128, default=None, null=True)
    first_name: str = models.CharField(max_length=128)
    last_name: str = models.CharField(max_length=128, default=None, null=True)
    serialized_user: str = models.TextField()

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, username={self.username!r}, first_name={self.first_name!r}, " \
               f"last_name={self.last_name!r})"


class Chat(BaseModel):
    id: int = models.BigIntegerField(primary_key=True)
    bot_id: int = models.BigIntegerField()
    type: str = models.CharField(max_length=16)
    serialized_chat: str = models.TextField()

    def __repr__(self) -> str:
        return f"Chat(id={self.id!r}, bot_id={self.bot_id!r}, type={self.type!r})"


class ChatMember(BaseModel):
    user_id: int = models.BigIntegerField()
    chat_id: int = models.BigIntegerField()
    bot_id: int = models.BigIntegerField()

    def __repr__(self) -> str:
        return f"ChatMember(user_id={self.user_id!r}, chat_id={self.chat_id!r}, bot_id={self.bot_id!r})"


class Webhook(BaseModel):
    bot_id: int = models.BigIntegerField(primary_key=True)
    url: str = models.CharField(max_length=1024)
    allowed_updates: str = models.TextField()
    secret_token: str = models.TextField()

    def __repr__(self) -> str:
        return f"Webhook(bot_id={self.bot_id!r}"

