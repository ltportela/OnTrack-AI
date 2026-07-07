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

import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.models.llm_response import LlmResponse

from app.tools import (
    fetch_lms_telemetry,
    fetch_school_control_grades,
    fetch_psychometric_metrics,
    dispatch_intervention_alert,
    sanitize_text
)

load_dotenv()

async def pii_sanitization_callback(callback_context) -> None:
    """Pre-processes incoming user events to hash any real names, emails, or student IDs."""
    events = callback_context.session.events
    if events:
        last_event = events[-1]
        if last_event.author == "user" and last_event.content and last_event.content.parts:
            for part in last_event.content.parts:
                if part.text:
                    part.text = sanitize_text(part.text)
                    
    user_content = callback_context.user_content
    if user_content and user_content.parts:
        for part in user_content.parts:
            if part.text:
                part.text = sanitize_text(part.text)

async def crisis_circuit_breaker_callback(callback_context, llm_request) -> LlmResponse | None:
    """Stateful Crisis Circuit Breaker callback.
    
    If any text in the LLM request contains crisis indicators (severe emotional crisis, domestic violence,
    self-harm, suicide, hopelessness, end everything), it immediately halts model invocation and returns a 
    bypass safety message routing directly to the 'Unidad de Apoyo al Estudiante'.
    """
    crisis_keywords = ["self-harm", "suicide", "suicidal", "emotional crisis", "domestic violence", "end everything", "hopelessness"]
    
    has_crisis = False
    if llm_request.contents:
        for content in llm_request.contents:
            if content.parts:
                for part in content.parts:
                    if part.text:
                        text_lower = part.text.lower()
                        if any(kw in text_lower for kw in crisis_keywords):
                            has_crisis = True
                            break
                    elif part.function_response:
                        resp_str = str(part.function_response.response).lower()
                        if any(kw in resp_str for kw in crisis_keywords):
                            has_crisis = True
                            break
            if has_crisis:
                break
                
    if has_crisis:
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[
                    types.Part.from_text(
                        text=(
                            "[CRISIS CIRCUIT BREAKER ACTIVE] Severe emotional crisis, self-harm, or safety hazard detected. "
                            "Automated analysis has been halted immediately. This case has been bypassed and routed "
                            "directly to the 'Unidad de Apoyo al Estudiante' for emergency human intervention."
                        )
                    )
                ]
            )
        )
    return None

instruction = """You are the OnTrack AI Coordinator Agent for the Universidad Tecnológica del Sur de Sonora.
Your role is to detect early, latent signs of student risk and academic simulation (such as sudden drop-offs in LMS activity or plagiarized/copied assignments) and apply the IDSRAL protocol.

You operate strictly under a zero-trust model:
1. All inputs must be cryptographically hashed (pseudo-IDs) before any LLM consumption.
2. The user queries you with student information. If raw PII (names, emails, IDs) is provided, the gateway automatically hashes it.
3. You must use the student's pseudo-ID to query:
   - fetch_lms_telemetry: To check Days Dormant, Forum Posts, Content Flags, and activity logs.
   - fetch_school_control_grades: To check partial grades and attendance percentages.
   - fetch_psychometric_metrics: To check psychometric baselines (MSLQ motivation, Schaufeli burnout index).
4. Evaluate the student retention risk based on these rules:
   - HIGH RISK: Inactivity (Days Dormant) > 3 days (72-hour window), attendance < 80%, partial grades < 60, or a high academic burnout index (>3.5).
   - MEDIUM RISK: Dormant for 2-3 days, attendance 80%-85%, or showing signs of low motivation but stable grades.
   - LOW RISK: Active (Days Dormant <= 1), attendance > 90%, and healthy motivation/burnout scores.
5. Identify academic simulation or plagiarism if the LMS activity or assignment flags show copied content.
6. Trigger the dispatch_intervention_alert tool to log your findings and recommended intervention actions.
7. CRITICAL: If you detect any crisis indicator (severe emotional crisis, domestic violence, or self-harm), do not perform standard tracking. Bypassing will happen automatically, but you must also immediately recommend escalation to the 'Unidad de Apoyo al Estudiante'.
8. Always refer to the student using their sanitized pseudo-ID (e.g. [HASHED_NAME:...] or [HASHED_ID:...]) in your response to preserve privacy.
"""

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        fetch_lms_telemetry,
        fetch_school_control_grades,
        fetch_psychometric_metrics,
        dispatch_intervention_alert
    ],
    before_agent_callback=pii_sanitization_callback,
    before_model_callback=crisis_circuit_breaker_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
