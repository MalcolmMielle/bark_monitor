import json
import os


class Config(object):
    # Singleton
    _CONFIG_FILE: str | None = None
    _CONFIG: dict | None = None

    def __init__(self, config_file=None):
        if config_file is None:
            config_file = Config.get_required_env_var("BARK_MONITOR_CONFIG_FILE")

        # Check that specified config file exists
        assert os.path.exists(config_file)

        # Use singleton pattern to store config file location/load config once
        Config._CONFIG_FILE = config_file
        with open(config_file, "r") as f:
            Config._CONFIG = json.load(f)

    @staticmethod
    def get_config_file() -> str | None:
        return Config._CONFIG_FILE

    @staticmethod
    def get_required_env_var(envvar: str) -> str:
        if envvar not in os.environ:
            raise RuntimeError(f"Please set the {envvar} environment variable")
        return os.environ[envvar]

    @staticmethod
    def get_required_config_var(configvar: str) -> str:
        assert Config._CONFIG
        if configvar not in Config._CONFIG:
            raise Exception(
                f"Please set the {configvar} variable "
                "in the config file {Config._CONFIG_FILE}"
            )
        return Config._CONFIG[configvar]

    @classmethod
    def google_cred(cls) -> str:
        """Example variable that is set in the config file (preferred)"""
        if cls._FOO is None:
            cls._FOO = Config.get_required_config_var("google_cred")
        return cls._FOO
