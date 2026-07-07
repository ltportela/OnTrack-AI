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

def sanitize_student_identity(raw_email: str) -> str:
    """
    Transforma identificadores PII reales en tokens criptográficos anonimizados.
    Evita la persistencia o exposición de datos sensibles en el runtime de la IA.
    """
    salt = "UT_SUR_SONORA_SECURE_SALT_2026"
    hashed = hashlib.sha256((raw_email + salt).encode('utf-8')).hexdigest()
    return f"student_sha256_{hashed[:16]}"
