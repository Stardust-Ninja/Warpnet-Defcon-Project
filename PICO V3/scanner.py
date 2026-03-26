import winreg
import socket
import subprocess
import time
import ctypes
import json

CVE_SCORES = {
    "FIREWALL_OFF": 7.5,
    "DEFENDER_OFF": 8.0,
    "DEFENDER_REALTIME_OFF": 9.0,
    "SERVICES_mpssvc": 6.5,
    "SERVICES_wscsvc": 5.0,
    "PORTS_21(FTP)": 7.0,
    "PORTS_23(TELNET)": 9.8,
    "PORTS_445(SMB)": 8.5,
    "PORTS_3389(RDP)": 7.8,
    "PORTS_5900(VNC)": 7.5,
    "MALWARE_mimikatz": 9.5,
    "MALWARE_pwdump": 9.0,
    "MALWARE_nc.exe": 6.0,
    "MULTIPLE_CRITICAL": 10.0,
    "CLEAR": 0.0
}

DANGEROUS_PORTS = [21, 23, 135, 139, 445, 3389, 5900]
SUSPICIOUS_NAMES = ["mimikatz", "pwdump", "nc.exe", "ncat", "meterpreter", "cryptinject", "ransomware"]

class SecurityScanner:
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
            return f"SERVICES_{stopped[0]}"
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
            return f"PORTS_{open_ports[0]}"
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
                return f"MALWARE_{found[0]}"
        except:
            pass
        return None

    def calculate_threat(self, findings):
        if not findings:
            return {"level": 5, "pattern": "GREEN", "info": "CLEAR", "cve_score": 0.0, "findings": []}
        
        malware = [f for f in findings if "MALWARE" in f]
        if malware:
            cve = CVE_SCORES.get(malware[0], 9.0)
            return {"level": 1, "pattern": "POLICE", "info": malware[0], "cve_score": cve, "findings": findings}
        
        critical = [f for f in findings if any(x in f for x in ["FIREWALL", "DEFENDER"])]
        if len(critical) >= 2:
            return {"level": 1, "pattern": "CHAOS", "info": "MULTIPLE_CRITICAL", "cve_score": 10.0, "findings": findings}
        
        if any("FIREWALL" in f for f in findings):
            return {"level": 2, "pattern": "RED_BLINK", "info": "FIREWALL_OFF", "cve_score": CVE_SCORES.get("FIREWALL_OFF", 7.5), "findings": findings}
        
        if any("DEFENDER_REALTIME" in f for f in findings):
            return {"level": 2, "pattern": "RED_BLINK", "info": "DEFENDER_REALTIME_OFF", "cve_score": CVE_SCORES.get("DEFENDER_REALTIME_OFF", 9.0), "findings": findings}
        
        if any("DEFENDER" in f for f in findings):
            return {"level": 2, "pattern": "RED_BLINK", "info": "DEFENDER_OFF", "cve_score": CVE_SCORES.get("DEFENDER_OFF", 8.0), "findings": findings}
        
        if any("SERVICES" in f for f in findings):
            svc = [f for f in findings if "SERVICES" in f][0]
            return {"level": 2, "pattern": "RED_YELLOW", "info": svc, "cve_score": CVE_SCORES.get(svc, 5.0), "findings": findings}
        
        if any("PORTS" in f for f in findings):
            port = [f for f in findings if "PORTS" in f][0]
            return {"level": 3, "pattern": "ORANGE_PULSE", "info": port, "cve_score": CVE_SCORES.get(port, 7.0), "findings": findings}
        
        return {"level": 4, "pattern": "WHITE_FLASH", "info": findings[0] if findings else "WARNING", "cve_score": 3.0, "findings": findings}

    def scan(self):
        findings = []
        checks = [("Firewall", self.check_firewall), ("Defender", self.check_defender), 
                 ("Realtime", self.check_defender_realtime), ("Services", self.check_services),
                 ("Ports", self.check_ports), ("Processes", self.check_processes)]
        
        for name, check_func in checks:
            result = check_func()
            if result:
                findings.append(result)
        
        results = self.calculate_threat(findings)
        results["timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S')
        return results

    def get_cve(self, threat):
        return CVE_SCORES.get(threat, 5.0)


if __name__ == "__main__":
    scanner = SecurityScanner()
    while True:
        r = scanner.scan()
        print(f"[{r['timestamp']}] Level {r['level']} | {r['pattern']} | CVE:{r['cve_score']} | {r['info']}")
        time.sleep(5)