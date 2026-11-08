"""
Quality checking and honest failure diagnostic engine for PromoLens.
Identifies edge cases, false cliffhangers, pronoun ambiguity, and visual-action mismatches.
"""
from typing import List, Dict, Any
from .models import RankedPromo, ScriptElement

class QualityChecker:
    """Diagnoses where the automated promo extractor succeeds and where it fails."""

    def diagnose_promo(self, promo: RankedPromo) -> Dict[str, Any]:
        flags = []
        severity = "PASS"
        
        all_elements: List[ScriptElement] = []
        for seg in promo.segments:
            all_elements.extend(seg.elements)
            
        dialogues = [el for el in all_elements if el.element_type == 'DIALOGUE']
        actions = [el for el in all_elements if el.element_type == 'ACTION']
        cameras = [el for el in all_elements if el.element_type == 'CAMERA']
        
        # Check 1: Pronoun Ambiguity / Cold-Viewer Context Failure
        if dialogues:
            first_words = dialogues[0].content.strip().lower().split()
            if first_words and first_words[0] in ['he', 'she', 'they', 'him', 'her', 'them', 'that', 'this']:
                flags.append({
                    "issue": "Pronoun Ambiguity",
                    "detail": f'Opens with "{first_words[0]}", risking lack of clarity for a cold scrolling viewer.',
                    "level": "MEDIUM"
                })
                severity = "FLAGGED"

        # Check 2: Low Dialogue Density / Action Reliance
        if len(dialogues) <= 1 and len(actions) >= 2:
            flags.append({
                "issue": "High Visual Action / Low Dialogue",
                "detail": "Promo relies heavily on visual physical acting without verbal exposition. May require sound effects or visual polish in final cut.",
                "level": "LOW"
            })

        # Check 3: Multi-Party Auditory Overcrowding
        speakers = set(d.character for d in dialogues if d.character)
        if len(speakers) >= 4:
            flags.append({
                "issue": "Character Overcrowding",
                "detail": f"Contains {len(speakers)} distinct speakers. Might feel cluttered in a 30s TikTok feed.",
                "level": "MEDIUM"
            })
            severity = "FLAGGED"

        # Check 4: False Cliffhanger (Cut on non-interrogative, neutral statement)
        if dialogues:
            last_dlg = dialogues[-1].content.strip()
            if not last_dlg.endswith("?") and not last_dlg.endswith("!") and not last_dlg.endswith("..."):
                if promo.cliffhanger_score < 7.5:
                    flags.append({
                        "issue": "Weak Cliffhanger Cut",
                        "detail": f'Last line "{last_dlg[-30:]}" ends on a flat period without obvious unresolved tension.',
                        "level": "HIGH"
                    })
                    severity = "WARNING"

        return {
            "promo_id": promo.promo_id,
            "rank": promo.global_rank,
            "episode": promo.episode_number,
            "severity": severity,
            "flags": flags,
            "element_counts": {
                "dialogue": len(dialogues),
                "action": len(actions),
                "camera": len(cameras)
            }
        }

    def run_suite(self, promos: List[RankedPromo]) -> Dict[str, Any]:
        """Runs diagnostics on all ranked promos and produces aggregate quality metrics."""
        diagnostics = [self.diagnose_promo(p) for p in promos]
        clean_count = sum(1 for d in diagnostics if d["severity"] == "PASS")
        flagged_count = sum(1 for d in diagnostics if d["severity"] == "FLAGGED")
        warning_count = sum(1 for d in diagnostics if d["severity"] == "WARNING")
        
        # Categorize common failure modes
        failure_summary = {
            "Pronoun Ambiguity": sum(1 for d in diagnostics if any(f["issue"] == "Pronoun Ambiguity" for f in d["flags"])),
            "High Visual Action / Low Dialogue": sum(1 for d in diagnostics if any(f["issue"] == "High Visual Action / Low Dialogue" for f in d["flags"])),
            "Character Overcrowding": sum(1 for d in diagnostics if any(f["issue"] == "Character Overcrowding" for f in d["flags"])),
            "Weak Cliffhanger Cut": sum(1 for d in diagnostics if any(f["issue"] == "Weak Cliffhanger Cut" for f in d["flags"])),
        }
        
        return {
            "total_evaluated": len(promos),
            "clean_promos": clean_count,
            "flagged_for_editorial_review": flagged_count,
            "warning_revisions_needed": warning_count,
            "failure_mode_breakdown": failure_summary,
            "detailed_diagnostics": diagnostics
        }
