import serial
import serial.tools.list_ports
import winreg
import socket
import subprocess
import time
import signal
import ctypes
import sys

BAUD_RATE = 115200
SCAN_INTERVAL = 5
VERBOSE = True

DANGEROUS_PORTS = [21, 23, 135, 139, 445, 3389, 5900]
SUSPICIOUS_NAMES = ["mimikatz", "pwdump", "nc.exe", "ncat", "meterpreter", "cryptinject", "ransomware"]

class SecurityMonitor:
    def __init__(self):
        self.ser = None
        self.running = True
        self.last_level = None
        self.last_pattern = None
        self.scan_count = 0
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
    
    def _shutdown(self, *args):
        print("\n[!] Shutting down...")
        self.running = False
    
    def find_pico(self):
        print("\n[+] Scanning for Pico...")
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            desc = p.description.lower()
            if any(x in desc for x in ['pico', 'circuitpy', 'rp2040', 'usb serial']):
                print(f"[+] Found Pico on {p.device}")
                return p.device
        
        print("\n[!] Pico not auto-detected. Available ports:")
        for i, p in enumerate(ports, 1):
            print(f"    {i}. {p.device}: {p.description}")
        
        choice = input("\n[?] Enter port number or COM name: ").strip()
        try:
            return ports[int(choice)-1].device
        except:
            return choice if "COM" in choice.upper() else None
    
    def connect(self):
        while self.running and not self.ser:
            port = self.find_pico()
            if not port:
                time.sleep(2)
                continue
            try:
                print(f"[+] Opening {port}...")
                self.ser = serial.Serial(port, BAUD_RATE, timeout=2)
                time.sleep(1.5)
                self.ser.reset_input_buffer()
                print(f"[+] Connected!")
                return True
            except serial.SerialException as e:
                if "Permission" in str(e):
                    print(f"[!] Port {port} in use")
                else:
                    print(f"[!] Error: {e}")
                time.sleep(3)
            except Exception as e:
                print(f"[!] Error: {e}")
                time.sleep(3)
        return False
    
    def check_firewall(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Services\SharedAccess\Parameters\FirewallPolicy\StandardProfile")
            enabled, _ = winreg.QueryValueEx(key, "EnableFirewall")
            winreg.CloseKey(key)
            if enabled == 0:
                return "FIREWALL_OFF"
        except:
            pass
        return None
    
    def check_defender(self):
        try:
            result = subprocess.run(["sc", "query", "WinDefend"], 
                                  capture_output=True, text=True, timeout=5)
            if "RUNNING" not in result.stdout:
                return "DEFENDER_OFF"
        except:
            pass
        return None
    
    def check_defender_realtime(self):
        """Check if Windows Defender Realtime Protection is actually enabled"""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows Defender\Real-Time Protection")
            disabled, _ = winreg.QueryValueEx(key, "DisableRealtimeMonitoring")
            winreg.CloseKey(key)
            if disabled == 1:
                return "DEFENDER_REALTIME_OFF"
        except:
            pass
        
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection")
            disabled, _ = winreg.QueryValueEx(key, "DisableRealtimeMonitoring")
            winreg.CloseKey(key)
            if disabled == 1:
                return "DEFENDER_REALTIME_OFF"
        except:
            pass
        
        return None
    
    def check_services(self):
        stopped = []
        for svc in ["mpssvc", "wscsvc"]:
            try:
                result = subprocess.run(["sc", "query", svc], 
                                      capture_output=True, text=True, timeout=3)
                if "RUNNING" not in result.stdout:
                    stopped.append(svc)
            except:
                pass
        if stopped:
            return f"SERVICES_{stopped}"
        return None
    
    def check_ports(self):
        open_ports = []
        port_names = {21: "FTP", 23: "TELNET", 135: "RPC", 139: "NETBIOS", 
                     445: "SMB", 3389: "RDP", 5900: "VNC"}
        for port in DANGEROUS_PORTS:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.15)
                if sock.connect_ex(('127.0.0.1', port)) == 0:
                    name = port_names.get(port, "UNK")
                    open_ports.append(f"{port}({name})")
                sock.close()
            except:
                pass
        if open_ports:
            return f"PORTS_{open_ports}"
        return None
    
    def check_processes(self):
        try:
            result = subprocess.run(["tasklist", "/FO", "CSV"], 
                                  capture_output=True, text=True, timeout=10)
            output = result.stdout.lower()
            found = []
            for bad in SUSPICIOUS_NAMES:
                if bad in output:
                    found.append(bad)
            if found:
                return f"MALWARE_{found}"
        except:
            pass
        return None
    
    def calculate_threat(self, findings):
        if not findings:
            return 5, "GREEN", "CLEAR"
        
        if any("MALWARE" in f for f in findings):
            return 1, "POLICE", findings[0]
        
        critical = [f for f in findings if any(x in f for x in ["FIREWALL", "DEFENDER"])]
        if len(critical) >= 2:
            return 1, "CHAOS", "MULTIPLE_CRITICAL"
        
        if any("FIREWALL" in f for f in findings):
            return 2, "RED_BLINK", "FIREWALL_OFF"
        if any("DEFENDER_REALTIME" in f for f in findings):
            return 2, "RED_BLINK", "DEFENDER_REALTIME_OFF"
        if any("DEFENDER" in f for f in findings):
            return 2, "RED_BLINK", "DEFENDER_OFF"
        if any("SERVICES" in f for f in findings):
            return 2, "RED_YELLOW", findings[0]
        if any("PORTS" in f for f in findings):
            return 3, "ORANGE_PULSE", findings[0]
        
        return 4, "WHITE_FLASH", findings[0] if findings else "WARNING"
    
    def send(self, level, pattern, info):
        if not self.ser or not self.ser.is_open:
            return False
        message = f"{level},{pattern},{info}"
        if VERBOSE or level != self.last_level or pattern != self.last_pattern:
            print(f"[TX] {message}")
            self.last_level = level
            self.last_pattern = pattern
        try:
            self.ser.write(message.encode() + b'\n')
            self.ser.flush()
            return True
        except Exception as e:
            print(f"[!] Send failed: {e}")
            self.ser = None
            return False
    
    def scan(self):
        self.scan_count += 1
        print(f"\n[SCAN #{self.scan_count}] {time.strftime('%H:%M:%S')}")
        
        findings = []
        
        checks = [
            ("Firewall", self.check_firewall),
            ("Defender Service", self.check_defender),
            ("Defender Realtime", self.check_defender_realtime),
            ("Services", self.check_services),
            ("Ports", self.check_ports),
            ("Processes", self.check_processes),
        ]
        
        for name, check in checks:
            result = check()
            if result:
                findings.append(result)
                print(f"  [!] {name}: {result}")
            else:
                if VERBOSE:
                    print(f"  [OK] {name}")
        
        level, pattern, info = self.calculate_threat(findings)
        
        if VERBOSE:
            print(f"  [RESULT] Level {level} | Pattern {pattern} | {info}")
        
        self.send(level, pattern, info)
        return level
    
    def run(self):
        print("=" * 50)
        print("SECURITY MONITOR")
        print(f"VERBOSE MODE: {'ON' if VERBOSE else 'OFF'}")
        print("=" * 50)
        
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("[!] Warning: Not running as Administrator")
            print("    Realtime Protection check may fail\n")
        
        if not self.connect():
            print("[!] Failed to connect to Pico")
            return
        
        print(f"\n[+] Starting monitoring...")
        
        while self.running:
            if not self.ser:
                if not self.connect():
                    break
            self.scan()
            
            if VERBOSE:
                for i in range(SCAN_INTERVAL, 0, -1):
                    if not self.running:
                        break
                    print(f"\r  [Next scan in {i}s...]", end="", flush=True)
                    time.sleep(1)
                print("\r" + " " * 30 + "\r", end="")
            else:
                time.sleep(SCAN_INTERVAL)
        
        if self.ser and self.ser.is_open:
            self.ser.close()
        print("[+] Stopped")

if __name__ == "__main__":
    monitor = SecurityMonitor()
    monitor.run()