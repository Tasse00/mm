from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class SensorStoreSettings:
    length: int


class Sensor(ABC):
    """收集数据"""

    DataType = None

    @abstractmethod
    async def collect(self) -> Any:
        """收集数据"""

    @classmethod
    @abstractmethod
    def infer_preferred_params(cls) -> Dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def infer_preferred_store_settings(cls) -> SensorStoreSettings:
        pass
