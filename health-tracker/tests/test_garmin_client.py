"""
Garmin client regression tests.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from garmin.garmin_client import GarminClient


class DummyGarmin:
    def __init__(self, sleep_data=None, rhr_data=None):
        self._sleep_data = sleep_data
        self._rhr_data = rhr_data

    def get_sleep_data(self, _date_str):
        return self._sleep_data

    def get_rhr_day(self, _date_str):
        return self._rhr_data


def build_client(dummy: DummyGarmin) -> GarminClient:
    client = GarminClient(email="test@example.com", password="secret", is_china=True)
    client._authenticated = True
    client.garmin = dummy
    return client


def test_get_sleep_data_returns_none_for_empty_sleep_payload():
    client = build_client(DummyGarmin(sleep_data={
        "dailySleepDTO": {
            "sleepTimeSeconds": None,
            "deepSleepSeconds": None,
            "lightSleepSeconds": None,
            "remSleepSeconds": None,
            "sleepStartTimestampLocal": None,
            "sleepEndTimestampLocal": None,
        }
    }))

    assert client.get_sleep_data(datetime(2026, 3, 18)) is None


def test_get_sleep_data_preserves_actual_sleep_values():
    client = build_client(DummyGarmin(sleep_data={
        "restingHeartRate": 58,
        "dailySleepDTO": {
            "sleepTimeSeconds": 24540,
            "deepSleepSeconds": 5160,
            "lightSleepSeconds": 14700,
            "remSleepSeconds": 4680,
            "awakeSleepSeconds": 120,
            "sleepStartTimestampLocal": 1,
            "sleepEndTimestampLocal": 2,
            "avgHeartRate": 64,
            "sleepScores": {"overall": {"value": 85}},
        }
    }))

    result = client.get_sleep_data(datetime(2026, 3, 18))

    assert result["sleep_duration"] == 6.82
    assert result["deep_sleep_duration"] == 1.43
    assert result["rem_sleep_duration"] == 1.3
    assert result["resting_heart_rate"] == 58
    assert result["avg_heart_rate"] == 64


def test_get_heart_rate_data_returns_none_when_resting_hr_missing():
    client = build_client(DummyGarmin(rhr_data={"allMetrics": {"metricsMap": {}}}))

    assert client.get_heart_rate_data(datetime(2026, 3, 18)) is None
