import scapy.all as scapy
import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def scan(ip_range):
    print(f"Scanning {ip_range} ...")
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

local_ip = get_local_ip()
# Build range e.g. 192.168.1.0/24
ip_range = ".".join(local_ip.split(".")[:3]) + ".0/24"

print(f"Your IP: {local_ip}")
print(f"Scanning range: {ip_range}\n")

devices = scan(ip_range)
print(f"Found {len(devices)} devices:")
for d in devices:
    print(f"  IP: {d['ip']:<16} MAC: {d['mac']:<20} Hostname: {d['hostname']}")