import tkinter as tk
from tkinter import ttk, messagebox
import threading
import socket
import scapy.all as scapy

# ── Theme ───────────────────────────────────────────
BG = "#1e1e2e"
CARD = "#2a2a3e"
ACCENT = "#00b4d8"
TEXT = "#ffffff"
SUBTEXT = "#aaaacc"
GREEN = "#4caf50"
RED = "#ef5350"
YELLOW = "#ffd166"

# ── Root ─────────────────────────────────────────────
root = tk.Tk()
root.title("🌐 Network Scanner")
root.geometry("800x650")
root.configure(bg=BG)
root.resizable(False, False)

# ── Style ────────────────────────────────────────────
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background=CARD, foreground=TEXT,
    fieldbackground=CARD, rowheight=28, font=("Segoe UI", 10))
style.configure("Treeview.Heading", background=ACCENT, foreground=TEXT,
    font=("Segoe UI", 10, "bold"))
style.map("Treeview", background=[("selected", ACCENT)])

# ── Helpers ──────────────────────────────────────────
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def scan_network(ip_range):
    arp = scapy.ARP(pdst=ip_range)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = broadcast / arp
    result = scapy.srp(packet, timeout=2, verbose=False)[0]

    devices = []
    for sent, received in result:
        try:
            hostname = socket.gethostbyaddr(received.psrc)[0]
        except:
            hostname = "Unknown"
        devices.append({
            "ip": received.psrc,
            "mac": received.hwsrc,
            "hostname": hostname
        })
    return devices

def scan_ports(ip, ports):
    open_ports = []
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((ip, port)) == 0:
                try:
                    service = socket.getservbyport(port)
                except:
                    service = "unknown"
                open_ports.append((port, service))
            s.close()
        except:
            pass
    return open_ports

# ── Scan Logic ───────────────────────────────────────
def run_scan():
    scan_btn.config(state="disabled")
    status_var.set("Scanning network...")
    for row in device_table.get_children():
        device_table.delete(row)
    for row in port_table.get_children():
        port_table.delete(row)
    port_status_var.set("")
    root.update()

    def task():
        local_ip = get_local_ip()
        ip_range = ".".join(local_ip.split(".")[:3]) + ".0/24"
        devices = scan_network(ip_range)

        root.after(0, lambda: populate_devices(devices, local_ip))

    threading.Thread(target=task, daemon=True).start()

def populate_devices(devices, local_ip):
    for d in devices:
        tag = "self" if d["ip"] == local_ip else ""
        device_table.insert("", "end", values=(
            d["ip"], d["mac"], d["hostname"]
        ), tags=(tag,))

    device_table.tag_configure("self", foreground=YELLOW)
    status_var.set(f"Found {len(devices)} devices on your network  —  Your IP: {local_ip}")
    scan_btn.config(state="normal")

def on_device_select(event):
    selected = device_table.selection()
    if not selected:
        return
    ip = device_table.item(selected[0])["values"][0]
    port_status_var.set(f"Scanning ports on {ip}...")
    for row in port_table.get_children():
        port_table.delete(row)
    root.update()

    common_ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143,
                    443, 445, 3389, 8080, 8443]

    def task():
        open_ports = scan_ports(ip, common_ports)
        root.after(0, lambda: populate_ports(ip, open_ports))

    threading.Thread(target=task, daemon=True).start()

def populate_ports(ip, open_ports):
    if not open_ports:
        port_status_var.set(f"No common open ports found on {ip}")
        return
    for port, service in open_ports:
        port_table.insert("", "end", values=(port, service.upper()))
    port_status_var.set(f"Found {len(open_ports)} open port(s) on {ip}")

# ── Header ───────────────────────────────────────────
header = tk.Frame(root, bg=ACCENT, pady=15)
header.pack(fill="x")
tk.Label(header, text="🌐  Network Scanner",
         font=("Segoe UI", 22, "bold"), bg=ACCENT, fg=TEXT).pack()
tk.Label(header, text="Discover devices and open ports on your local network",
         font=("Segoe UI", 10), bg=ACCENT, fg="#ddd").pack()

# ── Scan Button ──────────────────────────────────────
btn_frame = tk.Frame(root, bg=BG)
btn_frame.pack(pady=12)

scan_btn = tk.Button(btn_frame, text="🔍  Scan Network", command=run_scan,
    bg=GREEN, fg=TEXT, font=("Segoe UI", 11, "bold"),
    relief="flat", padx=20, pady=8, cursor="hand2")
scan_btn.pack()

status_var = tk.StringVar(value="Click 'Scan Network' to begin")
tk.Label(root, textvariable=status_var, font=("Segoe UI", 9),
         bg=BG, fg=SUBTEXT).pack()

# ── Device Table ─────────────────────────────────────
tk.Label(root, text="Devices Found", font=("Segoe UI", 12, "bold"),
         bg=BG, fg=ACCENT).pack(anchor="w", padx=20, pady=(10, 3))

device_frame = tk.Frame(root, bg=BG)
device_frame.pack(fill="x", padx=20)

device_cols = ("IP Address", "MAC Address", "Hostname")
device_table = ttk.Treeview(device_frame, columns=device_cols,
    show="headings", height=7)
for col in device_cols:
    device_table.heading(col, text=col)
    device_table.column(col, width=240, anchor="center")
device_table.pack(fill="x")
device_table.bind("<<TreeviewSelect>>", on_device_select)

tk.Label(root, text="↑ Click a device to scan its ports",
         font=("Segoe UI", 8, "italic"), bg=BG, fg=SUBTEXT).pack(anchor="w", padx=20)

# ── Port Table ───────────────────────────────────────
port_header = tk.Frame(root, bg=BG)
port_header.pack(fill="x", padx=20, pady=(10, 3))
tk.Label(port_header, text="Open Ports", font=("Segoe UI", 12, "bold"),
         bg=BG, fg=ACCENT).pack(side="left")

port_status_var = tk.StringVar()
tk.Label(root, textvariable=port_status_var, font=("Segoe UI", 9),
         bg=BG, fg=SUBTEXT).pack(anchor="w", padx=20)

port_frame = tk.Frame(root, bg=BG)
port_frame.pack(fill="x", padx=20)

port_cols = ("Port", "Service")
port_table = ttk.Treeview(port_frame, columns=port_cols,
    show="headings", height=5)
port_table.heading("Port", text="Port")
port_table.heading("Service", text="Service")
port_table.column("Port", width=100, anchor="center")
port_table.column("Service", width=620, anchor="center")
port_table.pack(fill="x")

root.mainloop()