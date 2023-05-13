from django.contrib import admin

from .models import User, Message, Chat

admin.site.register(User)
admin.site.register(Message)
admin.site.register(Chat)
