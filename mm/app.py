import asyncio
import logging
import os
import sys
from asyncio import AbstractEventLoop
from threading import Thread
from typing import Optional

from PyQt5 import QtWidgets

from mm.config import ConfigStore, SensorSettings
from mm.data import DataStore
from mm.utils import dynamic_load
from mm.win import MainWindow

logger = logging.getLogger(__name__)



class CollectThread(Thread):

    def __init__(self, config_store: ConfigStore, data_store: DataStore):
        super(CollectThread, self).__init__()
        self.config_store = config_store
        self.data_store = data_store
        self.is_end : Optional[asyncio.Future] = None
    async def run_collect_job(self, sensor_config: SensorSettings, loop: AbstractEventLoop):
        sensor_cls = dynamic_load(sensor_config.type)
        sensor = sensor_cls(**sensor_config.kwargs)
        logger.debug(f"register '{sensor_config.type}'")
        self.data_store.register(identifier=sensor_config.type, cfg=sensor_config.store)

        while True:
            val = await sensor.collect()
            self.data_store.store(sensor_config.type, val)
            await asyncio.sleep(sensor_config.interval / 1000, loop=loop)

    def run(self) -> None:

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.is_end = asyncio.Future()
        tasks = [loop.create_task(self.run_collect_job(sensor_settings, loop)) for sensor_settings in
                 self.config_store.config.sensors_settings]

        async def waiting_quit():
            await self.is_end
            for task in tasks:
                task.cancel()
        task = loop.create_task(waiting_quit())
        loop.run_until_complete(task)


class Application:

    def __init__(self):
        self.home_dir = os.path.expanduser(os.environ.get("MM_HOME", "~/.mm"))
        self.config_file = os.path.join(self.home_dir, "config.yaml")
        self.custom_indicators_dir = os.path.join(self.home_dir, "indicators")

        self.init_mm_home()
        self.config_store = self.build_config_store()
        self.data_store = self.build_data_store()
        self.init_custom_indicators_supports()

    def init_mm_home(self):
        os.makedirs(self.home_dir, exist_ok=True)
        os.makedirs(self.custom_indicators_dir, exist_ok=True)

    def init_custom_indicators_supports(self):
        sys.path.append(self.custom_indicators_dir)

    def build_config_store(self) -> ConfigStore:
        config = ConfigStore(self.config_file)
        config.load_config()
        config.update_config_file()
        return config

    def build_data_store(self) -> DataStore:
        return DataStore()

    def run(self):
        collect_thread = CollectThread(config_store=self.config_store, data_store=self.data_store)
        collect_thread.start()

        app = QtWidgets.QApplication(sys.argv)
        MainWindow(self.config_store, self.data_store)
        ret = app.exec_()

        collect_thread.is_end.set_result(True)
        collect_thread.join()

        sys.exit(ret)
