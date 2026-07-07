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

from app.tools import (
    get_pseudo_id,
    sanitize_text,
    fetch_lms_telemetry,
    fetch_school_control_grades,
    fetch_psychometric_metrics,
    dispatch_intervention_alert,
    STUDENTS_DB
)

def test_get_pseudo_id():
    raw_id = "12345"
    pseudo = get_pseudo_id(raw_id)
    assert len(pseudo) == 64
    assert pseudo == get_pseudo_id("12345")

def test_sanitize_text():
    text = "Student Juan Perez with ID 12345 and email jperez@unison.mx"
    sanitized = sanitize_text(text)
    
    # Assert real details are masked
    assert "Juan Perez" not in sanitized
    assert "12345" not in sanitized
    assert "jperez@unison.mx" not in sanitized
    
    # Assert hashed placeholders are present
    assert "[HASHED_NAME:" in sanitized
    assert "[HASHED_ID:" in sanitized
    assert "[HASHED_EMAIL:" in sanitized

def test_fetch_lms_telemetry():
    pseudo_id = get_pseudo_id("12345")
    res = fetch_lms_telemetry(pseudo_id)
    assert res["status"] == "success"
    assert res["days_dormant"] == 5
    assert res["forum_posts"] == 1
    assert "Juan Perez" not in res["recent_activity_log"]

    # Test with short hash
    res_short = fetch_lms_telemetry(pseudo_id[:16])
    assert res_short["status"] == "success"
    assert res_short["days_dormant"] == 5

def test_fetch_school_control_grades():
    pseudo_id = get_pseudo_id("67890")
    res = fetch_school_control_grades(pseudo_id)
    assert res["status"] == "success"
    assert res["grades"]["math"] == 95
    assert res["attendance_percentage"] == 98.0

def test_fetch_psychometric_metrics():
    pseudo_id = get_pseudo_id("12345")
    res = fetch_psychometric_metrics(pseudo_id)
    assert res["status"] == "success"
    assert "low motivation" in res["mslq_motivation_spectrum"]
    assert "burnout" in res["burnout_index"]

def test_dispatch_intervention_alert():
    pseudo_id = get_pseudo_id("12345")
    res = dispatch_intervention_alert(
        student_pseudo_id=pseudo_id,
        risk_level="HIGH",
        indicators=["Dormant for 5 days", "low motivation"],
        recommendation="Assign tutoring program"
    )
    assert res["status"] == "success"
    assert res["dispatched"] is True

    # Test crisis bypass trigger
    res_crisis = dispatch_intervention_alert(
        student_pseudo_id=pseudo_id,
        risk_level="HIGH",
        indicators=["Expressing self-harm thoughts"],
        recommendation="Halting automated tracking, immediate route to psychologist"
    )
    assert res_crisis["status"] == "CIRCUIT_BREAKER_TRIGGERED"
    assert res_crisis["route_to"] == "Unidad de Apoyo al Estudiante"
