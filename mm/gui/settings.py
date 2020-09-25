import collections
import json
import logging
from typing import List, OrderedDict, Tuple, Any

from PyQt5 import QtWidgets, Qt, QtCore, QtGui
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QListWidget, QLabel, QLineEdit, QTextEdit, \
    QListWidgetItem, QWidget, QComboBox

from mm.config import SettingsStore, SensorSettings, SensorStoreSettings, IndicatorSettings, IndicatorData

logger = logging.getLogger(__name__)

class ListItemEditWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(ListItemEditWidget, self).__init__(*args, **kwargs)

        self.list = QListWidget(parent=self)

        self.edit_fields: OrderedDict[str, Tuple[QWidget, QWidget]] = collections.OrderedDict()

        self.init_edit_fields()

        self.add_btn = QPushButton(text="Add", parent=self)
        self.del_btn = QPushButton(text="Del", parent=self)
        self.up_btn = QPushButton(text="Up", parent=self)
        self.down_btn = QPushButton(text="Down", parent=self)

        self._init_ui()

    def init_edit_fields(self):

        def name_handler(val: str):
            item = self.list.currentItem()
            item.setData(Qt.Qt.UserRole, val)

        name_edit = QLineEdit(parent=self)
        name_edit.textChanged.connect(name_handler)
        self.edit_fields['name'] = QLabel("Name", parent=self), name_edit

    def build_item_widget(self, data):
        return QLabel(data)

    def set_form_data(self, data):
        self.edit_fields['name'][1].setText(data)

    def new_data(self):
        return "New One"

    def get_all_data(self) -> List[str]:
        return ["demo1", "demo2", "demo3"]

    def _init_ui(self):
        hl = QHBoxLayout()

        list_vl = QVBoxLayout()

        act_hl = QHBoxLayout()
        act_hl.addWidget(self.add_btn)
        act_hl.addWidget(self.del_btn)
        act_hl.addWidget(self.up_btn)
        act_hl.addWidget(self.down_btn)
        list_vl.addLayout(act_hl)

        list_vl.addWidget(self.list)

        hl.addLayout(list_vl)
        form_vl = QVBoxLayout()

        for lbl, edit in self.edit_fields.values():
            form_vl.addWidget(lbl)
            form_vl.addWidget(edit)
            edit.setDisabled(True)

        hl.addLayout(form_vl)

        self.setLayout(hl)

        self.list.currentItemChanged.connect(self._on_item_changed)

        self.add_btn.clicked.connect(self._on_add_item)
        self.del_btn.clicked.connect(self._on_del_item)
        self.up_btn.clicked.connect(self._on_up_item)
        self.down_btn.clicked.connect(self._on_down_item)

    # List Action
    def _on_item_changed(self, current: QListWidgetItem, _: QListWidgetItem):
        if current:
            self.set_form_data(current.data(Qt.Qt.UserRole))
            for _, edit in self.edit_fields.values():
                edit.setDisabled(False)

            self.down_btn.setDisabled(False)
            self.up_btn.setDisabled(False)
            self.del_btn.setDisabled(False)
        else:
            for _, edit in self.edit_fields.values():
                edit.setDisabled(True)
            self.down_btn.setDisabled(True)
            self.up_btn.setDisabled(True)
            self.del_btn.setDisabled(True)

    # Button Action
    def _on_add_item(self):
        self._add_data_as_item(self.new_data())

    def _on_del_item(self):
        row = self.list.currentRow()
        self.list.takeItem(row)

    def _on_up_item(self):
        curr_row = self.list.currentRow()
        if curr_row > 0:
            item = self.list.takeItem(curr_row)
            self.list.insertItem(curr_row - 1, item)
            self.list.setCurrentRow(curr_row - 1)

    def _on_down_item(self):
        curr_row = self.list.currentRow()
        if curr_row + 1 < self.list.count():
            item = self.list.takeItem(curr_row)
            self.list.insertItem(curr_row + 1, item)
            self.list.setCurrentRow(curr_row + 1)

    def _add_data_as_item(self, data):
        item = QListWidgetItem(parent=self.list)
        item.setData(Qt.Qt.UserRole, data)
        self.list.setItemWidget(item, self.build_item_widget(data))

    def modifiedData(self) -> List[Any]:
        data = []
        for idx in range(self.list.count()):
            sensor_settings: List[Any] = self.list.item(idx).data(Qt.Qt.UserRole)
            data.append(sensor_settings)
        return data

    def reset(self):
        self.list.clear()
        for data in self.get_all_data():
            self._add_data_as_item(data)


