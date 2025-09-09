import json
import typing
from base64 import b64encode
from hashlib import md5
from os import path

import toml
import yaml


def locate_config():
    """Find config (checking for .yml, .yaml and .toml in that order), crashing on failure (n found is not exactly 1)"""
    # Check possible config file paths
    yml_found = path.isfile("./config/config.yml")
    yaml_found = path.isfile("./config/config.yaml")
    toml_found = path.isfile("./config/config.toml")
    # Count how many were found
    n_found = yml_found + yaml_found + toml_found
    if n_found < 1:  # If none were found produce an error and exit
        print(
            "No configuration found!\n"
            "The config file must be in the ./config folder relative to main.py.\n"
            "Valid filenames are:\n"
            "\tconfig.yml\n"
            "\tconfig.yaml\n"
            "\tconfig.toml\n"
            "Please see the documentation for more information."
        )
        exit(1)
    elif n_found > 1:  # If more than one were found produce an error and exit
        print(
            "Multiple possible configurations found!\n"
            "Please remove or rename all but one of them.\n"
            "See the documentation for more information."
        )
        exit(1)
    else:  # Return the path that was found for the caller to consume
        if yml_found:
            config_path = "./config/config.yml"
        elif yaml_found:
            config_path = "./config/config.yaml"
        elif toml_found:
            config_path = "./config/config.toml"
        return config_path


def read_config(config_path: str) -> dict[str, typing.Any]:
    """Read a config file and return the contents as a dict"""
    if not path.exists(config_path):
        raise FileNotFoundError(f"Could not find {config_path}")
    else:
        ext = config_path.split(".")[-1]
        with open(config_path) as file:
            match ext:
                case "yml" | "yaml":
                    result = yaml.safe_load(file)
                case "toml":
                    result = toml.load(file)
                case _:
                    raise ValueError("Extension {ext} is not one of: [yml, yaml, toml]")
        return result


def gen_config_hash(config) -> bytes:
    """Generate a hash of a config dict to check for changes. Converts to key-sorted json first to ensure consistency."""
    return b64encode(md5(json.dumps(config, sort_keys=True).encode()).digest())
