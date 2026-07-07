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

import hashlib
import re
from typing import Any

# Mock Database
STUDENTS_DB = {
    "12345": {
        "name": "Juan Perez",
        "email": "jperez@unison.mx",
        "telemetry": {
            "days_dormant": 5,
            "forum_posts": 1,
            "content_flags": 3,
            "recent_activity_log": "Student logged in 5 days ago, downloaded one syllabus, has not posted or submitted since."
        },
        "school_control": {
            "grades": {"math": 45, "history": 55, "spanish": 60},
            "attendance_percentage": 70.5
        },
        "psychometrics": {
            "mslq_motivation_spectrum": "low motivation, high test anxiety",
            "burnout_index": "high academic burnout (Schaufeli index 4.2)"
        }
    },
    "67890": {
        "name": "Maria Rodriguez",
        "email": "mrodriguez@unison.mx",
        "telemetry": {
            "days_dormant": 1,
            "forum_posts": 12,
            "content_flags": 0,
            "recent_activity_log": "Highly active, submits assignments on time, participates in forums."
        },
        "school_control": {
            "grades": {"math": 95, "history": 92, "spanish": 88},
            "attendance_percentage": 98.0
        },
        "psychometrics": {
            "mslq_motivation_spectrum": "high intrinsic motivation",
            "burnout_index": "low academic burnout (Schaufeli index 1.5)"
        }
    },
    "99999": {
        "name": "Crisis Test Student",
        "email": "crisis@unison.mx",
        "telemetry": {
            "days_dormant": 15,
            "forum_posts": 0,
            "content_flags": 5,
            "recent_activity_log": "Severe emotional crisis. Forum post draft saved with self-harm ideation and expressing feelings of total hopelessness."
        },
        "school_control": {
            "grades": {"math": 20, "history": 10, "spanish": 15},
            "attendance_percentage": 30.0
        },
        "psychometrics": {
            "mslq_motivation_spectrum": "extremely low, severe anxiety",
            "burnout_index": "critical academic burnout, signs of self-harm risk"
        }
    }
}

def get_pseudo_id(raw_id: str) -> str:
    """Helper to generate a SHA256 hashed pseudo-ID."""
    return hashlib.sha256(raw_id.strip().encode('utf-8')).hexdigest()

HASH_MAP = {}
for real_id, data in STUDENTS_DB.items():
    h_id = get_pseudo_id(real_id)
    h_email = get_pseudo_id(data["email"])
    h_name = get_pseudo_id(data["name"])
    
    HASH_MAP[h_id] = real_id
    HASH_MAP[h_id[:16]] = real_id
    HASH_MAP[h_email] = real_id
    HASH_MAP[h_email[:16]] = real_id
    HASH_MAP[h_name] = real_id
    HASH_MAP[h_name[:16]] = real_id

def sanitize_text(text: str) -> str:
    """Masks emails, IDs, and names inside any unstructured text to ensure PII sanitization."""
    # Hash email addresses
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    emails = re.findall(email_pattern, text)
    for email in emails:
        text = text.replace(email, f"[HASHED_EMAIL:{get_pseudo_id(email)[:16]}]")
    
    # Hash institutional IDs (5-10 digit numbers)
    id_pattern = r'\b\d{5,10}\b'
    ids = re.findall(id_pattern, text)
    for s_id in ids:
        text = text.replace(s_id, f"[HASHED_ID:{get_pseudo_id(s_id)[:16]}]")
        
    # Mask known names
    for real_id, data in STUDENTS_DB.items():
        name = data["name"]
        text = re.sub(re.escape(name), f"[HASHED_NAME:{get_pseudo_id(name)[:16]}]", text, flags=re.IGNORECASE)
        
    return text

