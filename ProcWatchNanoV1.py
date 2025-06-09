
import psutil
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
import time

def getUptime():
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    now = datetime.now()
    uptime = now - boot_time
    return uptime

def generateHeader():
    header = Table.grid()
    header.add_column()
    header.add_column()

    header.add_row('Username:', psutil.users()[0].name)
    header.add_row('Uptime:', str(getUptime()))
    header.add_row('Physical Cores:', str(psutil.cpu_count(logical=False)))
    header.add_row('Logical Cores:', str(psutil.cpu_count()))
    header.add_row('Max Frequency:', f"{psutil.cpu_freq().max / 1000} GHz")
    header.add_row('Current Frequency:', f"{psutil.cpu_freq().current / 1000} GHz")
    header.add_row('Battery Percentage:', f"{psutil.sensors_battery().percent}%" if psutil.sensors_battery() else "N/A")

    return header

def generateTable():
    table = Table(title="PROCESSES")
    table.add_column('PID')
    table.add_column('Name')
    table.add_column('Status')
    table.add_column('CPU')
    table.add_column('Memory')
    table.add_column('Disk')
    table.add_column('Network')

    processes = list(psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_info', 'io_counters',
                                      'connections']))
    for proc in processes[:20]:
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            status = proc.info['status']
            cpu = proc.info['cpu_percent']
            memory = proc.info['memory_info'].rss / (1024 ** 2)  # Convert bytes to MB
            disk = proc.info['io_counters'].read_bytes / (1024 ** 2) if proc.info['io_counters'] else 0
            network = len(proc.info['connections']) if proc.info['connections'] else 0

            table.add_row(str(pid), name, status, f"{cpu}%", f"{memory:.2f} MB", f"{disk:.2f} MB", str(network))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return table

console = Console()
console.print("\n[bold]ProcWatchNano v1.0[/bold]\n", justify= 'center')

layout = Layout()
layout.split_column(
    Layout(name="top", ratio=1),
            Layout(name="bottom", size=14),
)

layout["bottom"].split_row(
    Layout(name="left"),
            Layout(name="right")
)
actions = """
    1. Kill a process by PID
    2. Start a new process
    3. Sort processes by CPU usage
    4. Sort processes by Memory usage
    5. Sort processes by Disk usage
    6. Sort processes by Name
    7. Sort processes by PID
"""

try:
    with Live(layout, refresh_per_second=1) as live:
        layout["right"].update(Align.left(Panel(actions, title="Actions")))
        while True:
            layout["left"].update(Align.right(Panel(generateHeader(), title="System Info")))
            layout["top"].update(Align.center(Panel(generateTable(), expand=False)))
            time.sleep(2)
except KeyboardInterrupt:
    console.print("\n[bold red]Stopped by user[/bold red]")

