# Generated by Django 4.2.1 on 2023-05-13 13:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proxy", "0004_chatmember_remove_message_from_chat_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="last_name",
            field=models.CharField(default=None, max_length=128, null=True),
        ),
    ]
