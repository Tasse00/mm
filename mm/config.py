import logging
import os
import sys
from dataclasses import dataclass, field, asdict
from itertools import chain
from pathlib import Path
from typing import Dict, Any, List, Iterator

import dacite
from mm.sensor import Sensor, SensorStoreSettings

from mm.indicator import Indicator, IndicatorData

from mm.utils import find_mods_in

logger = logging.getLogger(__name__)


@dataclass
class IndicatorSettings:
    type: str
    data: IndicatorData
    name: str = ""
    kwargs: Dict[str, Any] = field(default_factory=dict)
    interval: int = 2000

    def __post_init__(self):
        if not self.name:
            self.name = self.type


@dataclass
class SensorSettings:
    type: str
    store: SensorStoreSettings
    interval: int = 2000
    name: str = ""
    kwargs: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.name:
            self.name = self.type


@dataclass
class Config:
    ui_file: str = ""
    pos_x: int = 400
    pos_y: int = 400
    indicators_settings: List[IndicatorSettings] = field(default_factory=list)
    sensors_settings: List[SensorSettings] = field(default_factory=list)


class SettingsStore:
    BUILTIN_SENSORS_MODULE = "mm.sensor"
    BUILTIN_SENSORS_DIR = Path(__file__).parent.joinpath("sensor")
    BUILTIN_INDICATORS_MODULE = "mm.indicator"
    BUILTIN_INDICATORS_DIR = Path(__file__).parent.joinpath("indicator")

    def __init__(self, settings_home: str):

        self.settings_home = os.path.expanduser(settings_home)
        self.additional_indicators_dir = Path(self.settings_home, "indicators")
        self.additional_sensors_dir = Path(self.settings_home, "sensors")

        for p in [self.additional_indicators_dir, self.additional_sensors_dir]:
            if p not in sys.path:
                sys.path.append(str(p))

        os.makedirs(self.settings_home, exist_ok=True)
        os.makedirs(self.additional_sensors_dir, exist_ok=True)
        os.makedirs(self.additional_indicators_dir, exist_ok=True)

        self.config_file = Path(self.settings_home, "config.yaml")

        self.config = self._load_config()

    def _load_config(self) -> Config:
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
            cfg = self._generate_init_config()
        return cfg

    def _generate_init_config(self) -> Config:
        """创建初始配置"""
        from mm.indicator.simple import CpuIndicator, MemoryIndicator, NetworkIndicator, DiskIndicator
        from mm.indicator.chart import CpuIndicator as ChartCpuIndicator, MemoryIndicator as ChartMemoryIndicator
        from mm.sensor.simple import CpuSensor, MemorySensor, NetworkSensor, DiskSensor

        indicator_configs = []

        for indicator_cls in [CpuIndicator, ChartCpuIndicator, MemoryIndicator, ChartMemoryIndicator, NetworkIndicator,
                              DiskIndicator]:
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

    def scan_available_sensor(self) -> Iterator[type]:
        for mod in chain(
                find_mods_in(self.BUILTIN_SENSORS_DIR, self.BUILTIN_SENSORS_MODULE),
                find_mods_in(self.additional_sensors_dir)
        ):
            for attr in dir(mod):
                if attr.startswith("_"):
                    continue
                val = getattr(mod, attr)
                try:
                    if val != Sensor and issubclass(val, Sensor):
                        yield val
                except:
                    pass

    def scan_available_indicator(self) -> Iterator[type]:
        for mod in chain(
                find_mods_in(self.BUILTIN_INDICATORS_DIR, self.BUILTIN_INDICATORS_MODULE),
                find_mods_in(self.additional_indicators_dir)
        ):
            for attr in dir(mod):
                if attr.startswith("_"):
                    continue
                val = getattr(mod, attr)
                try:
                    if val != Indicator and issubclass(val, Indicator):
                        yield val
                except:
                    pass
