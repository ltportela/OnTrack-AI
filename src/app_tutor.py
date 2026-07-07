# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# Import OnTrackOrchestrator
from src.agents.orchestrator import OnTrackOrchestrator, RiskAssessmentPayload

app = FastAPI(
    title="OnTrack AI - Tutor Dashboard",
    description="Frontend dashboard layer for simulated student cohort evaluation under the IDSRAL protocol."
)

orchestrator = OnTrackOrchestrator()

# Load mock profiles from file for simulation seeding
MOCK_PROFILES_PATH = os.path.join("tests", "mock_cohort_profiles.json")
try:
    with open(MOCK_PROFILES_PATH, "r", encoding="utf-8") as f:
        MOCK_PROFILES = json.load(f)
except Exception:
    MOCK_PROFILES = []

# In-memory database to store historical evaluation logs
EVALUATION_LOGS: List[Dict[str, Any]] = []

class SimulateRequest(BaseModel):
    pseudo_id: str
    mslq_motivation_score: float
    burnout_index: float
    days_dormant: int
    simulation_risk_detected: bool
    raw_input_log: str

@app.get("/api/profiles")
def get_profiles():
    """Returns the mock profiles loaded from the project tests/mock_cohort_profiles.json."""
    return JSONResponse(content=MOCK_PROFILES)

@app.get("/api/logs")
def get_logs():
    """Returns the historical assessment logs."""
    return JSONResponse(content=EVALUATION_LOGS)

@app.post("/api/analyze")
def analyze_student(payload: SimulateRequest):
    """Executes the diagnostic pipeline including prompt injection check and stateful crisis circuit breaker."""
    # 1. Stateful Circuit Breaker check
    crisis_keywords = ["self-harm", "suicide", "suicidal", "emotional crisis", "domestic violence", "end everything", "hopelessness", "depression"]
    has_crisis = any(kw in payload.raw_input_log.lower() for kw in crisis_keywords)
    
    # 2. Prompt Injection Defense evaluation
    # Look for common jailbreak indicators like SYSTEM OVERRIDE, IGNORE, FORCE OUTPUT
    injection_keywords = ["system override", "ignore prior", "ignore instructions", "force output", "terminate task"]
    has_injection = any(kw in payload.raw_input_log.lower() for kw in injection_keywords)
    
    # Check if they attempted to manipulate risk level
    attempted_override = None
    if has_injection:
        if "low" in payload.raw_input_log.lower() and "risk" in payload.raw_input_log.lower():
            attempted_override = "Force risk level to 'LOW'"
    
    # Evaluate risk using structured orchestrator payload
    orchestrator_payload = RiskAssessmentPayload(
        pseudo_id=payload.pseudo_id,
        mslq_motivation_score=payload.mslq_motivation_score,
        burnout_index=payload.burnout_index,
        days_dormant=payload.days_dormant,
        simulation_risk_detected=payload.simulation_risk_detected
    )
    
    # Call the orchestrator
    orchestrator_raw = orchestrator.evaluate_retention_risk(orchestrator_payload)
    orchestrator_result = json.loads(orchestrator_raw)
    
    risk_level = orchestrator_result.get("risk_level", "LOW")
    primary_risk_driver = orchestrator_result.get("primary_risk_driver", "None")
    suggested_action_track = orchestrator_result.get("suggested_action_track", "Continue standard tracking")
    
    # If crisis bypass is active, normal action plan is halted and overridden
    if has_crisis:
        risk_level = "HIGH"
        primary_risk_driver = "STATEFUL CIRCUIT BREAKER: Psychological Crisis Vector"
        suggested_action_track = "HALT AUTOMATED FLOW: Immediately route case to 'Unidad de Apoyo al Estudiante' for emergency human intervention."
    
    # If injection was detected, we log it and ensure the risk level reflects actual metrics
    # Note: tests assert that even with injection payload, risk should be HIGH if metrics warrant it.
    
    response_data = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pseudo_id": payload.pseudo_id,
        "risk_level": risk_level,
        "primary_risk_driver": primary_risk_driver,
        "suggested_action_track": suggested_action_track,
        "crisis_detected": has_crisis,
        "injection_detected": has_injection,
        "attempted_override": attempted_override,
        "metrics": {
            "mslq_motivation_score": payload.mslq_motivation_score,
            "burnout_index": payload.burnout_index,
            "days_dormant": payload.days_dormant,
            "simulation_risk_detected": payload.simulation_risk_detected
        }
    }
    
    # Add to in-memory historical logs (keep last 50)
    EVALUATION_LOGS.insert(0, response_data)
    if len(EVALUATION_LOGS) > 50:
        EVALUATION_LOGS.pop()
        
    return JSONResponse(content=response_data)