def fetch_lms_telemetry(student_pseudo_id: str) -> dict[str, Any]:
    """Fetches behavior telemetry data (dormant days, forum activity, content flags) from LMS (Moodle/Classroom) for a student.
    
    Args:
        student_pseudo_id: The cryptographically masked student ID (SHA256 hash or slice).
        
    Returns:
        A dictionary containing telemetry data.
    """
    real_id = HASH_MAP.get(student_pseudo_id)
    if not real_id:
        return {"status": "error", "message": "Student record not found for the provided pseudo-ID."}
    
    student_data = STUDENTS_DB[real_id]
    telemetry = student_data["telemetry"]
    
    return {
        "status": "success",
        "student_pseudo_id": student_pseudo_id,
        "days_dormant": telemetry["days_dormant"],
        "forum_posts": telemetry["forum_posts"],
        "content_flags": telemetry["content_flags"],
        "recent_activity_log": sanitize_text(telemetry["recent_activity_log"])
    }

def fetch_school_control_grades(student_pseudo_id: str) -> dict[str, Any]:
    """Queries partial grades and attendance percentages from the School Control System for a student.
    
    Args:
        student_pseudo_id: The cryptographically masked student ID (SHA256 hash or slice).
        
    Returns:
        A dictionary containing grades and attendance.
    """
    real_id = HASH_MAP.get(student_pseudo_id)
    if not real_id:
        return {"status": "error", "message": "Student record not found for the provided pseudo-ID."}
        
    student_data = STUDENTS_DB[real_id]
    school_control = student_data["school_control"]
    
    return {
        "status": "success",
        "student_pseudo_id": student_pseudo_id,
        "grades": school_control["grades"],
        "attendance_percentage": school_control["attendance_percentage"]
    }

def fetch_psychometric_metrics(student_pseudo_id: str) -> dict[str, Any]:
    """Fetches IDSRAL psychometric metrics (motivation and academic burnout inventory index) for a student.
    
    Args:
        student_pseudo_id: The cryptographically masked student ID (SHA256 hash or slice).
        
    Returns:
        A dictionary containing psychometric baselines.
    """
    real_id = HASH_MAP.get(student_pseudo_id)
    if not real_id:
        return {"status": "error", "message": "Student record not found for the provided pseudo-ID."}
        
    student_data = STUDENTS_DB[real_id]
    psychometrics = student_data["psychometrics"]
    
    return {
        "status": "success",
        "student_pseudo_id": student_pseudo_id,
        "mslq_motivation_spectrum": sanitize_text(psychometrics["mslq_motivation_spectrum"]),
        "burnout_index": sanitize_text(psychometrics["burnout_index"])
    }

def dispatch_intervention_alert(
    student_pseudo_id: str,
    risk_level: str,
    indicators: list[str],
    recommendation: str
) -> dict[str, Any]:
    """Dispatches a structured warning or action alert to the Student Support system.
    
    Args:
        student_pseudo_id: The cryptographically masked student ID.
        risk_level: The determined academic/retention risk level (e.g. HIGH, MEDIUM, LOW).
        indicators: A list of specific risk indicators detected.
        recommendation: Recommended intervention action based on the IDSRAL protocol.
        
    Returns:
        A dictionary with the alert dispatch status.
    """
    real_id = HASH_MAP.get(student_pseudo_id)
    if not real_id:
        return {"status": "error", "message": "Student record not found."}
        
    # Check for crisis circuit breaker in alert contents
    crisis_keywords = ["self-harm", "suicide", "suicidal", "emotional crisis", "domestic violence", "hopelessness", "end everything"]
    all_text = (recommendation + " " + " ".join(indicators)).lower()
    
    if any(kw in all_text for kw in crisis_keywords):
        return {
            "status": "CIRCUIT_BREAKER_TRIGGERED",
            "route_to": "Unidad de Apoyo al Estudiante",
            "message": "Automated routing bypassed. Crisis intervention alert triggered."
        }
        
    return {
        "status": "success",
        "student_pseudo_id": student_pseudo_id,
        "risk_level": risk_level,
        "dispatched": True,
        "message": "Intervention alert successfully logged for support staff review."
    }
