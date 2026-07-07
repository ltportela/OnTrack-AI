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

import asyncio
from src.agents.telemetry_fleet import TelemetryFleetAgent
from src.agents.orchestrator import OnTrackOrchestrator, RiskAssessmentPayload
from src.agents.intervention_desk import InterventionDeskAgent

async def pipeline_execution_loop():
    print("=== [OnTrack AI] Inicializando Flujo Multiagente Serverless ===")
    
    # 1. Instanciar componentes de la flota
    telemetry_agent = TelemetryFleetAgent()
    orchestrator_agent = OnTrackOrchestrator()
    intervention_agent = InterventionDeskAgent()
    
    # 2. Simular captura perimetral mediante MCP
    print("[Fleet] Extrayendo telemetría activa desde Moodle 5.2 MCP...")
    lms_data = await telemetry_agent.gather_student_metrics(
        email="vulnerable.student@utsur.edu.mx", 
        course_id="course_101"
    )
    
    # 3. Empaquetar variables junto a los datos psicométricos estáticos del IDSRAL
    payload = RiskAssessmentPayload(
        pseudo_id=lms_data["pseudo_student_id"],
        mslq_motivation_score=0.32,  # Capturado en test inicial de ingreso
        burnout_index=0.81,          # Refleja desgaste por traslados largos
        days_dormant=lms_data["metrics"]["days_dormant"],
        simulation_risk_detected=lms_data["metrics"]["simulation_risk_detected"]
    )
    
    # 4. Invocación segura del Orquestador Central
    print("[Orchestrator] Evaluando vector de deserción con Gemini 2.5 Pro...")
    import json
    try:
        raw_analysis = orchestrator_agent.evaluate_retention_risk(payload)
        analysis_json = json.loads(raw_analysis)
        
        # 5. Ejecutar generación final de intervenciones docentes
        action_plan = intervention_agent.draft_tutor_action_plan(payload.pseudo_id, analysis_json)
        print("\n=== REPORTE DE INTERVENCIÓN GENERADO ===")
        print(action_plan)
    except Exception as e:
        print(f"Error crítico en el runtime agéntico: {e}")

if __name__ == "__main__":
    asyncio.run(pipeline_execution_loop())
