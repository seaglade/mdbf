import json
import typing
from base64 import b64encode
from hashlib import md5
from os import path

import toml
import yaml


def locate_config() -> str:
    """Find config file (.yml, .yaml, .toml, or .json) in the ./config directory."""
    config_file_paths = [
        "./config/config.yml",
        "./config/config.yaml",
        "./config/config.toml",
        "./config/config.json",
    ]

    found_files = [file for file in config_file_paths if path.isfile(file)]

    if len(found_files) == 0:
        raise FileNotFoundError(
            "No configuration found! The config file must be in the ./config folder relative to main.py."
        )
    elif len(found_files) > 1:
        raise RuntimeError(
            "Multiple possible configurations found! Please remove or rename all but one of them."
        )

    return found_files[0]


def read_config(config_path: str) -> dict[str, typing.Any]:
    """Read a config file and return its contents as a dictionary."""
    if not path.exists(config_path):
        raise FileNotFoundError(f"Could not find {config_path}")

    ext = config_path.split(".")[-1]
    try:
        with open(config_path) as file:
            match ext:
                case "yml" | "yaml":
                    return yaml.safe_load(file)
                case "toml":
                    return toml.load(file)
                case "json":
                    return json.load(file)
                case _:
                    raise ValueError(f"Unsupported file extension: {ext}")
    except Exception as e:
        raise RuntimeError(f"Error reading config file {config_path}: {e}")


def gen_config_hash(config: dict) -> bytes:
    """Generate a hash of a config dictionary for change detection."""
    try:
        json_data = json.dumps(config, sort_keys=True)
        return b64encode(md5(json_data.encode()).digest())
    except Exception as e:
        raise RuntimeError(f"Error generating config hash: {e}")
