import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List

import dacite

logger = logging.getLogger(__name__)


@dataclass
class IndicatorData:
    sensor: str

@dataclass
class IndicatorSettings:
    type: str
    data: IndicatorData
    kwargs: Dict[str, Any] = field(default_factory=dict)
    interval: int = 2000


@dataclass
class SensorStoreSettings:
    length: int


@dataclass
class SensorSettings:
    type: str
    store: SensorStoreSettings
    interval: int = 2000
    kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Config:
    ui_file: str = ""
    pos_x: int = 400
    pos_y: int = 400
    indicators_settings: List[IndicatorSettings] = field(default_factory=list)
    sensors_settings: List[SensorSettings] = field(default_factory=list)

class ConfigStore:

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = Config()

    def load_config(self):
        import yaml
        try:
            with open(self.config_file) as fr:
                dat = yaml.full_load(fr)
            try:
                cfg = dacite.from_dict(Config, dat)
            except Exception as e:
                logger.error(f"load config failed: {e}")
                raise
        except FileNotFoundError:
            cfg = self.generate_init_config()
        self.config = cfg

    def generate_init_config(self) -> Config:
        """创建初始配置"""
        from mm.indicator.simple import CpuIndicator, MemoryIndicator, NetworkIndicator, DiskIndicator
        from mm.sensor.simple import CpuSensor, MemorySensor, NetworkSensor, DiskSensor
        indicator_configs = []

        for indicator_cls in [CpuIndicator, MemoryIndicator, NetworkIndicator, DiskIndicator]:
            indicator_configs.append(
                IndicatorSettings(type=".".join([indicator_cls.__module__, indicator_cls.__qualname__]),
                                  data=indicator_cls.infer_preferred_data(),
                                  kwargs=indicator_cls.infer_preferred_params(), ))
        sensor_configs = []
        for sensor_cls in [CpuSensor, MemorySensor, DiskSensor, NetworkSensor]:
            sensor_configs.append(
                SensorSettings(type=".".join([sensor_cls.__module__, sensor_cls.__qualname__]),
                               store=sensor_cls.infer_preferred_store_settings(),
                               kwargs=sensor_cls.infer_preferred_params())
            )

        return Config(indicators_settings=indicator_configs, sensors_settings=sensor_configs)

    def update_config_file(self):
        import yaml
        with open(self.config_file, "w") as fw:
            data = asdict(self.config)
            yaml.safe_dump(data, fw)
