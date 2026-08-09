"""
The departmental assistant suite.

Five specialised agents, each scoped to a clinical vertical, sharing one
tool-using runtime:

* ``enquiry``      — general departmental information (front desk)
* ``scheduling``   — appointment booking, rescheduling, cancellation
* ``counselling``  — parent counselling support (Early Intervention)
* ``screening``    — hearing screening pathways (Audiology)
* ``slp_guidance`` — speech-language therapy guidance (SLP)

Design rule that holds across all of them: every clinical fact an assistant
states comes from a deterministic tool reading clinician-authored data. The LLM
chooses which tool to call and how to word the reply — never what is true.
"""

from app.agents.base import AgentContext, AgentReply, AgentSpec, ToolDef
from app.agents.registry import get_agent, list_agents
from app.agents.router import route_message

__all__ = [
    "AgentContext",
    "AgentReply",
    "AgentSpec",
    "ToolDef",
    "get_agent",
    "list_agents",
    "route_message",
]
