"""Standard-library OKX USDT perpetual rankings; Python 3.10+."""
import argparse
import csv
import html
import json
import math
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = 'https://www.okx.com'
FIELDS = ['inst_id', 'last', 'change_24h_pct', 'funding_pct']


def api(path, **params):
    request = Request(BASE + path + '?' + urlencode(params), headers={'User-Agent': 'curl/8'})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=15) as response:
                payload = json.load(response)
            if payload.get('code') != '0':
                raise ValueError(f"OKX: {payload.get('code')} {payload.get('msg')}")
            return payload['data']
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(0.5 * 2 ** attempt)


def number(value):
    if value is None or value == '':
        return None
    n = float(value)
    if not math.isfinite(n):
        raise ValueError('Non-finite number')
    return n


def normalize(payload):
    """Accept local sym snapshots or OKX ticker envelopes with optional funding."""
    items = payload.get('data') if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise ValueError('Expected a JSON array or an OKX {data: [...]} envelope')
    if isinstance(payload, dict) and payload.get('code', '0') != '0':
        raise ValueError('Unsuccessful OKX response')
    rows = []
    seen = set()
    for item in items:
        inst = item.get('instId') or (str(item.get('sym', '')).upper() + '-USDT-SWAP')
        if not re.fullmatch(r'[A-Z0-9]+-USDT-SWAP', inst) or inst.startswith('TEST'):
            continue
        if inst in seen:
            raise ValueError(f'Duplicate instrument: {inst}')
        seen.add(inst)
        last = number(item.get('last'))
        if last is None or last <= 0:
            raise ValueError(f'Invalid price: {inst}')
        if 'ch24' in item:
            change = number(item['ch24'])
        else:
            opening = number(item.get('open24h'))
            change = (last / opening - 1) * 100 if opening and opening > 0 else None
        funding = (number(item['funding_pct']) if 'funding_pct' in item
                   else number(item.get('fundingRate')))
        if funding is not None and 'funding_pct' not in item:
            funding *= 100
        rows.append(dict(zip(FIELDS, (inst, last, change, funding))))
    if not rows:
        raise ValueError('No valid USDT perpetual contracts found')
    return rows


def fetch_market():
    tickers = api('/api/v5/market/tickers', instType='SWAP')
    rows = normalize(tickers)
    warnings = []
    # Bulk request first (one call for every contract); fall back per instrument for gaps.
    try:
        bulk = {d.get('instId'): number(d.get('fundingRate')) for d in api('/api/v5/public/funding-rate', instId='ANY')}
    except (OSError, ValueError, KeyError, TypeError):
        bulk = {}
    for row in rows:
        if bulk.get(row['inst_id']) is not None:
            row['funding_pct'] = bulk[row['inst_id']] * 100
            continue
        try:
            data = api('/api/v5/public/funding-rate', instId=row['inst_id'])
            rate = number(data[0].get('fundingRate')) if data else None
            row['funding_pct'] = rate * 100 if rate is not None else None
            if rate is None:
                warnings.append(row['inst_id'] + ': funding unavailable')
        except (OSError, ValueError, KeyError) as exc:
            warnings.append(f"{row['inst_id']}: {exc}")
        time.sleep(0.12)
    return rows, warnings


def ranking(rows, key, descending=True):
    return sorted(rows, key=lambda r: (r[key] is None,
                  (-r[key] if descending else r[key]) if r[key] is not None else 0, r['inst_id']))


def display(value, signed=False):
    if value is None:
        return '—'
    return format(value, '+.6g' if signed else '.10g')


