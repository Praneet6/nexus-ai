"""
F01 — Conversation Will
Negotiates a transparent plan with the user before acting.
"""
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContractStep:
    id: int
    description: str
    status: str = "pending"   # pending | in_progress | done | failed
    result: Optional[str] = None


@dataclass
class Contract:
    session_id: str
    proposed_plan: str
    steps: list[ContractStep] = field(default_factory=list)
    status: str = "proposed"  # proposed | accepted | amended | in_progress | completed | failed
    user_amendment: Optional[str] = None
    outcome_report: Optional[str] = None


def build_contract_system_prompt() -> str:
    return """
[CONVERSATION WILL — ACTIVE]
You are Nexus AI, a next-generation customer care assistant. Before attempting to resolve any issue, you MUST:

1. Acknowledge the user's problem in one warm, empathetic sentence.
2. Propose a transparent 3-step resolution plan using EXACTLY this format:
   "Here's my plan:
   Step 1: [specific action you will take].
   Step 2: [specific action you will take].
   Step 3: [specific action you will take].
   Does this work for you, or would you like to adjust anything?"
3. Wait for the user to approve ("yes", "ok", "sure", "go ahead", "looks good") or amend the plan before proceeding.
4. After completing each step, report: "✓ Step [N] done: [brief result]. Moving to Step [N+1]."
5. End the conversation with: "Contract complete. Here is a summary of everything I did: [clear summary]."

IMPORTANT: If you cannot resolve something, say so BEFORE the user asks. Honesty builds trust.
"""


def parse_contract_from_response(response_text: str, session_id: str) -> Optional[Contract]:
    """Extract a Contract object from Claude's first response."""
    steps_raw = re.findall(
        r"Step\s+(\d+)[:\.]?\s*(.+?)(?=Step\s+\d+[:\.]|Does this|Would you|$)",
        response_text,
        re.IGNORECASE | re.DOTALL,
    )

    if len(steps_raw) < 2:
        return None

    steps = []
    for step_num, description in steps_raw[:3]:
        steps.append(ContractStep(
            id=int(step_num),
            description=description.strip()[:200],
        ))

    return Contract(
        session_id=session_id,
        proposed_plan=response_text[:500],
        steps=steps,
        status="proposed",
    )


def build_contract_progress_prompt(contract: Contract) -> str:
    """Inject contract state into every subsequent message."""
    if contract.status == "proposed":
        return f"\n[CONTRACT STATUS — AWAITING USER APPROVAL]\nProposed {len(contract.steps)}-step plan pending user response."

    completed = [s for s in contract.steps if s.status == "done"]
    current = next((s for s in contract.steps if s.status == "in_progress"), None)
    pending = [s for s in contract.steps if s.status == "pending"]

    lines = [f"\n[CONTRACT STATUS — {contract.status.upper()}]"]
    lines.append(f"Progress: {len(completed)}/{len(contract.steps)} steps completed")

    if current:
        lines.append(f"Currently executing: Step {current.id} — {current.description}")
    if pending:
        lines.append(f"Next: Step {pending[0].id} — {pending[0].description}")

    return "\n".join(lines)


def update_contract_step(contract: Contract, step_id: int, result: str, success: bool = True) -> Contract:
    """Mark a step as done or failed."""
    for step in contract.steps:
        if step.id == step_id:
            step.status = "done" if success else "failed"
            step.result = result
            break

    all_done = all(s.status in ("done", "failed") for s in contract.steps)
    if all_done:
        any_failed = any(s.status == "failed" for s in contract.steps)
        contract.status = "failed" if any_failed else "completed"

    return contract


def contract_to_dict(contract: Contract) -> dict:
    return {
        "session_id": contract.session_id,
        "proposed_plan": contract.proposed_plan,
        "status": contract.status,
        "user_amendment": contract.user_amendment,
        "outcome_report": contract.outcome_report,
        "steps": [
            {
                "id": s.id,
                "description": s.description,
                "status": s.status,
                "result": s.result,
            }
            for s in contract.steps
        ],
    }


def contract_from_dict(data: dict) -> Contract:
    return Contract(
        session_id=data["session_id"],
        proposed_plan=data.get("proposed_plan", ""),
        status=data.get("status", "proposed"),
        user_amendment=data.get("user_amendment"),
        outcome_report=data.get("outcome_report"),
        steps=[
            ContractStep(
                id=s["id"],
                description=s["description"],
                status=s.get("status", "pending"),
                result=s.get("result"),
            )
            for s in data.get("steps", [])
        ],
    )
