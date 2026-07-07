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

import sys
import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from src.tools.privacy_gate import sanitize_student_identity

# Standard FastMCP library configuration
from mcp.server.fastmcp import FastMCP
app = FastMCP(name="ontrack-lms-telemetry")

class TelemetryQuery(BaseModel):
    student_email: str = Field(..., description="Correo institucional del alumno.")
    course_id: str = Field(..., description="ID del curso en la plataforma LMS.")

# Tool function compatibility layer for direct python import and invocation
async def fetch_lms_activity_telemetry(ctx: Optional[Any], request: TelemetryQuery) -> Dict[str, Any]:
    """
    Consulta en tiempo real métricas de interacción e identifica signos implícitos
    de simulación académica (plagios, inactividad persistente en foros).
    """
    pseudo_id = sanitize_student_identity(request.student_email)
    
    # Mock de persistencia simulando consulta real a APIs de Moodle 5.2/Classroom
    mock_lms_records = {
        "course_101": {
            "clicks_last_7_days": 1,
            "submission_lag_days": 6.5,
            "copied_content_flags": 3
        }
    }
    
    data = mock_lms_records.get(request.course_id, {"clicks_last_7_days": 20, "submission_lag_days": 0.2, "copied_content_flags": 0})
    
    return {
        "pseudo_student_id": pseudo_id,
        "course_id": request.course_id,
        "metrics": {
            "days_dormant": 7 if data["clicks_last_7_days"] < 3 else 0,
            "submission_lag_rating": "CRITICAL" if data["submission_lag_days"] > 3.0 else "NORMAL",
            "simulation_risk_detected": data["copied_content_flags"] > 1
        }
    }

# Registering the tool with FastMCP for MCP clients (stdio/sse discovery)
@app.tool(name="fetch_lms_activity_telemetry")
async def fetch_lms_activity_telemetry_mcp(request: TelemetryQuery) -> Dict[str, Any]:
    return await fetch_lms_activity_telemetry(None, request)

if __name__ == "__main__":
    # Runs the stdio server automatically
    app.run()