@app.get("/", response_class=HTMLResponse)
def get_dashboard_index():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OnTrack AI - Tutor Retention Dashboard</title>
    <!-- Modern typography from Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            /* ADK Dark-Mode Color System */
            --bg-primary: #0a0c16;
            --bg-secondary: #12162b;
            --bg-tertiary: #191f3a;
            --border-color: rgba(255, 255, 255, 0.08);
            
            --text-primary: #f1f3f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --accent-glow: #38bdf8;
            --accent-glow-rgb: 56, 189, 248;
            
            --success-color: #10b981;
            --success-glow: rgba(16, 185, 129, 0.15);
            
            --error-color: #ef4444;
            --error-glow: rgba(239, 68, 68, 0.25);
            
            --warning-color: #f59e0b;
            --warning-glow: rgba(245, 158, 11, 0.15);
            
            --panel-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
            --transition-speed: 0.3s;
        }

        /* Crisis Override Styles */
        body.crisis-alert {
            --bg-primary: #1a080c;
            --bg-secondary: #2d0e14;
            --bg-tertiary: #3a151b;
            --border-color: rgba(239, 68, 68, 0.2);
            --accent-glow: #ef4444;
            --accent-glow-rgb: 239, 68, 68;
            --panel-shadow: 0 8px 40px 0 rgba(239, 68, 68, 0.15);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            transition: background-color var(--transition-speed), color var(--transition-speed);
            overflow-x: hidden;
        }

        /* Premium Glow Header Background */
        header {
            background: linear-gradient(to bottom, var(--bg-secondary), transparent);
            border-bottom: 1px solid var(--border-color);
            padding: 1.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            backdrop-filter: blur(10px);
            z-index: 10;
        }

        .header-title-section h1 {
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            background: linear-gradient(135deg, var(--text-primary) 30%, var(--accent-glow) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .header-title-section p {
            font-size: 0.825rem;
            color: var(--text-secondary);
            margin-top: 0.2rem;
        }

        .header-status {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .status-badge {
            background-color: var(--bg-tertiary);
            border: 1px solid var(--border-color);
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: var(--panel-shadow);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--success-color);
            box-shadow: 0 0 8px var(--success-color);
        }

        body.crisis-alert .status-dot {
            background-color: var(--error-color);
            box-shadow: 0 0 12px var(--error-color);
            animation: pulse-red 1.5s infinite;
        }

        @keyframes pulse-red {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.4; }
            100% { transform: scale(1); opacity: 1; }
        }

        /* Container & Layout Grid */
        main {
            flex: 1;
            max-width: 1400px;
            width: 100%;
            margin: 0 auto;
            padding: 2rem;
            display: grid;
            grid-template-columns: 420px 1fr;
            gap: 2rem;
        }

        /* Sidebar: Inputs & Profile Selector */
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .dashboard-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--panel-shadow);
            transition: all var(--transition-speed);
            backdrop-filter: blur(12px);
        }

        .dashboard-card h2 {
            font-size: 1.15rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
            border-left: 3px solid var(--accent-glow);
            padding-left: 0.75rem;
            color: var(--text-primary);
        }

        .form-group {
            margin-bottom: 1.25rem;
        }

        .form-group label {
            display: block;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .form-select, .form-input, .form-textarea {
            width: 100%;
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
            font-family: inherit;
            padding: 0.75rem;
            font-size: 0.9rem;
            transition: border-color var(--transition-speed), box-shadow var(--transition-speed);
        }

        .form-select:focus, .form-input:focus, .form-textarea:focus {
            outline: none;
            border-color: var(--accent-glow);
            box-shadow: 0 0 0 2px rgba(var(--accent-glow-rgb), 0.15);
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
            margin: 1.5rem 0;
            user-select: none;
        }

        .checkbox-group input {
            width: 18px;
            height: 18px;
            accent-color: var(--accent-glow);
        }

        .form-textarea {
            resize: vertical;
            min-height: 100px;
            font-family: 'Outfit', sans-serif;
            line-height: 1.4;
        }

        .btn {
            display: block;
            width: 100%;
            background: linear-gradient(135deg, var(--accent-glow) 0%, #1d4ed8 100%);
            border: none;
            border-radius: 8px;
            color: white;
            font-family: inherit;
            font-size: 0.95rem;
            font-weight: 600;
            padding: 0.875rem;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(var(--accent-glow-rgb), 0.2);
            transition: all var(--transition-speed) cubic-bezier(0.4, 0, 0.2, 1);
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(var(--accent-glow-rgb), 0.35);
        }

        .btn:active {
            transform: translateY(0);
        }

        /* Main Workspace: Diagnostics Console */
        .workspace {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        /* Banner styles for Stateful Circuit Breaker */
        .circuit-breaker-banner {
            border-radius: 12px;
            padding: 1.25rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            font-size: 0.95rem;
            border-left: 4px solid var(--success-color);
            background-color: rgba(16, 185, 129, 0.08);
            box-shadow: var(--panel-shadow);
            transition: all var(--transition-speed);
        }

        body.crisis-alert .circuit-breaker-banner {
            border-left-color: var(--error-color);
            background-color: rgba(239, 68, 68, 0.12);
            border-color: rgba(239, 68, 68, 0.25);
            animation: alert-border-pulse 2s infinite alternate;
        }

        @keyframes alert-border-pulse {
            0% { box-shadow: 0 0 5px rgba(239, 68, 68, 0.1); }
            100% { box-shadow: 0 0 25px rgba(239, 68, 68, 0.3); }
        }

        .banner-icon {
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .banner-content h3 {
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            margin-bottom: 0.2rem;
        }

        .banner-content p {
            font-size: 0.825rem;
            color: var(--text-secondary);
        }

        /* Output Grid Cards */
        .output-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        .risk-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.375rem 1rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            margin-top: 0.5rem;
        }

        .risk-badge.low {
            background-color: var(--success-glow);
            color: var(--success-color);
            border: 1px solid rgba(16, 185, 129, 0.2);
            box-shadow: 0 0 10px rgba(16, 185, 129, 0.1);
        }

        .risk-badge.high {
            background-color: var(--error-glow);
            color: var(--error-color);
            border: 1px solid rgba(239, 68, 68, 0.2);
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.15);
        }

        .result-details {
            margin-top: 1rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .result-field label {
            font-size: 0.725rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: block;
            margin-bottom: 0.25rem;
        }

        .result-field .value {
            font-size: 0.95rem;
            font-weight: 500;
            color: var(--text-primary);
        }

        /* Console styling for raw outputs and telemetry */
        .console-box {
            background-color: rgba(5, 7, 16, 0.8);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.825rem;
            line-height: 1.5;
            color: #10b981;
            overflow-x: auto;
            max-height: 140px;
        }

        .console-box.security-alert {
            color: var(--warning-color);
            background-color: rgba(245, 158, 11, 0.05);
            border-color: rgba(245, 158, 11, 0.2);
        }

        /* Logs Table */
        .logs-section {
            grid-column: span 2;
        }

        .logs-table-container {
            width: 100%;
            overflow-x: auto;
            margin-top: 1rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
            text-align: left;
        }

        th {
            background-color: var(--bg-tertiary);
            color: var(--text-secondary);
            font-weight: 600;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border-color);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }

        td {
            padding: 0.875rem 1rem;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-primary);
        }

        tr:hover td {
            background-color: rgba(255, 255, 255, 0.02);
        }

        .text-pill {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            display: inline-block;
        }

        .text-pill.risk-high { background-color: var(--error-glow); color: var(--error-color); }
        .text-pill.risk-low { background-color: var(--success-glow); color: var(--success-color); }
        .text-pill.warning { background-color: var(--warning-glow); color: var(--warning-color); }

        footer {
            margin-top: auto;
            border-top: 1px solid var(--border-color);
            padding: 1.5rem;
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-muted);
        }
    </style>