def write_reports(rows, output, source, warnings=()):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    boards = [('gainers', '涨幅榜 / Gainers', 'change_24h_pct', True),
              ('losers', '跌幅榜 / Losers', 'change_24h_pct', False),
              ('funding', '资金费率 / Funding', 'funding_pct', True)]
    sections = []
    for name, title, key, descending in boards:
        ordered = ranking(rows, key, descending)
        with (output / (name + '.csv')).open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['rank'] + FIELDS)
            writer.writeheader()
            writer.writerows(dict(rank=i, **{k: (round(v, 6) if isinstance(v, float) and k != 'last' else v)
                                             for k, v in row.items()}) for i, row in enumerate(ordered, 1))
        body = ''
        for i, row in enumerate(ordered, 1):
            cells = ''.join(f'<td class="{"up" if row[k] is not None and row[k] >= 0 else "down"}">{display(row[k], True)}%</td>'
                            if row[k] is not None else '<td>—</td>' for k in FIELDS[2:])
            body += f'<tr><td>{i:02}</td><th scope="row">{html.escape(row["inst_id"])}</th><td>{display(row["last"])}</td>{cells}</tr>'
        sections.append(f'<section><h2>{title}</h2><a href="{name}.csv">下载 CSV / Download</a><div class="scroll"><table><thead><tr><th>#</th><th>合约 / Instrument</th><th>价格 / USDT</th><th>24h %</th><th>Funding %</th></tr></thead><tbody>{body}</tbody></table></div></section>')
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    metadata = {'source': source, 'generated_at_utc': stamp, 'count': len(rows), 'warnings': list(warnings)}
    (output / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    css = '''*{box-sizing:border-box}body{margin:0;background:#0a1020;color:#e6edf8;font:15px/1.6 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:48px 22px}.eyebrow{color:#64dfc4;letter-spacing:.18em;font-size:12px}h1{font-size:clamp(30px,5vw,54px);line-height:1.15;margin:16px 0}p{color:#aab8d0;overflow-wrap:anywhere}.stats{display:flex;gap:18px;flex-wrap:wrap;margin:30px 0}.stat,section{background:#121d32;border:1px solid #263650;border-radius:18px;padding:24px}.stat strong{font-size:30px;display:block}.stat{flex:1;min-width:160px}section{margin:24px 0}h2{display:inline-block;margin:0 20px 20px 0;font-size:22px}a,.up{color:#76e4c4}.down{color:#ff9eaa}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;white-space:nowrap;font-variant-numeric:tabular-nums}th,td{text-align:right;padding:13px 10px;border-bottom:1px solid #263650}th:nth-child(2){text-align:left}thead{color:#aab8d0;font-size:12px}tbody tr:hover{background:#1c2a42}footer{color:#aab8d0;font-size:13px}'''
    warning_html = ''.join('<li>' + html.escape(w) + '</li>' for w in warnings)
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>USDT Perpetual · Market Radar</title><style>{css}</style></head><body><main><header><div class="eyebrow">MARKET RADAR / OKX</div><h1>永续市场，一眼看清。<br>USDT Perpetual Monitor</h1><p>{html.escape(source)}</p><p>报表生成时间 / Report generated: {stamp}</p></header><div class="stats"><div class="stat">合约 / Contracts<strong>{len(rows)}</strong></div><div class="stat">上涨 / Positive 24h<strong>{sum(r['change_24h_pct'] is not None and r['change_24h_pct'] > 0 for r in rows)}</strong></div><div class="stat">资金费缺失 / Missing funding<strong>{sum(r['funding_pct'] is None for r in rows)}</strong></div></div>{''.join(sections)}<ul>{warning_html}</ul><footer>所有合约按指标排序；未知值置末。资金费率为单期百分数，非年化。<br>All contracts ranked; missing values last. Funding is per-period %, not annualized.</footer></main></body></html>'''
    (output / 'report.html').write_text(page, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', type=Path, metavar='JSON', help='Read JSON without any network requests')
    parser.add_argument('--output', type=Path, default=Path('output'))
    args = parser.parse_args()
    try:
        if args.offline:
            rows = normalize(json.loads(args.offline.read_text(encoding='utf-8')))
            warnings = []
            source = f'离线快照 / OFFLINE SNAPSHOT: {args.offline.name} · 采集时间未知 / capture time unknown · 非实时 / not live'
        else:
            rows, warnings = fetch_market()
            source = 'OKX public API · sequential snapshot / 分次采集快照'
        write_reports(rows, args.output, source, warnings)
        print(f'{len(rows)} contracts → {args.output}/report.html ({len(warnings)} warnings)')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
