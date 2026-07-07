---
name: idsral-psychometrics
description: >
  Skill for managing student psychometric profiling metrics under the IDSRAL protocol,
  including MSLQ motivation spectrum and Schaufeli academic burnout index.
metadata:
  spec_reference: .agents-cli-spec.md
---
# Skill: IDSRAL Psychometric Matrix Evaluation

## Purpose
Grounds the agent in interpreting student motivation spectrums and burnout indexes according to the Universidad Tecnológica del Sur de Sonora protocol parameters.

## Core Evaluation Logic & Thresholds
1. **Low Motivation Signal:** MSLQ Motivation Score < 0.40.
2. **High Burnout Signal:** Schaufeli Burnout Index > 0.70.
3. **Severe Risk State:** If BOTH conditions are met, or if either condition is combined with an LMS Dormancy > 5 days, the output category MUST be forced to `HIGH`.

## Crisis Circuit Breaker Rule
CRITICAL: If textual student input or forum telemetry containing keys indicating emotional crisis or self-harm is passed, IMMEDIATELY halt processing and trigger `HUMAN_BYPASS` to the "Unidad de Apoyo al Estudiante". Do not attempt automated risk classification.