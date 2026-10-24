"""Anti-LLM-Bias Engine — off-prior, godhand, evidence label validation."""


class AntiBiasEngine:
    OFF_PRIOR_RATIO = 0.20

    def validate_slice_plan(self, slices: list, advisory_families: set) -> dict:
        """Validate that >=20% of slices target off-prior families."""
        total = len(slices)
        if total == 0:
            return {"valid": True, "off_prior_ratio": 0, "message": "No slices"}

        off_prior = [
            s for s in slices if s.get("family") not in advisory_families
        ]
        ratio = len(off_prior) / total

        if ratio < self.OFF_PRIOR_RATIO:
            needed = max(1, int(total * self.OFF_PRIOR_RATIO) - len(off_prior))
            return {
                "valid": False,
                "off_prior_ratio": round(ratio, 2),
                "off_prior_count": len(off_prior),
                "total": total,
                "message": (
                    f"Need {needed} more off-prior slices to reach 20% threshold"
                ),
            }
        return {
            "valid": True,
            "off_prior_ratio": round(ratio, 2),
            "off_prior_count": len(off_prior),
            "total": total,
        }

    def validate_evidence_chain(self, primitives: list) -> dict:
        """Check evidence label distribution in a chain. >50% ASSUMED → downgrade."""
        if not primitives:
            return {"valid": True, "assumed_ratio": 0}

        labels = [p.get("evidence_label", "ASSUMED") for p in primitives]
        assumed = sum(1 for l in labels if l == "ASSUMED")
        ratio = assumed / len(labels)

        return {
            "valid": ratio <= 0.5,
            "assumed_ratio": round(ratio, 2),
            "labels": {
                "READ": labels.count("READ"),
                "INFERRED": labels.count("INFERRED"),
                "ASSUMED": assumed,
            },
            "recommendation": "downgrade_severity" if ratio > 0.5 else "keep",
        }

    def validate_family_rotation(self, hunt_history: list) -> dict:
        """Check if hunting is stuck on one family."""
        if len(hunt_history) < 3:
            return {"valid": True}

        last_3 = [h.get("family") for h in hunt_history[-3:]]
        if len(set(last_3)) == 1:
            return {
                "valid": False,
                "stuck_family": last_3[0],
                "message": (
                    f"3 consecutive rounds on '{last_3[0]}'. "
                    "Rotate to another family."
                ),
            }
        return {"valid": True}

    def validate_critic_evidence(self, critic_reasoning: dict) -> dict:
        """When critic flags FP, check if reasoning is evidence-based."""
        label = critic_reasoning.get("evidence_label", "ASSUMED")
        if label == "ASSUMED":
            return {
                "action": "keep_finding",
                "reason": (
                    "Critic reasoning based on ASSUMED evidence. "
                    "Keep finding, flag for manual review."
                ),
            }
        return {
            "action": "accept_critic" if label == "READ" else "review",
            "reason": f"Critic reasoning based on {label} evidence.",
        }
