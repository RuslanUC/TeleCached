# TeleCached

### Caching proxy server for telegram bot api

## Running the server
```shell
git clone https://github.com/RuslanUC/TeleCached
cd TeleCached
pip install -r requirements.txt
cd tg_proxy
python manage.py migrate
python manage.py runserver
```

## Make request to server
Just replace api.telegram.org with your server url, for example (replace token and chat id with yours):
```shell
$ curl http://127.0.0.1:8000/bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11/sendMessage?chat_id=777000&text=test
{
  "ok": true,
  "result": {
    "message_id": 42,
    "from": {
      "id": 123456,
      "is_bot": true,
      "first_name": "Bot",
      "username": "bot"
    },
    "chat": {
      "id": 777000,
      "first_name": "Telegram",
      "type": "private"
    },
    "date": 2147483647,
    "text": "test"
  }
}
```
Now you can get this message via getMessage api method:
```shell
$ curl http://127.0.0.1:8000/bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11/getMessage?message_id=42
{
  "ok": true,
  "result": {
    "message_id": 42,
    "from": {
      "id": 123456,
      "is_bot": true,
      "first_name": "Bot",
      "username": "bot"
    },
    "chat": {
      "id": 777000,
      "first_name": "Telegram",
      "type": "private"
    },
    "date": 2147483647,
    "text": "test"
  }
}
```

Or get all messages (received or sent after you started using TeleCached server) from the chat:
```shell
$ curl http://127.0.0.1:8000/bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11/getMessages?chat_id=777000
{
  "ok": true,
  "result": [
    {
      "message_id": 42,
      "from":
      } {
        "id": 123456,
        "is_bot": true,
        "first_name": "Bot",
        "username": "bot"
      },
      "chat": {
        "id": 777000,
        "first_name": "Telegram",
        "type": "private"
      },
      "date": 2147483647,
      "text": "test"
    }
  ]
}
```

Or get all chats:
```shell
$ curl http://127.0.0.1:8000/bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11/getChats
{
  "ok": true,
  "result": [
    {
      "id": 777000,
      "first_name": "Telegram",
      "type": "private"
    }
  ]
}
```

Or get user:
```shell
$ curl http://127.0.0.1:8000/bot123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11/getUser?user_id=777000
{
  "ok": true,
  "result": {
    "id": 777000,
    "is_bot": false,
    "first_name": "Telegram",
  }
}
```

#### getMessage parameters:
  - message_id - integer, id of message you need to get

#### getMessages parameters:
  - chat_id - integer, id of chat you need to get messages from
  - limit - integer, messages limit, minimum is 1, maximum is 100, default is 100
  - before - integer, id to which you want to get messages
  - after - integer, id from which you want to get messages

#### getChats parameters:
  - limit - integer, chats limit, minimum is 1, maximum is 100, default is 100
  - before - integer, id to which you want to get chats
  - after - integer, id from which you want to get chats
  - type - string, chat type (private, group, supergroup, channel), empty is all (default)

#### getUser parameters:
  - user_id - integer, id of user you need to get


### TODO
  - [ ] add setWebhook, deleteWebhook, getWebhookInfo views
  - [x] add getUser view
  - [x] add getChats view
  - [ ] add getChatMembers view
  - [x] use pyrogram/telethon to upload big files