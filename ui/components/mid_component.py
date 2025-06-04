import re

from qasync import asyncSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from structs.result import Result
from util.logger import CLogger
from util.pay_period_manager import PayPeriodManager
from util.task_manager import TaskManager

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class MidComponent(QWidget):
    def __init__(self, manager: TaskManager):
        super().__init__()

        self.pp_manager = PayPeriodManager()
        self.manager = manager

        self.ppd = QComboBox()
        self.ppd.setEditable(True)

        self.group = QComboBox()
        self.group.setEditable(True)

        self.employee = QComboBox()
        self.employee.setEditable(True)

        self.search = QPushButton("Search")
        self.search.clicked.connect(self.send_search)

        self.refresh = QPushButton("Refresh")
        self.refresh.clicked.connect(self.refresh_ui)

        self.mid_widgets = QHBoxLayout()
        self.mid_widgets.addWidget(self.ppd)
        self.mid_widgets.addWidget(self.group)
        self.mid_widgets.addWidget(self.employee)
        self.mid_widgets.addWidget(self.search)
        self.mid_widgets.addWidget(self.refresh)

        self.mid_layout = QVBoxLayout()
        self.mid_layout.addLayout(self.mid_widgets)

        self.setLayout(self.mid_layout)

        self.manager.done.connect(self.refresh_ui)

    @asyncSlot()
    async def send_search(self):
        selected_name = "ANGEL A ALANIZ"

        if selected_name == "" or selected_name is None:
            await self.manager.start_query(method_name="_default_employee")

        else:
            name = [tuple(self.__sanitize_name_for_db(selected_name),)]
            await self.manager.start_signal("db_result", name)

    @asyncSlot()
    async def refresh_ui(self):
        self.manager.refresh_call()

    @staticmethod
    def __sanitize_name_for_db(employee: str):
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