class SensorTab(ListItemEditWidget):
    def __init__(self, config_store: SettingsStore, *args, **kwargs):
        self.config_store = config_store
        super(SensorTab, self).__init__(*args, **kwargs)

    def init_edit_fields(self):

        def name_handler(value):
            item = self.list.currentItem()
            settings: SensorSettings = item.data(Qt.Qt.UserRole)
            settings.name = value
            self.list.setItemWidget(item, self.build_item_widget(settings))

        def type_handler(value):
            item = self.list.currentItem()
            settings: SensorSettings = item.data(Qt.Qt.UserRole)
            settings.type = value

        def param_handler():
            item = self.list.currentItem()
            settings: SensorSettings = item.data(Qt.Qt.UserRole)
            try:
                settings.kwargs = json.loads(self.edit_fields['param'][1].toPlainText())
            except Exception as e:
                logger.debug(str(e))

        def interval_handler(value: str):
            item = self.list.currentItem()
            settings: SensorSettings = item.data(Qt.Qt.UserRole)
            try:
                settings.interval = int(value)
            except:
                pass

        def store_length_handler(value: str):
            item = self.list.currentItem()
            settings: SensorSettings = item.data(Qt.Qt.UserRole)
            try:
                settings.store.length = int(value)
            except:
                pass

        name_edit = QLineEdit(parent=self)
        name_edit.textChanged.connect(name_handler)

        type_edit = QComboBox(parent=self)
        type_edit.addItems(
            [
                cls.__module__ + '.' + cls.__qualname__
                for cls in
                self.config_store.scan_available_sensor()
            ]
        )
        type_edit.currentTextChanged.connect(type_handler)

        param_edit = QTextEdit(parent=self)
        param_edit.textChanged.connect(param_handler)

        interval_edit = QLineEdit(parent=self)
        interval_edit.setValidator(QIntValidator(1, 3600000, self))
        interval_edit.textChanged.connect(interval_handler)

        store_length_edit = QLineEdit(parent=self)
        store_length_edit.setValidator(QIntValidator(1, 10000, self))
        store_length_edit.textChanged.connect(store_length_handler)

        self.edit_fields["name"] = QLabel("Name"), name_edit
        self.edit_fields["type"] = QLabel(text="Type"), type_edit
        self.edit_fields["param"] = QLabel(text="Param"), param_edit
        self.edit_fields["interval"] = QLabel(text="Interval(ms)"), interval_edit
        self.edit_fields["store_length"] = QLabel(text="Store.Length"), store_length_edit

    def build_item_widget(self, data: SensorSettings):
        return QLabel(text=data.name)

    def set_form_data(self, data: SensorSettings):
        self.edit_fields['name'][1].setText(data.name)
        self.edit_fields['type'][1].setCurrentText(data.type)
        self.edit_fields['param'][1].setText(json.dumps(data.kwargs, ensure_ascii=False, indent=4))
        self.edit_fields['interval'][1].setText(str(data.interval))
        self.edit_fields['store_length'][1].setText(str(data.store.length))

    def new_data(self) -> SensorSettings:
        return SensorSettings(
            name="New One",
            type="",
            store=SensorStoreSettings(length=100)
        )

    def get_all_data(self) -> List[SensorSettings]:
        return [sensor_settings for sensor_settings in self.config_store.config.sensors_settings]


