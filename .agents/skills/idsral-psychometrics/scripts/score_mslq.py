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

def calculate_mslq_spectrum(raw_answers: list) -> float:
    """
    Suma y normaliza las respuestas de la escala Likert del MSLQ (1 al 7)
    para devolver un flotante puro entre 0.0 y 1.0.
    """
    if not raw_answers:
        return 0.0
    return round(sum(raw_answers) / (len(raw_answers) * 7), 2)
