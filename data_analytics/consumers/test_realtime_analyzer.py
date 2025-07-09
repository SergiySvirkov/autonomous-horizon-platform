# data_analytics/consumers/test_realtime_analyzer.py

import pytest
from unittest.mock import patch
from .realtime_analyzer import analyze_telemetry, LOW_BATTERY_THRESHOLD, HIGH_SPEED_THRESHOLD_SHUTTLE

# This file contains unit tests for the realtime_analyzer script.
# We use pytest for testing and unittest.mock.patch to capture print output.

def test_analyze_telemetry_no_alert():
    """
    Tests that no alert is printed for normal telemetry data.
    """
    normal_data = {
        "vehicle_id": "zoox-01",
        "vehicle_type": "shuttle",
        "battery_level": 0.85,
        "speed_kmh": 50
    }
    
    # 'patch' intercepts calls to 'print' within the 'with' block.
    with patch('builtins.print') as mocked_print:
        analyze_telemetry(normal_data)
        # assert_not_called() checks that print() was never invoked.
        mocked_print.assert_not_called()

def test_analyze_telemetry_low_battery_alert():
    """
    Tests that a low battery alert is correctly triggered and printed.
    """
    low_battery_data = {
        "vehicle_id": "zoox-02",
        "vehicle_type": "shuttle",
        "battery_level": LOW_BATTERY_THRESHOLD - 0.01, # Just below the threshold
        "speed_kmh": 45
    }
    
    with patch('builtins.print') as mocked_print:
        analyze_telemetry(low_battery_data)
        # assert_called_once() checks that print() was called exactly once.
        mocked_print.assert_called_once()
        # We check that the printed message contains the expected alert text.
        args, _ = mocked_print.call_args
        assert "LOW BATTERY" in args[0]
        assert "zoox-02" in args[0]

def test_analyze_telemetry_high_speed_alert():
    """
    Tests that a high speed alert is correctly triggered for a shuttle.
    """
    high_speed_data = {
        "vehicle_id": "zoox-03",
        "vehicle_type": "shuttle",
        "battery_level": 0.9,
        "speed_kmh": HIGH_SPEED_THRESHOLD_SHUTTLE + 10 # Well above the threshold
    }
    
    with patch('builtins.print') as mocked_print:
        analyze_telemetry(high_speed_data)
        mocked_print.assert_called_once()
        args, _ = mocked_print.call_args
        assert "HIGH SPEED" in args[0]
        assert "zoox-03" in args[0]

def test_analyze_telemetry_multiple_alerts():
    """
    Tests that both low battery and high speed alerts can be triggered from one message.
    """
    multiple_issues_data = {
        "vehicle_id": "evtol-01",
        "vehicle_type": "eVTOL", # Note: eVTOL has a different speed threshold
        "battery_level": LOW_BATTERY_THRESHOLD - 0.05,
        "speed_kmh": 350 # High speed for an eVTOL
    }
    
    with patch('builtins.print') as mocked_print:
        analyze_telemetry(multiple_issues_data)
        # We expect two print calls, one for each alert.
        assert mocked_print.call_count == 2
        
        # Check the content of both calls
        call_args_list = mocked_print.call_args_list
        assert any("LOW BATTERY" in str(call) for call in call_args_list)
        assert any("HIGH SPEED" in str(call) for call in call_args_list)

def test_analyze_telemetry_missing_keys():
    """
    Tests that the function handles missing keys in the data gracefully without crashing.
    """
    incomplete_data = {
        "vehicle_id": "zoox-04"
        # Missing battery_level and speed_kmh
    }
    
    try:
        # This should run without raising any exceptions.
        analyze_telemetry(incomplete_data)
    except Exception as e:
        pytest.fail(f"analyze_telemetry raised an exception with incomplete data: {e}")
