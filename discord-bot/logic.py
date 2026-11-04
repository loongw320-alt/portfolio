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
    text = content.casefold()
    return any(word.strip().casefold() in text for word in keywords if word.strip())


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

    def remove(self, alert_id):
        self._commit([a for a in self.items if a['id'] != alert_id])
