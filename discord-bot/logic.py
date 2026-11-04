"""Network-independent alert persistence and moderation logic."""
import json
import math
import os
import re
import uuid
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def instrument(symbol):
    value = symbol.strip().upper()
    if re.fullmatch(r'[A-Z0-9]{1,24}', value):
        return value + '-USDT-SWAP'
    if re.fullmatch(r'[A-Z0-9]{1,24}-USDT-SWAP', value):
        return value
    raise ValueError('Use BTC or BTC-USDT-SWAP / 请输入币种或 USDT 永续合约')


def positive(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Price must be positive and finite / 价格必须为有限正数')
    return value


def fetch_price(symbol):
    inst = instrument(symbol)
    request = Request('https://www.okx.com/api/v5/market/ticker?' + urlencode({'instId': inst}),
                      headers={'User-Agent': 'curl/8'})
    with urlopen(request, timeout=12) as response:
        payload = json.load(response)
    if payload.get('code') != '0' or not payload.get('data'):
        raise ValueError('OKX returned no price / 未找到价格')
    return positive(payload['data'][0]['last'])


def blocked(content, keywords):
    """True if any keyword appears as a whole word (case-insensitive), e.g. 'scam' matches 'a scam!' but not 'scamper'.
    CJK keywords match as substrings."""
    text = content.casefold()
    cjk = re.compile(r'[\u3040-\u30ff\u3400-\u9fff\uac00-\ud7af]')
    # CJK text has no spaces between words, so CJK keywords use substring matching.
    if any(cjk.search(w) and w.strip().casefold() in text for w in keywords if w.strip()):
        return True
    return any(not cjk.search(word) and re.search(r'(?<!\w)' + re.escape(word.strip().casefold()) + r'(?!\w)', text)
               for word in keywords if word.strip())


def reached(alert, price):
    price = positive(price)
    return price >= alert['target'] if alert['direction'] == 'above' else price <= alert['target']


class AlertStore:
    """Single-process store; synchronous operations must run on the event-loop thread."""
    def __init__(self, path):
        self.path = Path(path)
        self.items = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else []
        if not isinstance(self.items, list):
            raise ValueError('Alert store must be a JSON list')
        for item in self.items:
            if item['direction'] not in ('above', 'below'):
                raise ValueError('Invalid stored direction')
            instrument(item['symbol'])
            positive(item['target'])
            for key in ('id', 'user_id', 'channel_id'):
                if key not in item:
                    raise ValueError('Invalid alert store')

    def _commit(self, items):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + '.tmp')
        temporary.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(temporary, self.path)
        self.items = items

    def add(self, user_id, channel_id, symbol, target, direction):
        if direction not in ('above', 'below'):
            raise ValueError('Direction must be above or below')
        if sum(a['user_id'] == user_id for a in self.items) >= 20:
            raise ValueError('Maximum 20 active alerts per user / 每人最多 20 条提醒')
        item = dict(id=uuid.uuid4().hex, user_id=user_id, channel_id=channel_id,
                    symbol=instrument(symbol), target=positive(target), direction=direction)
        self._commit(self.items + [item])
        return item

    def for_user(self, user_id):
        return [a for a in self.items if a['user_id'] == user_id]

    def cancel(self, user_id, alert_id):
        """Delete one of the user's alerts by full id or unique prefix (min 4 chars). Returns the alert."""
        alert_id = alert_id.strip().lower()
        if len(alert_id) < 4:
            raise ValueError('Use at least 4 characters of the alert id / 至少输入 4 位提醒 ID')
        matches = [a for a in self.for_user(user_id) if a['id'].startswith(alert_id)]
        if len(matches) != 1:
            raise ValueError('No unique alert with that id / 未找到唯一匹配的提醒')
        self.remove(matches[0]['id'])
        return matches[0]

    def remove(self, alert_id):
        self._commit([a for a in self.items if a['id'] != alert_id])
