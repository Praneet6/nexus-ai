"""
Groq API client (OpenAI SDK) — streaming, tool use, full system prompt assembly.
Integrates all 6 feature injections into every call.
"""
import json
import logging
from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI

from app.config import get_settings
from app.ai.contract_manager import (
    build_contract_system_prompt,
    build_contract_progress_prompt,
    parse_contract_from_response,
    Contract,
)
from app.ai.silence_detector import get_silence_response_hint
from app.ai.style_mirror import StyleProfile, build_style_prompt_suffix
from app.ai.collective_memory import CollectiveMatch, build_collective_context_prompt
from app.ai.tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)

BASE_SYSTEM_PROMPT = """You are Nexus AI, a next-generation customer care assistant built to resolve issues transparently, empathetically, and completely.

Your core capabilities:
- You can check order status, process refunds, reset passwords, apply coupons, and escalate to humans
- You are honest: if you cannot resolve something, say so clearly BEFORE the user asks
- You track your own performance and take responsibility for failures
- You adapt your tone and language to match each individual user

Company context:
- Company: NexusMart — India's leading e-commerce platform
- Currency: Indian Rupees (₹)
- Working hours: 24/7 AI support, human agents available 9 AM – 9 PM IST

Always be warm, clear, and action-oriented."""


def build_system_prompt(
    contract: Optional[Contract] = None,
    silence_state: Optional[str] = None,
    style_profile: Optional[StyleProfile] = None,
    collective_matches: Optional[list[CollectiveMatch]] = None,
) -> str:
    parts = [BASE_SYSTEM_PROMPT]

    # F01 — Contract system instructions
    parts.append(build_contract_system_prompt())

    # F02 — Silence hint
    if silence_state and silence_state != "confident":
        hint = get_silence_response_hint(silence_state)
        if hint:
            parts.append(hint)

    # F04 — Style suffix
    if style_profile:
        parts.append(build_style_prompt_suffix(style_profile))

    # F05 — Collective context
    if collective_matches:
        ctx = build_collective_context_prompt(collective_matches)
        if ctx:
            parts.append(ctx)

    # F01 — Contract progress (mid-conversation)
    if contract and contract.status not in ("proposed", "none"):
        parts.append(build_contract_progress_prompt(contract))

    return "\n\n".join(parts)


async def stream_claude_response(
    messages: list[dict],
    session_id: str,
    contract: Optional[Contract] = None,
    silence_state: Optional[str] = None,
    style_profile: Optional[StyleProfile] = None,
    collective_matches: Optional[list[CollectiveMatch]] = None,
) -> AsyncGenerator[dict, None]:
    """
    Stream a Groq response via OpenAI SDK. Yields event dicts:
      {"type": "token",    "content": str}
      {"type": "tool_use", "tool": str, "result": dict, "triggers_trust": bool}
      {"type": "done",     "full_text": str}
      {"type": "error",    "message": str}
    """
    settings = get_settings()
    
    # Initialize OpenAI client pointing to Groq
    client = AsyncOpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1"
    )

    system_prompt = build_system_prompt(
        contract=contract,
        silence_state=silence_state,
        style_profile=style_profile,
        collective_matches=collective_matches,
    )

    # Groq expects system prompt as a message
    groq_messages = [{"role": "system", "content": system_prompt}] + messages

    full_text = ""
    tool_uses = []

    try:
        stream = await client.chat.completions.create(
            model=settings.model_name,
            messages=groq_messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            stream=True
        )

        current_tool_calls = {}

        async for chunk in stream:
            if chunk.choices:
                delta = chunk.choices[0].delta
                
                # Handle text
                if delta.content:
                    full_text += delta.content
                    yield {"type": "token", "content": delta.content}
                
                # Handle tool calls in stream
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        idx = tool_call.index
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {
                                "id": tool_call.id,
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments or ""
                            }
                        else:
                            if tool_call.function.arguments:
                                current_tool_calls[idx]["arguments"] += tool_call.function.arguments

        # Execute tools after streaming finishes
        for idx, tc in current_tool_calls.items():
            try:
                tool_input = json.loads(tc["arguments"]) if tc["arguments"] else {}
            except json.JSONDecodeError:
                tool_input = {}

            result = await execute_tool(tc["name"], tool_input, session_id)
            triggers_trust = result.get("_triggers_trust_debit", False)
            debit_reason = result.get("_debit_reason", "")

            tool_uses.append({
                "tool": tc["name"],
                "input": tool_input,
                "result": result,
            })

            yield {
                "type": "tool_use",
                "tool_id": tc["id"],
                "tool": tc["name"],
                "tool_input": tool_input,
                "result": result,
                "triggers_trust_debit": triggers_trust,
                "debit_reason": debit_reason,
            }

        yield {"type": "done", "full_text": full_text, "tool_uses": tool_uses}

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        yield {"type": "error", "message": f"API error: {str(e)}"}


async def get_claude_response(
    messages: list[dict],
    session_id: str,
    **kwargs,
) -> tuple[str, list[dict]]:
    """Non-streaming wrapper."""
    full_text = ""
    tool_uses = []
    async for event in stream_claude_response(messages, session_id, **kwargs):
        if event["type"] == "token":
            full_text += event["content"]
        elif event["type"] == "tool_use":
            tool_uses.append(event)
        elif event["type"] == "error":
            raise RuntimeError(event["message"])
    return full_text, tool_uses