</head>
<body>
    <header>
        <div class="header-title-section">
            <h1>OnTrack AI <span>Tutor Retention Hub</span></h1>
            <p>Under Universidad Tecnológica del Sur de Sonora IDSRAL Protocol</p>
        </div>
        <div class="header-status">
            <div class="status-badge" id="circuit-badge">
                <span class="status-dot" id="circuit-dot"></span>
                <span id="circuit-text">System Stable</span>
            </div>
            <div class="status-badge">
                <span>Model: <strong>Gemini Flash</strong></span>
            </div>
        </div>
    </header>

    <main>
        <!-- Sidebar Controls -->
        <section class="sidebar">
            <div class="dashboard-card">
                <h2>Simulation Seed</h2>
                <div class="form-group">
                    <label for="profile-select">Load Mock Cohort Profile</label>
                    <select id="profile-select" class="form-select">
                        <option value="">-- Choose Profile to Seed parameters --</option>
                    </select>
                </div>
            </div>

            <div class="dashboard-card">
                <h2>Diagnostic parameters</h2>
                <form id="simulator-form">
                    <div class="form-group">
                        <label for="pseudo_id">Student Pseudo ID</label>
                        <input type="text" id="pseudo_id" class="form-input" required placeholder="student_sha256_xxx">
                    </div>

                    <div class="form-group">
                        <label for="mslq_score">MSLQ Motivation Score (0.0 - 1.0)</label>
                        <input type="number" id="mslq_score" class="form-input" min="0" max="1" step="0.01" required>
                    </div>

                    <div class="form-group">
                        <label for="burnout_index">Schaufeli Burnout Index (0.0 - 1.0)</label>
                        <input type="number" id="burnout_index" class="form-input" min="0" max="1" step="0.01" required>
                    </div>

                    <div class="form-group">
                        <label for="days_dormant">LMS Days Dormant</label>
                        <input type="number" id="days_dormant" class="form-input" min="0" required>
                    </div>

                    <div class="checkbox-group">
                        <input type="checkbox" id="simulation_risk">
                        <label for="simulation_risk" style="margin: 0; cursor: pointer;">Academic Simulation Risk Detected</label>
                    </div>

                    <div class="form-group">
                        <label for="raw_input">Raw Interactive Logs / Forum Telemetry</label>
                        <textarea id="raw_input" class="form-textarea" required placeholder="Type forum posts or student statements here..."></textarea>
                    </div>

                    <button type="submit" class="btn">Execute Diagnostic Pipeline</button>
                </form>
            </div>
        </section>

        <!-- Workspace Output Display -->
        <section class="workspace">
            <!-- Stateful Circuit Breaker Alert Banner -->
            <div class="circuit-breaker-banner" id="circuit-banner">
                <div class="banner-icon" id="banner-icon">🟢</div>
                <div class="banner-content">
                    <h3 id="banner-title">GUARDRAIL STATUS: STABLE</h3>
                    <p id="banner-description">Continuous passive profiling loop active. Zero-trust rules enforced.</p>
                </div>
            </div>

            <div class="output-grid">
                <!-- Risk Analysis Outcome -->
                <div class="dashboard-card">
                    <h2>Risk Evaluation Result</h2>
                    <div id="risk-level-container">
                        <span class="risk-badge low">LOW RISK</span>
                    </div>
                    <div class="result-details">
                        <div class="result-field">
                            <label>Primary Risk Drivers</label>
                            <div class="value" id="risk-drivers">None</div>
                        </div>
                        <div class="result-field">
                            <label>Suggested Action Track</label>
                            <div class="value" id="action-track">Continue standard automated tracking</div>
                        </div>
                    </div>
                </div>

                <!-- Context Hygiene & Security Monitor -->
                <div class="dashboard-card">
                    <h2>Security Sandboxing Monitor</h2>
                    <div style="margin-bottom: 1rem;">
                        <span class="text-pill" id="security-pill" style="background-color: var(--success-glow); color: var(--success-color);">🛡️ SECURE ENVIRONMENT</span>
                    </div>
                    <div class="result-details">
                        <div class="result-field">
                            <label>Context Isolation Engine</label>
                            <div class="value" style="font-size: 0.85rem; color: var(--text-secondary);">
                                Structured metrics (burnout, dormancy) are programmatically parsed. Input logs are quarantined from prompt execution instructions.
                            </div>
                        </div>
                        <div class="result-field">
                            <label>Injection Detection Output</label>
                            <div class="console-box" id="security-console">
                                [SYSTEM] Waiting for execution...
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Historical Audit Logs -->
                <div class="dashboard-card logs-section">
                    <h2>Historical Audit Log (Dynamic Telemetry)</h2>
                    <div class="logs-table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Student Pseudo ID</th>
                                    <th>Risk Level</th>
                                    <th>Crisis Bypass</th>
                                    <th>Security State</th>
                                    <th>Primary Driver</th>
                                </tr>
                            </thead>
                            <tbody id="logs-tbody">
                                <tr>
                                    <td colspan="6" style="text-align: center; color: var(--text-muted);">No evaluations executed yet. Use parameters on the left to simulate a profile.</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer>
        OnTrack AI Retention Framework • Powered by ADK & Vibecode • Universidad Tecnológica del Sur de Sonora
    </footer>

    <script>
        // State storage for mock profiles
        let profiles = [];

        // Elements
        const profileSelect = document.getElementById('profile-select');
        const simulatorForm = document.getElementById('simulator-form');
        const pseudoInput = document.getElementById('pseudo_id');
        const mslqInput = document.getElementById('mslq_score');
        const burnoutInput = document.getElementById('burnout_index');
        const daysInput = document.getElementById('days_dormant');
        const simCheckbox = document.getElementById('simulation_risk');
        const rawInput = document.getElementById('raw_input');

        // Output fields
        const circuitBadge = document.getElementById('circuit-badge');
        const circuitDot = document.getElementById('circuit-dot');
        const circuitText = document.getElementById('circuit-text');
        const circuitBanner = document.getElementById('circuit-banner');
        const bannerIcon = document.getElementById('banner-icon');
        const bannerTitle = document.getElementById('banner-title');
        const bannerDescription = document.getElementById('banner-description');

        const riskContainer = document.getElementById('risk-level-container');
        const riskDrivers = document.getElementById('risk-drivers');
        const actionTrack = document.getElementById('action-track');
        const securityPill = document.getElementById('security-pill');
        const securityConsole = document.getElementById('security-console');
        const logsTbody = document.getElementById('logs-tbody');

        // Load profiles from backend API
        async function fetchProfiles() {
            try {
                const response = await fetch('/api/profiles');
                profiles = await response.json();
                
                profiles.forEach((profile, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = profile.description;
                    profileSelect.appendChild(option);
                });
            } catch (err) {
                console.error("Failed to fetch cohort profiles", err);
            }
        }

        // Load logs from backend
        async function fetchLogs() {
            try {
                const response = await fetch('/api/logs');
                const logs = await response.json();
                renderLogs(logs);
            } catch (err) {
                console.error("Failed to fetch logs", err);
            }
        }

        // Render logs in the table
        function renderLogs(logs) {
            if (logs.length === 0) {
                logsTbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No evaluations executed yet.</td></tr>`;
                return;
            }

            logsTbody.innerHTML = logs.map(log => {
                const riskClass = log.risk_level === 'HIGH' ? 'risk-high' : 'risk-low';
                const crisisText = log.crisis_detected ? '<span class="text-pill risk-high">TRIGGERED</span>' : '<span style="color: var(--text-muted)">Stable</span>';
                
                let securityState = '<span style="color: var(--success-color);">🛡️ Secure</span>';
                if (log.injection_detected) {
                    securityState = '<span class="text-pill warning" title="Attempted instruction override was blocked">⚠️ Blocked Injection</span>';
                }

                return `
                    <tr>
                        <td><span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: var(--text-secondary);">${log.timestamp}</span></td>
                        <td><span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem;">${log.pseudo_id}</span></td>
                        <td><span class="text-pill ${riskClass}">${log.risk_level} RISK</span></td>
                        <td>${crisisText}</td>
                        <td>${securityState}</td>
                        <td style="color: var(--text-secondary); max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${log.primary_risk_driver}</td>
                    </tr>
                `;
            }).join('');
        }

        // Handle profile selection populate
        profileSelect.addEventListener('change', (e) => {
            const index = e.target.value;
            if (index === '') {
                simulatorForm.reset();
                return;
            }

            const p = profiles[index];
            pseudoInput.value = p.pseudo_id;
            mslqInput.value = p.mslq_motivation_score;
            burnoutInput.value = p.burnout_index;
            daysInput.value = p.days_dormant;
            simCheckbox.checked = p.simulation_risk_detected;
            rawInput.value = p.raw_input_log;
        });

        // Form Submit simulation execution
        simulatorForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const payload = {
                pseudo_id: pseudoInput.value,
                mslq_motivation_score: parseFloat(mslqInput.value),
                burnout_index: parseFloat(burnoutInput.value),
                days_dormant: parseInt(daysInput.value),
                simulation_risk_detected: simCheckbox.checked,
                raw_input_log: rawInput.value
            };

            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                updateUI(result);
                await fetchLogs();
            } catch (err) {
                console.error("Analysis execution error", err);
                alert("Critical error invoking the retention orchestrator.");
            }
        });

        // Update the dashboard UI based on simulation results
        function updateUI(data) {
            // Update Body Class for Red Alert Layout
            if (data.crisis_detected) {
                document.body.classList.add('crisis-alert');
                
                // Update Circuit Breaker UI
                circuitText.textContent = "CRISIS INTERVENTION ACTIVE";
                circuitText.style.color = "var(--error-color)";
                circuitBanner.style.borderColor = "var(--error-color)";
                bannerIcon.textContent = "🚨";
                bannerTitle.textContent = "STATEFUL CIRCUIT BREAKER TRIGGERED";
                bannerTitle.style.color = "var(--error-color)";
                bannerDescription.textContent = "Severe emotional crisis or safety hazard detected. Processing bypassed and immediately routed to: 'Unidad de Apoyo al Estudiante'.";
            } else {
                document.body.classList.remove('crisis-alert');
                
                // Reset Circuit Breaker UI
                circuitText.textContent = "System Stable";
                circuitText.style.color = "var(--text-primary)";
                bannerIcon.textContent = "🟢";
                bannerTitle.textContent = "GUARDRAIL STATUS: STABLE";
                bannerTitle.style.color = "var(--text-primary)";
                bannerDescription.textContent = "Continuous passive profiling loop active. Zero-trust rules enforced.";
            }

            // Update Risk Outcome
            if (data.risk_level === 'HIGH') {
                riskContainer.innerHTML = `<span class="risk-badge high">HIGH RISK</span>`;
            } else {
                riskContainer.innerHTML = `<span class="risk-badge low">LOW RISK</span>`;
            }
            
            riskDrivers.textContent = data.primary_risk_driver;
            actionTrack.textContent = data.suggested_action_track;

            // Update Security Panel
            if (data.injection_detected) {
                securityPill.textContent = "⚠️ OVERRIDE ATTEMPT BLOCKED";
                securityPill.style.backgroundColor = "var(--warning-glow)";
                securityPill.style.color = "var(--warning-color)";
                
                let consoleOutput = `[ALERT] Prompt injection payload detected in raw text stream!\n`;
                if (data.attempted_override) {
                    consoleOutput += `[ATTEMPT] Malicious intent: "${data.attempted_override}"\n`;
                }
                consoleOutput += `[ACTION] Zero-trust validation active. Instruction tokens isolated.\n`;
                consoleOutput += `[ENFORCEMENT] Analyzed actual cohort variables: Risk level evaluated safely.`;
                
                securityConsole.className = "console-box security-alert";
                securityConsole.textContent = consoleOutput;
            } else {
                securityPill.textContent = "🛡️ SECURE ENVIRONMENT";
                securityPill.style.backgroundColor = "var(--success-glow)";
                securityPill.style.color = "var(--success-color)";
                
                securityConsole.className = "console-box";
                securityConsole.textContent = `[SYSTEM] Processing complete.\n[TELEMETRY] No injection patterns found in raw log.\n[ISOLATION] Context hygiene safe.`;
            }
        }

        // Run on load
        fetchProfiles();
        fetchLogs();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    # Start web dashboard server locally or in production
    import os
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8050))
    print(f"=== [Vibecode Dashboard] Starting OnTrack AI Tutor Retention Interface on {host}:{port} ===")
    uvicorn.run(app, host=host, port=port)
