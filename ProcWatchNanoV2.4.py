from rich.panel import Panel
from textual.widgets import Static, DataTable
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer
import shutil
import psutil
from datetime import datetime


class SystemInfoPanel(Static):
    def on_mount(self):
        self.set_interval(1, lambda: self.update(
            Panel(self.get_system_info(),
                  title='💻 SYSTEM-WIDE METRICS',
                  title_align='left',
                  border_style="bright_cyan",
                  padding=(1, 2))
        ))

    def get_uptime(self):
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        now = datetime.now()
        uptime = now - boot_time
        return uptime

    def get_system_info(self) -> str:
        battery = psutil.sensors_battery()
        battery_status = f"[green]{battery.percent}%[/green]" if battery else "[red]N/A[/red]"
        sort_key = self.app.query_one(ProcessTable).sort_key
        disk_usage = shutil.disk_usage("C:/")
        disk_percent = (disk_usage.used / disk_usage.total) * 100

        return (
            f"[b magenta]👤 Username:[/b magenta] [bold]{psutil.users()[0].name}[/bold]\n"
            f"[b magenta]⏱  Uptime:[/b magenta] [bold]{str(self.get_uptime()).split('.')[0]}[/bold]\n"
            f"[b magenta]⚙️ Physical Cores:[/b magenta] [bold]{psutil.cpu_count(logical=False)}[/bold]\n"
            f"[b magenta]🧠 Logical Cores:[/b magenta] [bold]{psutil.cpu_count()}[/bold]\n"
            f"[b magenta]🚀 Max Frequency:[/b magenta] [bold]{psutil.cpu_freq().max / 1000:.2f} GHz[/bold]\n"
            f"[b magenta]🎯 Current Frequency:[/b magenta] [bold]{psutil.cpu_freq().current / 1000:.2f} GHz[/bold]\n"
            f"[b magenta]🔋 Battery:[/b magenta] {battery_status}\n"
            f"[b magenta]🔀 Sorted on:[/b magenta] [bold]{sort_key.upper()}[/bold]\n"
            f"[b magenta]📦 Total Processes:[/b magenta] [bold]{len(list(psutil.process_iter()))}[/bold]\n"
            f"[b magenta]🔥 CPU Usage:[/b magenta] [bold yellow]{psutil.cpu_percent(interval=1)}%[/bold yellow]\n"
            f"[b magenta]🧾 Memory Used:[/b magenta] [bold yellow]{psutil.virtual_memory().percent}%[/bold yellow]\n"
            f"[b magenta]💽 Disk Used:[/b magenta] [bold yellow]{disk_percent:.2f}%[/bold yellow]\n"
            f"[b magenta]📤 Net Sent:[/b magenta] [bold green]{psutil.net_io_counters().bytes_sent / (1024 ** 2):.2f} MB[/bold green]\n"
            f"[b magenta]📥 Net Received:[/b magenta] [bold green]{psutil.net_io_counters().bytes_recv / (1024 ** 2):.2f} MB[/bold green]\n"
            f"[b magenta]🔗 Total Connections:[/b magenta] [bold]{len(psutil.net_connections())}[/bold]"
        )

class ProcessTable(DataTable):
    def on_mount(self):
        self.sort_key = "cpu"  # default sort field
        self.reverse = True  # Default sort direction for CPU usage
        self.sort_map = {
            "1": ("pid", False),
            "2": ("name", False),
            "3": ("status", False),
            "4": ("cpu", True),
            "5": ("memory", True),
            "6": ("disk", True),
            "7": ("network", True),
        }
        self.columns_order = ["pid", "name", "status", "cpu", "memory", "disk", "network"]

        self.add_columns(
            "[b cyan]PID[/b cyan]",
            "[b cyan]Name[/b cyan]",
            "[b cyan]Status[/b cyan]",
            "[b cyan]CPU %[/b cyan]",
            "[b cyan]Memory MB[/b cyan]",
            "[b cyan]Disk MB[/b cyan]",
            "[b cyan]Network[/b cyan]"
        )
        self.set_interval(8, self.update_processes)

    def update_processes(self):
        processes = []

        for proc in psutil.process_iter(
                ['pid', 'name', 'status', 'cpu_percent', 'memory_info', 'io_counters', 'connections']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                status = proc.info['status']
                cpu = proc.info['cpu_percent']
                mem = proc.info['memory_info'].rss / (1024 ** 2)  # MB
                io = proc.info['io_counters']
                disk = io.read_bytes / (1024 ** 2) if io else 0  # MB
                net = len(proc.info['connections']) if proc.info['connections'] else 0

                processes.append([pid, name, status, cpu, mem, disk, net])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        index = self.columns_order.index(self.sort_key)
        processes.sort(key=lambda row: row[index], reverse=self.reverse)

        top = processes[:50]

        data = []
        for row in top:
            pid, name, status, cpu, mem, disk, net = row
            # Color CPU & Memory usage based on thresholds
            cpu_color = "red" if cpu > 50 else "yellow" if cpu > 20 else "green"
            mem_color = "red" if mem > 500 else "yellow" if mem > 200 else "green"
            data.append(
                [
                    str(pid),
                    name,
                    status,
                    f"[{cpu_color}]{cpu:.1f}%[/]",
                    f"[{mem_color}]{mem:.1f} MB[/]",
                    f"{disk:.1f} MB",
                    str(net)
                ]
            )

        self.clear()
        self.add_rows(data)

    def on_key(self, event):
        key = event.key
        if key in self.sort_map:
            self.sort_key, self.reverse = self.sort_map[key]


class ProcWatchNanoV2(App):
    CSS = """
    Screen {
        layout: vertical;
        background: #1e1e2e;
        color: white;
    }

    .info {
        height: 24;
        layout: horizontal;
        padding: 1 2;
        border: tall $accent;
        width: 1fr;
    }

    .table {
        height: 1fr;
        overflow: auto;
        padding: 1 2;
        border: round $primary;
    }

    Header, Footer {
        background: $accent;
        color: black;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, name="ProcWatch v2")
        yield Vertical(
                SystemInfoPanel(classes="info"),
                        ProcessTable(classes="table"),
        )
        yield Footer()


if __name__ == "__main__":
    ProcWatchNanoV2().run()
