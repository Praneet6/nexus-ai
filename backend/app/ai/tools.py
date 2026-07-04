"""
Claude tool definitions and implementations.
All tools wrapped with @trace_action for F03 Resolution Replay.
"""
import random
import string
import logging
from typing import Any
from app.ai.replay_tracer import trace_action

logger = logging.getLogger(__name__)

# ── Claude Tool Schemas (JSON Schema format for Anthropic API) ──────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Check the current status and details of a customer's order by order ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID to check"},
                },
                "required": ["order_id"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_refund",
            "description": "Process a refund for a customer's order. Returns confirmation and refund amount.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID to refund"},
                    "amount": {"type": "number", "description": "Refund amount in INR. Use 0 to refund full amount."},
                    "reason": {"type": "string", "description": "Reason for refund"},
                },
                "required": ["order_id", "reason"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reset_password",
            "description": "Trigger a password reset email for the customer's account.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Customer's email address"},
                },
                "required": ["email"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_coupon",
            "description": "Apply a discount coupon to a customer's account or order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coupon_code": {"type": "string", "description": "The coupon code to apply"},
                    "order_id": {"type": "string", "description": "Order ID to apply coupon to (optional)"},
                },
                "required": ["coupon_code"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate this conversation to a human support agent when the issue cannot be resolved by AI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Why this needs human intervention"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"], "description": "Escalation priority"},
                },
                "required": ["reason", "priority"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email_confirmation",
            "description": "Send a confirmation email to the customer summarising actions taken.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Customer email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"},
                },
                "required": ["email", "subject", "body"],
            },
        }
    },
]


# ── Tool Implementations ──────────────────────────────────────────────────────

ORDER_STATUSES = [
    "PROCESSING", "CONFIRMED", "PACKED", "OUT_FOR_DELIVERY", "DELIVERED", "RETURNED", "CANCELLED"
]


@trace_action("check_order_status")
async def check_order_status(session_id: str, order_id: str) -> dict:
    """Simulated order status lookup."""
    status = random.choice(ORDER_STATUSES)
    estimated = "2-3 business days" if status in ("PROCESSING", "CONFIRMED", "PACKED") else "N/A"
    return {
        "order_id": order_id,
        "status": status,
        "estimated_delivery": estimated,
        "last_updated": "2025-01-15 14:30:00",
        "carrier": "BlueDart Express",
        "tracking_url": f"https://track.example.com/{order_id}",
    }


@trace_action("process_refund")
async def process_refund(session_id: str, order_id: str, reason: str, amount: float = 0) -> dict:
    """Simulated refund processing."""
    refund_amount = amount if amount > 0 else random.randint(500, 5000)
    ref_id = "REF" + "".join(random.choices(string.digits, k=8))
    return {
        "refund_id": ref_id,
        "order_id": order_id,
        "amount_inr": refund_amount,
        "status": "APPROVED",
        "eta": "3-5 business days",
        "reason": reason,
        "message": f"₹{refund_amount} refund approved. Ref: {ref_id}",
    }


@trace_action("reset_password")
async def reset_password(session_id: str, email: str) -> dict:
    """Simulated password reset trigger."""
    return {
        "email": email,
        "status": "RESET_LINK_SENT",
        "message": f"Password reset link sent to {email}. Valid for 24 hours.",
        "expires_in": "24 hours",
    }


@trace_action("apply_coupon")
async def apply_coupon(session_id: str, coupon_code: str, order_id: str = "") -> dict:
    """Simulated coupon application."""
    discount = random.choice([50, 100, 150, 200, 500])
    return {
        "coupon_code": coupon_code,
        "order_id": order_id or "NEXT_ORDER",
        "discount_inr": discount,
        "status": "APPLIED",
        "message": f"Coupon {coupon_code} applied! You save ₹{discount}.",
    }


@trace_action("escalate_to_human")
async def escalate_to_human(session_id: str, reason: str, priority: str = "medium") -> dict:
    """Escalate to human agent — triggers F06 trust debit."""
    ticket_id = "TKT" + "".join(random.choices(string.digits, k=6))
    wait_times = {"low": "4-6 hours", "medium": "1-2 hours", "high": "30 minutes", "urgent": "5-10 minutes"}
    return {
        "ticket_id": ticket_id,
        "priority": priority,
        "estimated_wait": wait_times.get(priority, "1-2 hours"),
        "reason": reason,
        "status": "ESCALATED",
        "message": f"Ticket {ticket_id} created. An agent will contact you within {wait_times.get(priority)}.",
        "_triggers_trust_debit": True,
        "_debit_reason": "escalation_to_human",
    }


@trace_action("send_email_confirmation")
async def send_email_confirmation(session_id: str, email: str, subject: str, body: str) -> dict:
    """Simulated email send."""
    msg_id = "MSG" + "".join(random.choices(string.alphanumeric if hasattr(string, 'alphanumeric') else string.ascii_uppercase + string.digits, k=10))
    return {
        "message_id": msg_id,
        "to": email,
        "subject": subject,
        "status": "SENT",
        "message": f"Confirmation email sent to {email}.",
    }


# ── Tool executor ──────────────────────────────────────────────────────────────

TOOL_MAP = {
    "check_order_status": check_order_status,
    "process_refund": process_refund,
    "reset_password": reset_password,
    "apply_coupon": apply_coupon,
    "escalate_to_human": escalate_to_human,
    "send_email_confirmation": send_email_confirmation,
}


async def execute_tool(tool_name: str, tool_input: dict, session_id: str) -> Any:
    """Execute a Claude tool call by name."""
    fn = TOOL_MAP.get(tool_name)
    if not fn:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return await fn(session_id=session_id, **tool_input)
    except Exception as e:
        logger.error(f"Tool {tool_name} execution failed: {e}")
        return {"error": str(e), "tool": tool_name}
