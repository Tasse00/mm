import json
import logging
from dataclasses import dataclass, field, asdict
from json import JSONDecodeError
from typing import Dict, Any, List

import dacite

logger = logging.getLogger(__name__)


@dataclass
class GlobalSettings:
    color: str = "blue"


@dataclass
class IndicatorSetting:
    type: str
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Config:
    interval: int = 2000  # 更新间隔, ms
    pos_x: int = 400
    pos_y: int = 400
    indicators_settings: List[IndicatorSetting] = field(default_factory=list)
    global_settings: GlobalSettings = field(default_factory=GlobalSettings)


class ConfigStore:

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = Config()

    def load_config(self):
        try:
            with open(self.config_file) as fr:
                dat = json.load(fr)
            try:
                cfg = dacite.from_dict(Config, dat)
            except Exception as e:
                logger.error(f"load config failed: {e}")
                raise
        except (FileNotFoundError, JSONDecodeError):
            cfg = Config()
            cfg.indicators_settings = self.generate_init_config()
        self.config = cfg

    def generate_init_config(self):
        """创建初始配置"""
        from mm.indicator.simple import CpuIndicator, MemoryIndicator, NetworkIndicator, DiskIndicator
        indicator_configs = []

        for indicator_cls in [CpuIndicator, MemoryIndicator, NetworkIndicator, DiskIndicator]:
            indicator_configs.append(
                IndicatorSetting(type=".".join([indicator_cls.__module__, indicator_cls.__qualname__]),
                                 kwargs=indicator_cls.infer_preferred_params()))
        return indicator_configs

    def update_config_file(self):

        with open(self.config_file, "w") as fw:
            data = asdict(self.config)
            json.dump(data, fw, indent=4)
