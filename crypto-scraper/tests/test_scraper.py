import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import scraper


class ScraperTests(unittest.TestCase):
    def test_local_percent_units(self):
        row = scraper.normalize([dict(sym='BTC', last=100, ch24=-2, funding_pct=0.01)])[0]
        self.assertEqual(row['funding_pct'], 0.01)
        self.assertEqual(row['change_24h_pct'], -2)

    def test_okx_units_and_filter(self):
        rows = scraper.normalize({'code': '0', 'data': [dict(instId='BTC-USDT-SWAP', last='110', open24h='100', fundingRate='0.0001'), dict(instId='BTC-USD-SWAP', last='50')]})
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]['change_24h_pct'], 10)
        self.assertEqual(rows[0]['funding_pct'], .01)

    def test_missing_and_zero_open(self):
        row = scraper.normalize([dict(instId='BTC-USDT-SWAP', last=1, open24h='0')])[0]
        self.assertIsNone(row['change_24h_pct'])
        self.assertIsNone(row['funding_pct'])

    def test_rankings_and_output(self):
        rows = scraper.normalize([dict(sym='A', last=1, ch24=-2, funding_pct=None), dict(sym='B', last=.000001, ch24=3, funding_pct=-.02)])
        with tempfile.TemporaryDirectory() as tmp:
            scraper.write_reports(rows, tmp, '<offline>')
            for name, first in [('gainers', 'B'), ('losers', 'A'), ('funding', 'B')]:
                with open(Path(tmp) / (name + '.csv'), encoding='utf-8-sig') as f:
                    data = list(csv.DictReader(f))
                self.assertEqual(data[0]['inst_id'], first + '-USDT-SWAP')
                self.assertEqual(len(data), 2)
            page = (Path(tmp) / 'report.html').read_text()
            self.assertIn('&lt;offline&gt;', page)
            self.assertIn('1e-06', page)

    def test_invalid(self):
        for payload in ([], {}, [dict(sym='BTC', last='NaN')], [dict(sym='BTC', last=-1)]):
            with self.assertRaises(ValueError):
                scraper.normalize(payload)

    @patch('scraper.time.sleep')
    @patch('scraper.api')
    def test_funding_failure_retains_contract(self, api, sleep):
        api.side_effect = [[dict(instId='BTC-USDT-SWAP', last=1)], OSError('offline')]
        rows, warnings = scraper.fetch_market()
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]['funding_pct'])
        self.assertEqual(len(warnings), 1)
        self.assertEqual(api.call_args_list[0].kwargs, {'instType': 'SWAP'})

    @patch('scraper.urlopen')
    def test_request_header(self, opener):
        response = MagicMock()
        response.read.return_value = b'{"code":"0","data":[]}'
        opener.return_value.__enter__.return_value = response
        self.assertEqual(scraper.api('/api/v5/market/tickers', instType='SWAP'), [])
        self.assertEqual(opener.call_args.args[0].get_header('User-agent'), 'curl/8')

    @patch('scraper.api', side_effect=AssertionError('network forbidden'))
    def test_offline_cli(self, api):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'market.json').write_text('[{"sym":"BTC","last":1,"ch24":0,"funding_pct":0}]')
            with patch('sys.argv', ['scraper', '--offline', str(p / 'market.json'), '--output', str(p / 'out')]):
                self.assertEqual(scraper.main(), 0)
            self.assertTrue((p / 'out/report.html').exists())


if __name__ == '__main__':
    unittest.main()
