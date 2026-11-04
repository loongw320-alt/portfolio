import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from logic import AlertStore, blocked, fetch_price, instrument, positive, reached


class LogicTests(unittest.TestCase):
    def test_symbols(self):
        self.assertEqual(instrument(' btc '), 'BTC-USDT-SWAP')
        self.assertEqual(instrument('ETH-USDT-SWAP'), 'ETH-USDT-SWAP')
        for symbol in ('', '../BTC', 'BTC-USD-SWAP', '@everyone'):
            with self.assertRaises(ValueError):
                instrument(symbol)

    def test_invalid_targets(self):
        for target in (0, -1, 'nan', 'inf'):
            with self.assertRaises(ValueError):
                positive(target)

    def test_thresholds(self):
        self.assertTrue(reached(dict(target=100, direction='above'), 100))
        self.assertFalse(reached(dict(target=100, direction='above'), 99))
        self.assertTrue(reached(dict(target=100, direction='below'), 99))
        self.assertFalse(reached(dict(target=100, direction='below'), 101))

    def test_persistence_remove_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'alerts.json'
            store = AlertStore(path)
            alert = store.add(1, 2, 'btc', 100, 'above')
            restored = AlertStore(path)
            self.assertEqual(restored.items, [alert])
            with self.assertRaises(ValueError):
                restored.add(1, 2, 'btc', 100, 'invalid')
            self.assertEqual(json.loads(path.read_text()), [alert])
            restored.remove(alert['id'])
            self.assertEqual(AlertStore(path).items, [])

    def test_failed_write_preserves_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = AlertStore(Path(tmp) / 'a.json')
            with patch('logic.os.replace', side_effect=OSError('disk failure')):
                with self.assertRaises(OSError):
                    store.add(1, 2, 'BTC', 1, 'above')
            self.assertEqual(store.items, [])

    def test_corruption_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'a.json'
            path.write_text('broken')
            with self.assertRaises(ValueError):
                AlertStore(path)
            self.assertEqual(path.read_text(), 'broken')

    def test_keywords(self):
        self.assertTrue(blocked('A SPAM link', ['spam', '']))
        self.assertTrue(blocked('示例广告', ['广告']))
        self.assertFalse(blocked('hello', ['', 'spam']))

    @patch('logic.urlopen')
    def test_price_no_network(self, opener):
        response = MagicMock()
        response.read.return_value = b'{"code":"0","data":[{"last":"123.45"}]}'
        opener.return_value.__enter__.return_value = response
        self.assertEqual(fetch_price('BTC'), 123.45)
        self.assertEqual(opener.call_args.args[0].get_header('User-agent'), 'curl/8')
        response.read.return_value = b'{"code":"51001","data":[]}'
        with self.assertRaises(ValueError):
            fetch_price('UNKNOWN')


if __name__ == '__main__':
    unittest.main()
