from django.contrib import admin

from .models import User, Message, Chat, Webhook, BotSession

admin.site.register(User)
admin.site.register(Message)
admin.site.register(Chat)
admin.site.register(Webhook)
admin.site.register(BotSession)
