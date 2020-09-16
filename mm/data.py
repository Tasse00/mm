import logging
from dataclasses import dataclass
from typing import Any, List, Dict

from mm.config import SensorStoreSettings


@dataclass
class StoreUnit:
    data: List[Any]
    config: SensorStoreSettings

    def store(self, sample: Any):
        if len(self.data) >= self.config.length:
            self.data = self.data[len(self.data) - self.config.length + 1:]
        self.data.append(sample)


logger = logging.getLogger(__name__)


class DataStore:

    def __init__(self):
        self.data: Dict[str, StoreUnit] = {}

    def register(self, identifier: str, cfg: SensorStoreSettings):
        self.data[identifier] = StoreUnit(data=[], config=cfg)

    def store(self, identifier: str, val: Any):
        if identifier not in self.data:
            logger.error(f"sensor:{identifier} is not registered.")
            return
        self.data[identifier].store(val)

    def get_sequence(self, identifier: str) -> List[Any]:
        if identifier not in self.data:
            logger.error(f"sensor:{identifier} is not existed.")
            return []
        else:
            return self.data[identifier].data
