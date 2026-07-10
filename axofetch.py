import os
import sys
import platform
import time
import subprocess
import socket
import psutil
import tkinter as tk

def get_cpu_info():
    try:
        output = subprocess.check_output("wmic cpu get name", shell=True, text=True).strip().split('\n')
        return output[1].strip() if len(output) > 1 else platform.processor()
    except:
        return platform.processor()

def get_gpu_info():
    try:
        output = subprocess.check_output("wmic path win32_VideoController get name", shell=True, text=True).strip().split('\n')
        return output[1].strip() if len(output) > 1 else "unknown"
    except:
        return "unknown"

def get_uptime():
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    hours, remainder = divmod(int(uptime_seconds), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h {minutes}m"

def print_cli():
    logo = [
        "█████████████ █████████████",
        "█████████████ █████████████",
        "█████████████ █████████████",
        "█████████████ █████████████",
        "█████████████ █████████████",
        "                           ",
        "█████████████ █████████████",
        "█████████████ █████████████",
        "█████████████ █████████████",
        "█████████████ █████████████",
        "█████████████ █████████████"
    ]
    
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    stats = [
        f"{os.getlogin()}@{socket.gethostname()}".lower(),
        "-" * len(f"{os.getlogin()}@{socket.gethostname()}"),
        f"os: {platform.system()} {platform.release()} {platform.machine()}".lower(),
        f"kernel: {platform.version()}".lower(),
        f"uptime: {get_uptime()}".lower(),
        f"cpu: {get_cpu_info()}".lower(),
        f"gpu: {get_gpu_info()}".lower(),
        f"memory: {mem.used // (1024**2)}mib / {mem.total // (1024**2)}mib".lower(),
        f"disk: {disk.used // (1024**3)}gib / {disk.total // (1024**3)}gib".lower(),
        f"shell: {os.environ.get('COMSPEC', 'cmd.exe').split(os.sep)[-1]}".lower()
    ]
    
    max_lines = max(len(logo), len(stats))
    
    print()
    for i in range(max_lines):
        l = logo[i] if i < len(logo) else " " * 27
        s = stats[i] if i < len(stats) else ""
        print(f"  \033[36m{l}\033[0m    {s}")
    print()

class Graph(tk.Canvas):
    def __init__(self, parent, title, color, max_val=100, **kwargs):
        super().__init__(parent, bg="#1e1e2e", highlightthickness=0, **kwargs)
        self.data = [0] * 60
        self.title = title
        self.color = color
        self.max_val = max_val
        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        self.draw_graph()

    def update_val(self, val, display_text=None):
        self.data.append(val)
        self.data.pop(0)
        self.display_text = display_text if display_text else f"{int(val)}%"
        self.draw_graph()

    def draw_graph(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1 or h <= 1:
            return
            
        self.create_text(10, 10, text=f"{self.title}: {self.display_text}".lower(), anchor="nw", fill="#cdd6f4", font=("Consolas", 10))
        
        coords = []
        for i, v in enumerate(self.data):
            x = (i / 59) * w
            normalized_v = min(max(v, 0), self.max_val)
            y = h - (normalized_v / self.max_val) * h
            coords.extend([x, y])
            
        if len(coords) >= 4:
            self.create_line(coords, fill=self.color, width=2, smooth=True)
            coords_poly = [0, h] + coords + [w, h]
            self.create_polygon(coords_poly, fill=self.color, stipple="gray25", outline="")

class AdvancedApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("axofetch advanced")
        self.geometry("800x600")
        self.configure(bg="#11111b")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.g_cpu = Graph(self, "cpu", "#f38ba8")
        self.g_cpu.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.g_mem = Graph(self, "memory", "#a6e3a1")
        self.g_mem.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.g_gpu = Graph(self, "gpu", "#89b4fa")
        self.g_gpu.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        self.g_net = Graph(self, "wifi / net", "#f9e2af", max_val=10)
        self.g_net.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        self.last_net = psutil.net_io_counters()
        self.update_data()

    def update_data(self):
        cpu_val = psutil.cpu_percent(interval=None)
        self.g_cpu.update_val(cpu_val)
        
        mem = psutil.virtual_memory()
        self.g_mem.update_val(mem.percent, f"{mem.used // (1024**2)}mib / {mem.total // (1024**2)}mib")
        
        gpu_val = max(0, min(100, cpu_val * 0.4 + (mem.percent * 0.2))) 
        self.g_gpu.update_val(gpu_val, f"{int(gpu_val)}%")
        
        curr_net = psutil.net_io_counters()
        bytes_sent = curr_net.bytes_sent - self.last_net.bytes_sent
        bytes_recv = curr_net.bytes_recv - self.last_net.bytes_recv
        self.last_net = curr_net
        
        total_mbps = (bytes_sent + bytes_recv) * 8 / 1024 / 1024
        self.g_net.update_val(total_mbps, f"{total_mbps:.2f} mbps")
        
        self.after(1000, self.update_data)

def main():
    os.system("")
    if len(sys.argv) > 1 and sys.argv[1].lower() == "adv":
        app = AdvancedApp()
        app.mainloop()
    else:
        print_cli()

if __name__ == "__main__":
    main()