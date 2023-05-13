from json import JSONDecodeError
from typing import Optional, Any

import httpx
from django.http import HttpResponse, JsonResponse
from pydantic import ValidationError


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