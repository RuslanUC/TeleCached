# Generated by Django 4.2.1 on 2023-05-15 14:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("proxy", "0007_botsession"),
    ]

    operations = [
        migrations.AddField(
            model_name="chat",
            name="_id",
            field=models.BigAutoField(default=None, primary_key=True, serialize=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="chat",
            name="id",
            field=models.BigIntegerField(),
        ),
        migrations.AddConstraint(
            model_name="chat",
            constraint=models.UniqueConstraint(
                fields=("id", "bot_id"), name="unique_chat_bot"
            ),
        ),
    ]
