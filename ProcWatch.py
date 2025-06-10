import sys
from datetime import datetime
import psutil
import shutil
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QApplication, QMainWindow, QHeaderView, QAbstractItemView, QMessageBox
from ui_procwatch import Ui_ProcWatch


class ProcWatch(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ProcWatch()
        self.ui.setupUi(self)
        self.initializeGrid()
        self.model = QStandardItemModel()
        self.initializeTable()
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateSystemInfo)
        self.timer.timeout.connect(self.update_processes)
        self.timer.start(10000)  # Update every 10 seconds
        self.ui.killBtn.clicked.connect(self.killProcess)

    def initializeGrid(self):
        username = psutil.users()[0].name
        battery = psutil.sensors_battery()
        battery_status = f"{battery.percent}%" if battery else "N/A"
        disk_usage = shutil.disk_usage("C:/")  # psutil's disk usage function is incompatible with the latest python
        # distro so using shutil
        disk_percent = (disk_usage.used / disk_usage.total) * 100
        disk_percent = f"{disk_percent:.2f}% of {disk_usage.total / (1024 ** 3):.2f} GB"
        physical_cores = str(psutil.cpu_count(logical=False))
        logical_cores = str(psutil.cpu_count())
        max_freq = f"{psutil.cpu_freq().max / 1000:.2f} GHz"

        self.ui.usernameDisplay.setText(username)
        self.ui.batteryDisplay.setText(battery_status)
        self.ui.diskUsageDisplay.setText(disk_percent)
        self.ui.physicalCoresDisplay.setText(physical_cores)
        self.ui.logicalCoresDisplay.setText(logical_cores)
        self.ui.maxFreqDisplay.setText(max_freq)

        self.updateSystemInfo()  # Initial system info update

    def updateSystemInfo(self):
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        now = datetime.now()
        uptime = now - boot_time
        uptime = str(uptime).split('.')[0]  # Remove microseconds
        current_freq = f"{psutil.cpu_freq().current / 1000:.2f} GHz"
        total_processes = str(len(list(psutil.process_iter())))
        cpu_usage = f"{psutil.cpu_percent(interval=1)}%"
        memory_used = f"{psutil.virtual_memory().percent}%"
        net_sent = f"{psutil.net_io_counters().bytes_sent / (1024 ** 2):.2f} MB"
        net_recv = f"{psutil.net_io_counters().bytes_recv / (1024 ** 2):.2f} MB"
        total_connections = str(len(psutil.net_connections()))

        self.ui.uptimeDisplay.setText(uptime)
        self.ui.currFreqDisplay.setText(current_freq)
        self.ui.totalProcessesDisplay.setText(total_processes)
        self.ui.cpuUsageDisplay.setText(cpu_usage)
        self.ui.memoryUsageDisplay.setText(memory_used)
        self.ui.netSentDisplay.setText(net_sent)
        self.ui.netRcvdDisplay.setText(net_recv)
        self.ui.totalConnDisplay.setText(total_connections)

    def initializeTable(self):
        # Setup model with headers
        self.model.setHorizontalHeaderLabels(
            ['PID', 'Name', 'Status', 'CPU %', 'Memory (MB)', 'Disk Read (MB)', 'Connections'])
        self.ui.processTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Set selection mode to select entire rows
        self.ui.processTable.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.update_processes()  # Initial update immediately
        # Set the model to the table view
        self.ui.processTable.setModel(self.model)

    def update_processes(self):
        self.model.removeRows(0, self.model.rowCount())  # Clear existing rows

        for proc in psutil.process_iter(
                ['pid', 'name', 'status', 'cpu_percent', 'memory_info', 'io_counters', 'connections']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                status = proc.info['status']
                cpu = proc.info['cpu_percent']
                mem = proc.info['memory_info'].rss / (1024 ** 2) if proc.info['memory_info'] else 0
                io = proc.info['io_counters']
                disk = io.read_bytes / (1024 ** 2) if io else 0
                net = len(proc.info['connections']) if proc.info['connections'] else 0

                row_data = [pid, name, status, cpu, mem, disk, net]

                items = []
                for attr in row_data:
                    item = QStandardItem()
                    item.setData(attr, Qt.ItemDataRole.DisplayRole)
                    item.setEditable(False)
                    items.append(item)

                self.model.appendRow(items)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def killProcess(self):
        selected_rows = self.ui.processTable.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select a process to kill.")
            return

        for index in selected_rows:
            pid_index = self.model.index(index.row(), 0)  # PID is in column 0
            pid = int(pid_index.data())

            try:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=3)
                QMessageBox.information(self, "Success", f"Terminated process with PID {pid}")
            except psutil.NoSuchProcess:
                QMessageBox.warning(self, "Error", f"No such process with PID {pid}")
            except psutil.AccessDenied:
                QMessageBox.critical(self, "Access Denied", f"Cannot terminate PID {pid}: Access Denied")
            except psutil.TimeoutExpired:
                QMessageBox.warning(self, "Timeout", f"Process PID {pid} did not terminate in time.")

        self.update_processes()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ProcWatch()
    window.show()
    sys.exit(app.exec())
