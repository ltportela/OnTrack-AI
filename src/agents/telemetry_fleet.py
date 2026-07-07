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

from typing import Dict, Any
from src.tools.mcp_client import fetch_lms_activity_telemetry, TelemetryQuery

class TelemetryFleetAgent:
    """
    Agente periférico de recolección asíncrona. Pide telemetría cruda a los canales MCP 
    y limpia los metadatos antes de enviarlos al núcleo orquestador.
    """
    async def gather_student_metrics(self, email: str, course_id: str) -> Dict[str, Any]:
        query = TelemetryQuery(student_email=email, course_id=course_id)
        # Ejecuta la invocación nativa de la herramienta MCP registrada
        telemetry_payload = await fetch_lms_activity_telemetry(ctx=None, request=query)
        return telemetry_payload
