"""Proposal template engine."""

from __future__ import annotations


PROPOSAL_TEMPLATE = """\
I'd approach this as a {core_bottleneck} problem, not just a {surface_task} task.

Here's how I'd handle it:
- {step_1}
- {step_2}
- {step_3}

Relevant background: I've built {portfolio_ref}, including {proof_point}.

One question before estimating precisely: {clarifying_question}

If useful, I can start by mapping the current flow and giving you a short implementation plan before touching the codebase.
"""


def render_proposal(
    core_bottleneck: str,
    surface_task: str,
    step_1: str,
    step_2: str,
    step_3: str,
    portfolio_ref: str,
    proof_point: str,
    clarifying_question: str,
) -> str:
    return PROPOSAL_TEMPLATE.format(
        core_bottleneck=core_bottleneck,
        surface_task=surface_task,
        step_1=step_1,
        step_2=step_2,
        step_3=step_3,
        portfolio_ref=portfolio_ref,
        proof_point=proof_point,
        clarifying_question=clarifying_question,
    )
