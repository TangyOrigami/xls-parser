import re
import asyncio

from qasync import asyncSlot
from PyQt6.QtCore import QSortFilterProxyModel, QStringListModel, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from structs.result import Result
from util.logger import CLogger
from util.task_manager import TaskManager
from util.pay_period_manager import PayPeriodManager

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class MidComponent(QWidget):
    def __init__(self, manager: TaskManager):
        super().__init__()

        self.pp_manager = PayPeriodManager()
        self.manager = manager

        self.ppd_combo_box = QComboBox()
        self.ppd_combo_box.setEditable(True)

        self.group_combo_box = QComboBox()
        self.group_combo_box.setEditable(True)
        self.group_combo_box.currentTextChanged.connect(self._on_group_changed)

        self.employee_combo_box = QComboBox()
        self.employee_combo_box.setEditable(True)

        self.search = QPushButton("Search")
        self.search.clicked.connect(self.send_search)

        self.refresh = QPushButton("Refresh")
        self.refresh.clicked.connect(self.refresh_ui)

        self.mid_widgets = QHBoxLayout()
        self.mid_widgets.addWidget(self.ppd_combo_box)
        self.mid_widgets.addWidget(self.group_combo_box)
        self.mid_widgets.addWidget(self.employee_combo_box)
        self.mid_widgets.addWidget(self.search)
        self.mid_widgets.addWidget(self.refresh)

        self.mid_layout = QVBoxLayout()
        self.mid_layout.addLayout(self.mid_widgets)

        self.setLayout(self.mid_layout)

        self.manager.init_finished.connect(self.combo_box_filler)
        self.manager.done.connect(self.refresh_ui)
        self.manager.db_dates.connect(self.dates_filler)
        self.manager.db_groups.connect(self.groups_filler)
        self.manager.db_names.connect(self.employee_filler)

    @asyncSlot()
    async def send_search(self):
        selected_date = self.ppd_combo_box.currentText().strip()
        selected_name = self.employee_combo_box.currentText().strip()

        if selected_name == "" or selected_name is None:
            await self.manager.start_query("_default_employee")

        else:
            name = tuple(self.__sanitize_name_for_db(selected_name))

        await self.manager.start_work_entry_query(name, selected_date)

    @asyncSlot()
    async def refresh_ui(self):
        self.manager.refresh_call()

    def make_combo_searchable(self, combo: QComboBox):
        model = QStringListModel([combo.itemText(i)
                                 for i in range(combo.count())])
        proxy_model = QSortFilterProxyModel(combo)
        proxy_model.setSourceModel(model)

        completer = QCompleter(proxy_model, combo)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        combo.setCompleter(completer)

    @asyncSlot()
    async def combo_box_filler(self):
        try:
            await self.manager.start_combo_box_query()

        except Exception as e:
            log.error(
                "Error during dump and compression: %s | %s",
                type(e).__name__,
                e.args,
            )

    def dates_filler(self, dates: list[tuple, ...]):
        try:
            for date in dates:
                self.ppd_combo_box.addItem(str(date[0]))

        except Exception as e:
            log.error(
                "Error during dump and compression: %s | %s",
                type(e).__name__,
                e.args,
            )

    def groups_filler(self, groups: list[tuple, ...]):
        try:
            for group in groups:
                self.group_combo_box.addItem(str(group[0]))

        except Exception as e:
            log.error(
                "Error during dump and compression: %s | %s",
                type(e).__name__,
                e.args,
            )

    def employee_filler(self, names: list[tuple, ...]):
        try:
            self.employee_combo_box.clear()
            for name in names:
                self.employee_combo_box.addItem(
                    ' '.join(' '.join(name).split())
                )

        except Exception as e:
            log.error(
                "Error during employee_filler: %s | %s",
                type(e).__name__,
                e.args,
            )

    def _on_group_changed(self, group: str):
        asyncio.create_task(
            self.manager.employee_combo_box_query(args=group.strip())
        )

    @asyncSlot(str)
    async def employee_names_setup(self, group: str):
        await self.manager.employee_combo_box_query(args=group)

    @staticmethod
    def __sanitize_name_for_db(employee: list):
        name = employee.split(" ")

        if len(name) < 3:
            name.insert(1, "")

        if len(name) > 3:
            name = [name[0], name[1], name[2] + " " + name[3]]

        if len(name[1]) >= 3 or re.search(pattern="JR(.|)", string=name[2]):
            if len(name[1]) > 1:
                name = [name[0], name[1] + " " + name[2]]

        if len(name) < 3:
            name.insert(1, "")

        return name