class IndicatorTab(ListItemEditWidget):
    def __init__(self, config_store: SettingsStore, *args, **kwargs):
        self.config_store = config_store
        super(IndicatorTab, self).__init__(*args, **kwargs)

    def build_item_widget(self, data: IndicatorSettings):
        return QLabel(text=data.name)

    def init_edit_fields(self):

        def name_handler(value):
            item = self.list.currentItem()
            settings: IndicatorSettings = item.data(Qt.Qt.UserRole)
            settings.name = value
            self.list.setItemWidget(item, self.build_item_widget(settings))

        def type_handler(value):
            item = self.list.currentItem()
            settings: IndicatorSettings = item.data(Qt.Qt.UserRole)
            settings.type = value

        def param_handler():
            item = self.list.currentItem()
            settings: IndicatorSettings = item.data(Qt.Qt.UserRole)
            try:
                settings.kwargs = json.loads(self.edit_fields['param'][1].toPlainText())
            except Exception as e:
                logger.debug(str(e))

        def interval_handler(value: str):
            item = self.list.currentItem()
            settings: IndicatorSettings = item.data(Qt.Qt.UserRole)
            try:
                settings.interval = int(value)
            except:
                pass

        def data_sensor_handler(value: str):
            item = self.list.currentItem()
            settings: IndicatorSettings = item.data(Qt.Qt.UserRole)
            settings.data.sensor = value

        name_edit = QLineEdit(parent=self)
        name_edit.textChanged.connect(name_handler)

        type_edit = QComboBox(parent=self)
        type_edit.addItems(
            [
                indicator_cls.__module__ + '.' + indicator_cls.__qualname__
                for indicator_cls in
                self.config_store.scan_available_indicator()
            ]
        )
        type_edit.currentTextChanged.connect(type_handler)

        param_edit = QTextEdit(parent=self)
        param_edit.textChanged.connect(param_handler)

        interval_edit = QLineEdit(parent=self)
        interval_edit.setValidator(QIntValidator(1, 3600000, self))
        interval_edit.textChanged.connect(interval_handler)

        data_sensor_edit = QComboBox(parent=self)
        data_sensor_edit.addItems(
            [
                cls.__module__ + '.' + cls.__qualname__
                for cls in
                self.config_store.scan_available_sensor()
            ]
        )
        data_sensor_edit.currentTextChanged.connect(data_sensor_handler)

        self.edit_fields["name"] = QLabel("Name"), name_edit
        self.edit_fields["type"] = QLabel(text="Type"), type_edit
        self.edit_fields["param"] = QLabel(text="Param"), param_edit
        self.edit_fields["interval"] = QLabel(text="Interval(ms)"), interval_edit
        self.edit_fields["data_sensor"] = QLabel(text="Data.Sensor"), data_sensor_edit

    def set_form_data(self, data: IndicatorSettings):
        self.edit_fields['name'][1].setText(data.name)
        self.edit_fields['type'][1].setCurrentText(data.type)
        self.edit_fields['param'][1].setText(json.dumps(data.kwargs, ensure_ascii=False, indent=4))
        self.edit_fields['interval'][1].setText(str(data.interval))
        self.edit_fields['data_sensor'][1].setCurrentText(str(data.data.sensor))

    def new_data(self) -> IndicatorSettings:
        return IndicatorSettings(
            name="New One",
            type="",
            data=IndicatorData(sensor="")
        )

    def get_all_data(self) -> List[IndicatorSettings]:
        return [settings for settings in self.config_store.config.indicators_settings]


class SettingsDialog(QDialog):
    # (List[SensorSettings], List[IndicatorSettings])
    sig_config_updated = QtCore.pyqtSignal(list, list)

    def __init__(self, config_store: SettingsStore, *args, **kwargs):
        super(SettingsDialog, self).__init__(*args, **kwargs)
        self.config_store = config_store

        self.sensor_tab = SensorTab(config_store=self.config_store, parent=self)
        self.indicator_tab = IndicatorTab(config_store=self.config_store, parent=self)

        self.btn_group = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            parent=self)

        self.init_ui()

    def on_ok(self):
        self.sig_config_updated.emit(self.sensor_tab.modifiedData(), self.indicator_tab.modifiedData())

    def init_ui(self):
        tab_w = QtWidgets.QTabWidget(parent=self)

        self.btn_group.accepted.connect(self.on_ok)
        self.btn_group.rejected.connect(self.hide)

        tab_w.addTab(self.indicator_tab, "Indicator")
        tab_w.addTab(self.sensor_tab, "Sensor")

        # 设置UI
        tab_w_layout = QVBoxLayout()
        tab_w_layout.addWidget(tab_w)
        tab_w_layout.addWidget(self.btn_group)
        self.setLayout(tab_w_layout)

        # 设置窗体属性
        self.setWindowModality(Qt.Qt.ApplicationModal)  # 该模式下，只有该dialog关闭，才可以关闭父界面
        self.setWindowTitle("Mini Monitor Settings")

    def showEvent(self, a0: QtGui.QShowEvent) -> None:
        self.sensor_tab.reset()
        self.indicator_tab.reset()

