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

from __future__ import annotations
from typing import Optional

from pydantic import BaseModel, validator
from pydantic.fields import Field


class User(BaseModel):
    id: int
    is_bot: bool
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None
    added_to_attachment_menu: Optional[bool] = None
    can_join_groups: Optional[bool] = None
    can_read_all_group_messages: Optional[bool] = None
    supports_inline_queries: Optional[bool] = None


class Chat(BaseModel):
    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_forum: Optional[bool] = None
    photo: Optional[dict] = None
    active_usernames: Optional[list[str]] = None
    emoji_status_custom_emoji_id: Optional[str] = None
    bio: Optional[str] = None
    has_private_forwards: Optional[bool] = None
    has_restricted_voice_and_video_messages: Optional[bool] = None
    join_to_send_messages: Optional[bool] = None
    join_by_request: Optional[bool] = None
    description: Optional[str] = None
    invite_link: Optional[str] = None
    pinned_message: Optional[Message] = None
    permissions: Optional[dict] = None
    slow_mode_delay: Optional[int] = None
    message_auto_delete_time: Optional[int] = None
    has_aggressive_anti_spam_enabled: Optional[bool] = None
    has_hidden_members: Optional[bool] = None
    has_protected_content: Optional[bool] = None
    sticker_set_name: Optional[str] = None
    can_set_sticker_set: Optional[bool] = None
    linked_chat_id: Optional[int] = None
    location: Optional[dict] = None


class Message(BaseModel):
    message_id: int
    date: int
    chat: Chat
    from_user: Optional[User] = Field(alias="from")
    message_thread_id: Optional[int] = None
    sender_chat: Optional[Chat] = None
    forward_from: Optional[User] = None
    forward_from_chat: Optional[Chat] = None
    forward_from_message_id: Optional[int] = None
    forward_signature: Optional[str] = None
    forward_sender_name: Optional[str] = None
    forward_date: Optional[int] = None
    is_topic_message: Optional[bool] = None
    is_automatic_forward: Optional[bool] = None
    reply_to_message: Optional[Message] = None
    via_bot: Optional[User] = None
    edit_date: Optional[int] = None
    has_protected_content: Optional[bool] = None
    media_group_id: Optional[str] = None
    author_signature: Optional[str] = None
    text: Optional[str] = None
    entities: Optional[list[dict]] = None
    animation: Optional[dict] = None
    audio: Optional[dict] = None
    document: Optional[dict] = None
    photo: Optional[list[dict]] = None
    sticker: Optional[dict] = None
    video: Optional[dict] = None
    video_note: Optional[dict] = None
    voice: Optional[dict] = None
    caption: Optional[str] = None
    caption_entities: Optional[list[dict]] = None
    has_media_spoiler: Optional[bool] = None
    contact: Optional[dict] = None
    dice: Optional[dict] = None
    game: Optional[dict] = None
    poll: Optional[dict] = None
    venue: Optional[dict] = None
    location: Optional[dict] = None
    new_chat_members: Optional[list[User]] = None
    left_chat_member: Optional[User] = None
    new_chat_title: Optional[str] = None
    new_chat_photo: Optional[list[dict]] = None
    delete_chat_photo: Optional[bool] = None
    group_chat_created: Optional[bool] = None
    supergroup_chat_created: Optional[bool] = None
    channel_chat_created: Optional[bool] = None
    message_auto_delete_timer_changed: Optional[dict] = None
    migrate_to_chat_id: Optional[int] = None
    migrate_from_chat_id: Optional[int] = None
    pinned_message: Optional[Message] = None
    invoice: Optional[dict] = None
    successful_payment: Optional[dict] = None
    user_shared: Optional[dict] = None
    chat_shared: Optional[dict] = None
    connected_website: Optional[str] = None
    write_access_allowed: Optional[dict] = None
    passport_data: Optional[dict] = None
    proximity_alert_triggered: Optional[dict] = None
    forum_topic_created: Optional[dict] = None
    forum_topic_edited: Optional[dict] = None
    forum_topic_closed: Optional[dict] = None
    forum_topic_reopened: Optional[dict] = None
    general_forum_topic_hidden: Optional[dict] = None
    general_forum_topic_unhidden: Optional[dict] = None
    video_chat_scheduled: Optional[dict] = None
    video_chat_started: Optional[dict] = None
    video_chat_ended: Optional[dict] = None
    video_chat_participants_invited: Optional[dict] = None
    web_app_data: Optional[dict] = None
    reply_markup: Optional[dict] = None

    class Config:
        allow_population_by_field_name = True


class GetMessageParams(BaseModel):
    message_id: int


class GetMessagesParams(BaseModel):
    chat_id: int
    limit: int = 100
    before: int = 2**63 - 1
    after: int = 0

    @validator("limit")
    def validate_limit(cls: GetMessagesParams, value: int) -> int:
        if value > 100: value = 100
        if value < 1: value = 1
        return value


class GetChatsParams(BaseModel):
    limit: int = 100
    before: int = 2 ** 63 - 1
    after: int = -(2 ** 63)
    type: str = ""

    @validator("limit")
    def validate_limit(cls: GetChatsParams, value: int) -> int:
        if value > 100: value = 100
        if value < 1: value = 1
        return value

    @validator("type")
    def validate_type(cls: GetChatsParams, value: str) -> str:
        if value not in ("", "private", "group", "supergroup", "channel"):
            value = ""
        return value


class GetUserParams(BaseModel):
    user_id: int