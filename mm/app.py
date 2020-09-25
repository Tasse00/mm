import asyncio
import logging
import os
import sys
from asyncio import AbstractEventLoop
from threading import Thread
from typing import Optional

from PyQt5 import QtWidgets

from mm.config import SettingsStore, SensorSettings
from mm.data import DataStore
from mm.utils import dynamic_load
from mm.gui import MainWindow

logger = logging.getLogger(__name__)


class CollectThread(Thread):

    def __init__(self, config_store: SettingsStore, data_store: DataStore):
        super(CollectThread, self).__init__()
        self.config_store = config_store
        self.data_store = data_store
        self.is_end: Optional[asyncio.Future] = None

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
        self.config_store = self.build_config_store()
        self.data_store = self.build_data_store()

    def build_config_store(self) -> SettingsStore:
        config = SettingsStore(os.environ.get("MM_HOME", "~/.mm"))
        return config

    def build_data_store(self) -> DataStore:
        return DataStore()

    def run(self):
        collect_thread = CollectThread(config_store=self.config_store, data_store=self.data_store)
        collect_thread.start()

        app = QtWidgets.QApplication(sys.argv)
        self.win = MainWindow(self.config_store, self.data_store)
        ret = app.exec_()

        logger.info("GUI is existed.")

        # TODO Thread退出有延迟，asyncio增加一个0.1s间隔的状态检测
        collect_thread.is_end.set_result(True)
        collect_thread.join()
        logger.info("Collect Thread is existed.")
        sys.exit(ret)
