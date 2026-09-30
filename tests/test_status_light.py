import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch


class BulbIpCachePathTests(unittest.TestCase):
    def test_cache_file_is_in_the_user_home_directory(self):
        helper_path = Path(__file__).resolve().parents[1] / "pi_status_light.py"
        pywizlight = ModuleType("pywizlight")
        pywizlight.wizlight = object()
        pywizlight.PilotBuilder = object()
        pywizlight.discovery = object()
        spec = importlib.util.spec_from_file_location("pi_status_light", helper_path)
        module = importlib.util.module_from_spec(spec)

        with patch.dict(sys.modules, {"pywizlight": pywizlight}):
            spec.loader.exec_module(module)

        self.assertEqual(module.BULB_IP_FILE, Path.home() / "blubip.txt")


if __name__ == "__main__":
    unittest.main()
