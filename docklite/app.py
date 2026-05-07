from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QHeaderView,
    QAbstractItemView,
    QLabel,
    QMessageBox,
)

from docklite.docker_service import DockerService


class DockLiteWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.docker = DockerService()
        self.selected_container_name = None

        self.logs_timer = QTimer()
        self.logs_timer.setInterval(1000)
        self.logs_timer.timeout.connect(self.view_logs)

        self.setWindowTitle("DockLite")
        self.resize(1000, 700)

        self.setup_ui()
        self.refresh_containers()

    def setup_ui(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        sidebar_layout = QVBoxLayout()
        content_layout = QVBoxLayout()

        central_widget.setLayout(main_layout)
        main_layout.addLayout(sidebar_layout)
        main_layout.addLayout(content_layout)
        self.setCentralWidget(central_widget)

        sidebar_title = QLabel("DockLite")
        sidebar_title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            padding-bottom: 10px;
        """)

        self.refresh_button = QPushButton("Refresh Containers")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.restart_button = QPushButton("Restart")
        self.logs_button = QPushButton("View Logs")
        self.delete_button = QPushButton("Delete")

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Image", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.logs_title = QLabel("Logs")
        self.logs_box = QTextEdit()
        self.logs_box.setReadOnly(True)

        self.stats_label = QLabel("Stats: select a container")

        content_layout.addWidget(self.table)
        content_layout.addWidget(self.logs_title)
        content_layout.addWidget(self.logs_box)
        content_layout.addWidget(self.stats_label)

        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addWidget(self.refresh_button)
        sidebar_layout.addWidget(self.start_button)
        sidebar_layout.addWidget(self.stop_button)
        sidebar_layout.addWidget(self.restart_button)
        sidebar_layout.addWidget(self.delete_button)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.logs_button)

        self.table.cellClicked.connect(self.selected_container)
        self.refresh_button.clicked.connect(self.refresh_containers)
        self.start_button.clicked.connect(self.start_container)
        self.stop_button.clicked.connect(self.stop_container)
        self.restart_button.clicked.connect(self.restart_container)
        self.logs_button.clicked.connect(self.view_logs)
        self.delete_button.clicked.connect(self.delete_container)

    def show_error(self, message):
        QMessageBox.critical(self, "DockLite Error", message)

    def refresh_containers(self):
        try:
            containers = self.docker.list_containers()
            self.table.setRowCount(len(containers))

            for row, container in enumerate(containers):
                image = container.image.tags[0] if container.image.tags else "no tag"

                self.table.setItem(row, 0, QTableWidgetItem(container.name))
                self.table.setItem(row, 1, QTableWidgetItem(image))
                self.table.setItem(row, 2, QTableWidgetItem(container.status))

        except Exception as error:
            self.show_error(str(error))

    def selected_container(self, row, column):
        self.selected_container_name = self.table.item(row, 0).text()

        self.logs_timer.stop()
        self.logs_box.clear()
        self.stats_label.setText("Stats: loading...")

        self.update_container_stats()

    def update_container_stats(self):
        if self.selected_container_name is None:
            return

        try:
            stats = self.docker.stats(self.selected_container_name)

            memory_used = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 0)

            memory_used_mb = memory_used / 1024 / 1024
            memory_limit_mb = memory_limit / 1024 / 1024

            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )

            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )

            cpu_count = len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", []))

            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * cpu_count * 100
            else:
                cpu_percent = 0

            self.stats_label.setText(
                f"CPU: {cpu_percent:.2f}% | "
                f"Memory: {memory_used_mb:.2f} MB / {memory_limit_mb:.2f} MB"
            )

        except Exception as error:
            self.stats_label.setText(f"Stats error: {error}")

    def start_container(self):
        if self.selected_container_name is None:
            return

        try:
            self.docker.start(self.selected_container_name)
            self.refresh_containers()
            self.update_container_stats()
            self.view_logs()

        except Exception as error:
            self.show_error(str(error))

    def stop_container(self):
        if self.selected_container_name is None:
            return

        try:
            self.docker.stop(self.selected_container_name)

            self.logs_timer.stop()
            self.logs_box.clear()
            self.stats_label.setText("Stats: container stopped")

            self.refresh_containers()

        except Exception as error:
            self.show_error(str(error))

    def restart_container(self):
        if self.selected_container_name is None:
            return

        try:
            self.docker.restart(self.selected_container_name)
            self.refresh_containers()
            self.update_container_stats()
            self.view_logs()

        except Exception as error:
            self.show_error(str(error))

    def view_logs(self):
        if self.selected_container_name is None:
            return

        try:
            logs = self.docker.logs(self.selected_container_name)
            self.logs_box.setPlainText(logs)
            self.logs_timer.start()

        except Exception as error:
            self.show_error(str(error))

    def delete_container(self):
        if self.selected_container_name is None:
            return

        confirm = QMessageBox.question(
            self,
            "Delete Container",
            f"Delete container '{self.selected_container_name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            self.docker.delete(self.selected_container_name)

            self.selected_container_name = None
            self.logs_timer.stop()
            self.logs_box.clear()
            self.stats_label.setText("Stats: select a container")

            self.refresh_containers()

        except Exception as error:
            self.show_error(str(error))