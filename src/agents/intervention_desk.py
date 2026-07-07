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

from typing import Dict

class InterventionDeskAgent:
    """
    Agente enfocado en la generación de entregables de apoyo docente y alertas
    estructuradas para los tutores basados en la clasificación del protocolo IDSRAL.
    """
    def draft_tutor_action_plan(self, pseudo_id: str, analysis: Dict[str, str]) -> str:
        risk = analysis.get("risk_level", "UNKNOWN")
        driver = analysis.get("primary_risk_driver", "No driver provided")
        
        if risk == "HIGH":
            return (
                f"🚨 ALERTA CRÍTICA RECOMENDADA - PROTOCOLO IDSRAL\n"
                f"Referencia: {pseudo_id}\n"
                f"Causa Raíz: {driver}\n"
                f"Acción Inmediata: Agendar sesión uno a uno en campus dentro de las próximas 48 horas. "
                f"Habilitar acceso prioritario a salas de cómputo para mitigar brecha digital perimetral."
            )
        return f"Estatus Regular para {pseudo_id}. Continuar monitoreo pasivo en plataforma LMS."
