from dataclasses import dataclass
import tomlkit


@dataclass
class Config:
    pod: str
    idp: str
    username: str
    password: str


def load_config(filepath):
    with open(filepath) as fd:
        cfg_f = tomlkit.load(fd)
        config = Config(
            cfg_f.get('pod'),
            cfg_f.get('idp'),
            cfg_f.get('username'),
            cfg_f.get('password'),
            )
        return config
