import unittest
from pathlib import Path

from bark_monitor.cli.get_param import NextCloudParameters, Parameters


class TestConfig(unittest.TestCase):
    def test_save_load_config(self) -> None:
        parameters = Parameters(
            accept_new_users=True,
            api_key="test_api_key",
            output_folder=Path("test/data"),
            config_folder=Path(""),
        )
        parameters.save(Path("tests/data/config.json"))

        new_parameters = Parameters.read(Path("tests/data/config.json"))

        self.assertEqual(new_parameters.output_folder, Path("test/data"))
        self.assertEqual(new_parameters.api_key, "test_api_key")
        self.assertEqual(new_parameters.accept_new_users, True)

    def test_next_cloud(self) -> None:
        parameters = Parameters(
            accept_new_users=True,
            api_key="test_api_key",
            output_folder=Path("test/data"),
            config_folder=Path(""),
            nextcloud_parameters=NextCloudParameters(
                user="user", server="server", passwd="passwd"
            ),
        )

        parameters.save(Path("tests/data/config_nc.json"))
