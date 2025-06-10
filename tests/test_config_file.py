import unittest
from pathlib import Path

from bark_monitor.cli.get_param import Parameters


class TestConfig(unittest.TestCase):
    def test_save_load_config(self) -> None:
        parameters = Parameters(
            accept_new_users=True,
            api_key="test_api_key",
            output_folder=Path("test/data"),
            config_folder=Path(""),
        )
        parameters.save("tests/data/config.json")

        new_parameters = Parameters.read("tests/data/config.json")

        self.assertEqual(new_parameters.output_folder, Path("test/data"))
        self.assertEqual(new_parameters.api_key, "test_api_key")
        self.assertEqual(new_parameters.accept_new_users, True)
