import sys,unittest,datetime,urllib.error
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from fetch_elevation import retry_delay,download_with_retry

class RetryTests(unittest.TestCase):
    def test_seconds(self):
        self.assertEqual(retry_delay('120',0),120)
        self.assertEqual(retry_delay('1',1),60)
        self.assertEqual(retry_delay(None,2),120)
    def test_http_date(self):
        now=datetime.datetime(2026,1,1,tzinfo=datetime.timezone.utc)
        self.assertEqual(retry_delay('Thu, 01 Jan 2026 00:03:00 GMT',0,now),180)
    def test_retry(self):
        error=urllib.error.HTTPError('https://example.org',429,'Too Many Requests',{'Retry-After':'90'},None)
        with patch('fetch_elevation.download',side_effect=[error,None]) as dl,patch('fetch_elevation.time.sleep') as sleep:
            download_with_retry('lidar',0,{},100)
            self.assertEqual(dl.call_count,2)
            sleep.assert_called_once_with(90)
    def test_long_wait_stops(self):
        error=urllib.error.HTTPError('https://example.org',429,'Too Many Requests',{'Retry-After':'3600'},None)
        with patch('fetch_elevation.download',side_effect=error),patch('fetch_elevation.time.sleep') as sleep:
            with self.assertRaises(RuntimeError):download_with_retry('lidar',0,{},100)
            sleep.assert_not_called()

    def test_timeout_retry(self):
        with patch('fetch_elevation.download',side_effect=[TimeoutError('timed out'),None]) as dl,patch('fetch_elevation.time.sleep') as sleep:
            download_with_retry('lidar',0,{},100,timeout=15)
            self.assertEqual(dl.call_count,2)
            self.assertEqual(dl.call_args.kwargs['timeout'],15)
            sleep.assert_called_once_with(30)
    def test_no_retry_on_permanent_http(self):
        error=urllib.error.HTTPError('https://example.org',403,'Forbidden',{},None)
        with patch('fetch_elevation.download',side_effect=error),patch('fetch_elevation.time.sleep') as sleep:
            with self.assertRaises(urllib.error.HTTPError):download_with_retry('lidar',0,{},100)
            sleep.assert_not_called()
