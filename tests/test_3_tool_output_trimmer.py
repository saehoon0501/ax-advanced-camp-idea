import json
import unittest

from ax_advanced_class.tool_output_trimmer import parse_tool_output


class TestToolOutputTrimmer(unittest.TestCase):
    def test_compacts_large_json_string_and_caps_length(self):
        raw = {
            "temperature_c": 25,
            "timestamp": "2025-12-16T09:15:00Z",
            "location": "Seoul, KR",
            "station": {"id": "KXYZ", "lat": 37.5665, "lon": 126.9780},
            "raw": {"a": "x" * 5000, "b": list(range(1000))},
        }
        out = parse_tool_output(json.dumps(raw), max_len=50)
        self.assertLess(len(out), 50)
        self.assertIn("Temperature:", out)
        self.assertIn("25C", out)

    def test_accepts_dict_input(self):
        out = parse_tool_output({"temperature_c": "21", "location": "Busan"}, max_len=50)
        self.assertLess(len(out), 50)
        self.assertIn("Temperature:", out)
        self.assertIn("21C", out)

    def test_converts_fahrenheit_when_c_missing(self):
        out = parse_tool_output({"temperature_f": 77}, max_len=50)
        self.assertIn("25C", out)

    def test_missing_temperature_returns_compact_error(self):
        out = parse_tool_output({"location": "Somewhere", "timestamp": "now"}, max_len=20)
        self.assertLess(len(out), 20)
        self.assertIn("temperature", out)

    def test_invalid_json_string_returns_compact_error(self):
        out = parse_tool_output("{not-json", max_len=20)
        self.assertLess(len(out), 20)
        self.assertIn("temperature", out)


if __name__ == "__main__":
    unittest.main()


