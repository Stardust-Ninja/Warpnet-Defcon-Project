from flask import Flask, jsonify
from scanner import SecurityScanner
import socket

app = Flask(__name__)
scanner = SecurityScanner()

@app.route('/api/security/status', methods=['GET'])
def get_status():
    status = scanner.scan()
    status["hostname"] = socket.gethostname()
    return jsonify(status)

@app.route('/api/security/scan', methods=['POST'])
def trigger_scan():
    status = scanner.scan()
    status["hostname"] = socket.gethostname()
    return jsonify(status)

@app.route('/api/cve/<threat>', methods=['GET'])
def get_cve(threat):
    score = scanner.get_cve(threat)
    severity = "CRITICAL" if score >= 9 else "HIGH" if score >= 7 else "MEDIUM" if score >= 4 else "LOW"
    return jsonify({"threat": threat, "cve_score": score, "severity": severity})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "security-api"})

if __name__ == '__main__':
    print("API Server on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)