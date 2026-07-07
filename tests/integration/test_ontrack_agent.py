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

import pytest
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent
from app.tools import get_pseudo_id

@pytest.mark.asyncio
async def test_agent_retention_flow() -> None:
    """Integration test checking that the agent processes a student query,
    performs necessary database calls using hashes, and dispatches the alert.
    """
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    # Juan Perez (ID 12345) is a high-risk case
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Please analyze the retention risk for student Juan Perez (ID: 12345) and dispatch an alert if needed.")]
    )

    events = []
    async for event in runner.run_async(
        new_message=message,
        user_id="test_user",
        session_id=session.id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        events.append(event)

    assert len(events) > 0

    # Ensure PII is sanitized: real student name and raw ID must NOT be present in final events text content
    text_content = ""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    text_content += part.text + "\n"

    assert "Juan Perez" not in text_content
    assert "12345" not in text_content
    hashed_name_short = get_pseudo_id("Juan Perez")[:16]
    hashed_id_short = get_pseudo_id("12345")[:16]
    assert hashed_name_short in text_content or hashed_id_short in text_content

@pytest.mark.asyncio
async def test_agent_crisis_circuit_breaker() -> None:
    """Integration test checking that a student with crisis indicators
    triggers the Crisis Circuit Breaker callback, halting model execution.
    """
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    # Real ID 99999 is mock configured with severe emotional crisis
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Perform diagnostic on student ID 99999 and check their psychometrics.")]
    )

    events = []
    async for event in runner.run_async(
        new_message=message,
        user_id="test_user",
        session_id=session.id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    ):
        events.append(event)

    text_content = ""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    text_content += part.text + "\n"

    assert "[CRISIS CIRCUIT BREAKER ACTIVE]" in text_content
    assert "bypassed and routed directly" in text_content
