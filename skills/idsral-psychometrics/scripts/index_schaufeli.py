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

def compute_schaufeli_burnout(exhaustion_scores: list) -> float:
    """
    Calcula el índice de desgaste académico base según el inventario Schaufeli.
    """
    if not exhaustion_scores:
        return 0.0
    return round(sum(exhaustion_scores) / (len(exhaustion_scores) * 6), 2)
