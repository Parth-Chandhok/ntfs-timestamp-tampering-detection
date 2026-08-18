"""
prompts.py - prompt templates for the LLM triage comparison.

THREE ARMS (supervisor's specification)
  1. rules   - static rule engine alone. No LLM. Already built.
  2. llm     - LLM sees raw artefact evidence only. Never sees the rule output.
  3. hybrid  - LLM sees the evidence AND the rule verdict, and is asked to
               CRITIQUE that verdict rather than accept it. Passing the verdict
               through unchallenged would produce near-total agreement and no
               analysable divergence.

DESIGN NOTES
  - The prompt never names a detection rule or describes what tampering looks
    like. The static rules were written by someone who already knew the answer;
    the LLM must reason from evidence alone or the comparison is meaningless.
  - Every claim must cite the artefact it came from. Uncited claims are counted
    as hallucinations at evaluation time.
  - "contradicting_evidence" is mandatory and may not be left empty without a
    stated reason: a triage assessment that only argues one side is not triage.
  - INSUFFICIENT_EVIDENCE was dropped from the supervisor's original class set.
    Bundles always contain full three-artefact evidence, so the class could
    never be correct and would only offer the model somewhere to hide.
"""

SYSTEM_INSTRUCTION = """You are a digital forensics triage assistant examining \
NTFS filesystem evidence from a Windows volume.

Your task is to assess whether a file's timestamps appear to have been \
deliberately manipulated, and to justify that assessment from the evidence \
supplied.

Rules you must follow:

1. Reason only from the evidence in the bundle. Do not assume facts that are \
not stated. If something is not in the evidence, say so rather than inferring \
it.

2. Cite the artefact for every factual claim you make. The artefacts are: \
"MFT" (the file's own timestamp attributes), "USN" (the filesystem change \
journal), and "EventLog" (Windows system events). A claim without a citation \
is not admissible.

3. Distinguish evidence from inference. State what the evidence shows, then \
state separately what you infer from it.

4. Report contradicting evidence as well as supporting evidence. If you find \
none that contradicts your conclusion, say so explicitly and explain why.

5. Do not speculate about who performed any action or why. Assess the \
artefacts, not motive.

Classification options:
  BENIGN              - no indication of timestamp manipulation
  SUSPICIOUS          - anomalies present but not conclusive
  LIKELY_TIMESTOMPING - evidence indicates deliberate manipulation

Respond with JSON only. No preamble, no markdown fences, no commentary."""


RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "classification": {
            "type": "string",
            "enum": ["BENIGN", "SUSPICIOUS", "LIKELY_TIMESTOMPING"],
        },
        "confidence": {
            "type": "number",
            "description": "0.0 to 1.0",
        },
        "supporting_evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "artefact": {"type": "string",
                                 "enum": ["MFT", "USN", "EventLog"]},
                    "observation": {"type": "string",
                                    "description": "What the evidence states"},
                    "inference": {"type": "string",
                                  "description": "What you conclude from it"},
                },
                "required": ["artefact", "observation", "inference"],
            },
        },
        "contradicting_evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "artefact": {"type": "string",
                                 "enum": ["MFT", "USN", "EventLog"]},
                    "observation": {"type": "string"},
                },
                "required": ["artefact", "observation"],
            },
        },
        "reasoning": {"type": "string"},
        "recommended_action": {"type": "string"},
    },
    "required": ["classification", "confidence", "supporting_evidence",
                 "contradicting_evidence", "reasoning", "recommended_action"],
}


LLM_ARM_TEMPLATE = """Assess the following file.

{evidence}

Return your triage assessment as JSON."""


HYBRID_ARM_TEMPLATE = """Assess the following file.

{evidence}

An automated static rule engine has already examined this file and reached the \
verdict below. Your task is NOT to agree with it. Assess independently from the \
evidence above, then state whether the rule engine's conclusion is supported by \
that evidence, overstated, understated, or resting on reasoning you cannot \
verify.

--- STATIC RULE ENGINE OUTPUT ---
Verdict: {rule_band} (confidence score {rule_score}/100)
Reasons given:
{rule_reasons}
--- END RULE ENGINE OUTPUT ---

Include your assessment of the rule engine's verdict in your "reasoning" field. \
If you disagree with it, say so and explain why.

Return your triage assessment as JSON."""


# Ablation: Experiment C files with the Event Log evidence withheld.
# The static rules only detect clock rollback because a purpose-built rule was
# written for it. This tests whether the model recognises that the remaining
# evidence is insufficient - epistemic restraint - or fabricates a
# justification, which would be a clean hallucination measurement.
ABLATION_TEMPLATE = """Assess the following file.

{evidence}

Return your triage assessment as JSON."""
