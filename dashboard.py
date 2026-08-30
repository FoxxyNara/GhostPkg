from flask import Flask, request, jsonify, render_template_string
import datetime

app = Flask(__name__)
alerts = [] # Stores alerts in memory for the demo

# Dark-mode enterprise UI 
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GhostPkg | CISO Telemetry</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 30px; }
        h1 { color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 10px; font-weight: 400; }
        .alert { background-color: #21262d; border-left: 4px solid #f85149; padding: 15px; margin-bottom: 15px; border-radius: 4px; font-family: monospace; box-shadow: 0 4px 6px rgba(0,0,0,0.3);}
        .critical { color: #f85149; font-weight: bold; font-size: 1.1em;}
        .timestamp { color: #8b949e; margin-right: 10px; }
        .details { margin-top: 8px; color: #a5d6ff; }
    </style>
    <script>
        // Polls the server every 1 second to update the UI instantly
        async function fetchAlerts() {
            try {
                const response = await fetch('/api/alerts');
                const data = await response.json();
                const container = document.getElementById('alerts-container');
                container.innerHTML = '';
                if (data.alerts.length === 0) {
                    container.innerHTML = '<p style="color: #484f58;">[System Online] Waiting for telemetry events...</p>';
                }
                data.alerts.forEach(alert => {
                    container.innerHTML += `
                        <div class="alert">
                            <span class="timestamp">[${alert.timestamp}]</span>
                            <span class="critical">ZERO-DAY BLOCKED: ${alert.package}</span> <br>
                            <div class="details">
                                > Defense Layer: Tier ${alert.stage === 'pypi' ? '1 (Registry)' : (alert.stage === 'static_scan' ? '2 (AST)' : '3 (Sandbox)')} <br>
                                > AI Correction: ${alert.action} <br>
                                > Threat Detail: ${alert.message}
                            </div>
                        </div>
                    `;
                });
            } catch (e) {}
        }
        setInterval(fetchAlerts, 1000);
        window.onload = fetchAlerts;
    </script>
</head>
<body>
    <h1>🛡️ GhostPkg | Enterprise Threat Telemetry</h1>
    <div id="alerts-container"></div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/alerts')
def get_alerts():
    return jsonify({"alerts": alerts[::-1]}) # Reverses the list so newest is on top

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receives threat data from GhostPkg CLI and pushes it to the dashboard."""
    data = request.json
    data['timestamp'] = datetime.datetime.now().strftime("%H:%M:%S")
    alerts.append(data)
    return {"status": "ok"}

if __name__ == '__main__':
    # Runs the dashboard on port 5000
    print("[+] CISO Dashboard running at http://localhost:5000")
    app.run(port=5000, debug=False)