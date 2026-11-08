"""
Multi-dimensional feature scoring engine for microdrama promos.
Supports both fast deterministic rule-based evaluation and pluggable LLM evaluation.
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from .models import PromoSegment, RankedPromo, ScriptElement

# Lexicon of high-entropy microdrama hook triggers
HOOK_KEYWORDS = {
    'betrayal': ['marry', 'wedding', 'bride', 'groom', 'altar', 'changed my mind', 'worthless', 'not anymore', 'reject', 'disgrace', 'plain', 'maid'],
    'status': ['duke', 'duchess', 'kneel', 'beg', 'disown', 'bastard', 'inheritance', 'scandal', 'nobleman', 'regalia', 'commander', 'signet ring', 'majesty'],
    'threat': ['arrest', 'kill', 'treason', 'poison', 'guards', 'dagger', 'sword', 'witchcraft', 'burn', 'dead', 'execution', 'guilty', 'seizure'],
    'action': ['slap', 'clenches', 'grab', 'push', 'tear', 'mud', 'scars', 'shattered', 'blood', 'rain', 'drops to knee', 'kneeling', 'fire']
}

HIGH_EMOTION_TAGS = [
    'cold', 'commanding', 'devastated', 'piercing', 'shattered', 'disbelieving', 
    'mocking', 'spiteful', 'outraged', 'accusing', 'furious', 'cruel', 'derisive',
    'scornful', 'arrogant', 'heartbroken', 'trembling', 'vicious', 'taunting'
]

CLIFFHANGER_TRIGGERS = [
    '?', 'never', 'or else', 'die', 'too late', 'regret', 'you dare', 'who are you',
    'unyielding', 'defiance', 'cliffhanger', 'cut to black', 'drone', 'swells', 'draws sword'
]

class BaseScoringEngine:
    """Abstract base class for promo scoring engines."""
    def score_candidate(self, segments: List[PromoSegment], episode_number: int) -> Optional[RankedPromo]:
        raise NotImplementedError

class HeuristicScoringEngine(BaseScoringEngine):
    """
    High-precision neuro-symbolic rule-based scoring engine.
    Evaluates Hook entropy, Cliffhanger tension, Standalone clarity, and Pacing.
    Zero external API dependency, runs in milliseconds.
    """

    def score_candidate(self, segments: List[PromoSegment], episode_number: int) -> Optional[RankedPromo]:
        if not segments:
            return None
            
        total_duration = sum(s.duration_sec for s in segments)
        all_elements: List[ScriptElement] = []
        for s in segments:
            all_elements.extend(s.elements)
            
        if not all_elements:
            return None

        # 1. Analyze Hook Window (first 3-5 seconds of first segment)
        hook_elements = [el for el in segments[0].elements if (el.timing.end_sec - segments[0].start_sec) <= 5.0]
        if not hook_elements:
            hook_elements = segments[0].elements[:2]

        hook_score, hook_desc, hook_type = self._evaluate_hook(hook_elements, segments[0])

        # 2. Analyze Cliffhanger Window (last 4 seconds of last segment)
        cliff_elements = [el for el in segments[-1].elements if (segments[-1].end_sec - el.timing.start_sec) <= 5.0]
        if not cliff_elements:
            cliff_elements = segments[-1].elements[-2:]

        cliff_score, cliff_desc, cliff_type = self._evaluate_cliffhanger(cliff_elements, segments[-1])

        # 3. Analyze Standalone Clarity & Comprehensibility
        clarity_score, clarity_notes = self._evaluate_clarity(all_elements)

        # 4. Analyze Pacing & Retention Curve
        pacing_score = self._evaluate_pacing(total_duration, all_elements)

        # Composite Score Calculation (Weighted)
        # Weights: Hook (35%), Cliffhanger (30%), Clarity (20%), Pacing (15%)
        composite = (
            0.35 * hook_score +
            0.30 * cliff_score +
            0.20 * clarity_score +
            0.15 * pacing_score
        )

        # Determine campaign funnel category
        if hook_score >= 8.2 and "Betrayal" in hook_type:
            campaign = "Top-of-Funnel (Cold Hook)"
        elif "Lethal" in cliff_type or "Identity" in cliff_type or cliff_score >= 8.5:
            campaign = "Retargeting (High Cliffhanger)"
        else:
            campaign = "Mid-Funnel (Emotional Escalation)"

        # Generate marketing rationale: "why it works"
        why_it_works = self._generate_why_it_works(hook_type, cliff_type, total_duration, all_elements)

        promo_id = f"PROMO_EP{episode_number:03d}_{int(segments[0].start_sec):03d}s"

        return RankedPromo(
            promo_id=promo_id,
            episode_number=episode_number,
            title=f"Ep {episode_number}: {hook_type} -> {cliff_type}",
            segments=segments,
            total_duration_sec=total_duration,
            hook_description=hook_desc,
            hook_type=hook_type,
            cliffhanger_description=cliff_desc,
            cliffhanger_type=cliff_type,
            why_it_works=why_it_works,
            hook_score=hook_score,
            cliffhanger_score=cliff_score,
            standalone_clarity_score=clarity_score,
            pacing_score=pacing_score,
            composite_score=composite,
            campaign_category=campaign,
            failure_risk_notes=clarity_notes
        )

    def _evaluate_hook(self, hook_elements: List[ScriptElement], segment: PromoSegment) -> Tuple[float, str, str]:
        score = 5.0  # baseline
        desc_parts = []
        detected_types = []
        
        hook_text = " ".join([el.content.lower() for el in hook_elements])
        
        # Check dialogue
        first_dlg = next((el for el in hook_elements if el.element_type == 'DIALOGUE'), None)
        first_action = next((el for el in hook_elements if el.element_type == 'ACTION'), None)
        
        if first_dlg:
            char = first_dlg.character or "Character"
            emotion = f" ({first_dlg.emotion})" if first_dlg.emotion else ""
            desc_parts.append(f'{char}{emotion}: "{first_dlg.content[:80]}"')
            
            # Check high-emotion parentheticals
            if first_dlg.emotion:
                for emo in HIGH_EMOTION_TAGS:
                    if emo in first_dlg.emotion.lower():
                        score += 1.2
                        break
        elif first_action:
            desc_parts.append(f'Action: {first_action.content[:90]}')
        else:
            desc_parts.append(f'Scene opens: {hook_elements[0].content[:80]}')

        # Check keyword categories
        for cat, kw_list in HOOK_KEYWORDS.items():
            for kw in kw_list:
                if kw in hook_text:
                    if cat == 'betrayal':
                        score += 1.5
                        detected_types.append("Altar Betrayal")
                    elif cat == 'status':
                        score += 1.4
                        detected_types.append("Status Reversal")
                    elif cat == 'threat':
                        score += 1.3
                        detected_types.append("Lethal Threat")
                    elif cat == 'action':
                        score += 1.2
                        detected_types.append("Physical Confrontation")
                    break

        # Check question or shocking interruption
        if "?" in hook_text:
            score += 0.5
        if "!" in hook_text:
            score += 0.4

        hook_type = detected_types[0] if detected_types else "High-Stakes Opening"
        hook_desc = " | ".join(desc_parts) if desc_parts else "Immediate dramatic opening beat"
        
        return min(10.0, max(2.0, score)), hook_desc, hook_type

    def _evaluate_cliffhanger(self, cliff_elements: List[ScriptElement], segment: PromoSegment) -> Tuple[float, str, str]:
        score = 5.0
        desc_parts = []
        detected_types = []
        
        cliff_text = " ".join([el.content.lower() for el in cliff_elements])
        last_dlg = next((el for el in reversed(cliff_elements) if el.element_type == 'DIALOGUE'), None)
        last_sfx = next((el for el in reversed(cliff_elements) if el.element_type == 'SOUND FX'), None)
        last_action = next((el for el in reversed(cliff_elements) if el.element_type == 'ACTION'), None)
        
        if last_dlg:
            char = last_dlg.character or "Speaker"
            desc_parts.append(f'{char}: "{last_dlg.content[:85]}"')
            if "?" in last_dlg.content:
                score += 1.8
                detected_types.append("Unanswered Question")
            if any(w in last_dlg.content.lower() for w in ['never', 'die', 'kill', 'dare', 'regret', 'leave', 'choice']):
                score += 1.5
                detected_types.append("Unresolved Ultimatum")
        elif last_action:
            desc_parts.append(f'Action: {last_action.content[:90]}')
            detected_types.append("Physical Climax")
            score += 1.2
            
        if last_sfx and any(w in last_sfx.content.lower() for w in ['drone', 'swell', 'cliffhanger', 'sting', 'cut']):
            score += 1.2
            
        # Check for cut on emotional defiance or shock
        if any(w in cliff_text for w in ['defiance', 'shock', 'tears', 'blade', 'gasps', 'seized', 'salute']):
            score += 1.0
            if "salute" in cliff_text or "duke" in cliff_text:
                detected_types.append("Identity Unmasking")
            elif "blade" in cliff_text or "seized" in cliff_text or "arrest" in cliff_text:
                detected_types.append("Lethal Stand-off")

        cliff_type = detected_types[0] if detected_types else "Suspenseful Cut"
        cliff_desc = " | ".join(desc_parts) if desc_parts else "Cuts abruptly on high-tension beat"
        
        return min(10.0, max(2.0, score)), cliff_desc, cliff_type

    def _evaluate_clarity(self, elements: List[ScriptElement]) -> Tuple[float, Optional[str]]:
        """Evaluates whether the clip is self-contained without prior show context."""
        score = 8.5
        notes = []
        
        # Check characters involved
        dialogues = [el for el in elements if el.element_type == 'DIALOGUE']
        characters = set(el.character for el in dialogues if el.character)
        
        # 2-3 characters is ideal (Protagonist vs Antagonist dynamic)
        if len(characters) == 2 or len(characters) == 3:
            score += 1.0
        elif len(characters) >= 5:
            score -= 1.8
            notes.append("Multi-character crowd scene; risk of confusing cold viewers.")
            
        # Check pronoun ambiguity (e.g. "He did what she wanted to them")
        dialogue_text = " ".join([d.content for d in dialogues]).lower()
        if dialogue_text.startswith("he ") or dialogue_text.startswith("she ") or dialogue_text.startswith("they "):
            score -= 1.0
            notes.append("Opens with third-person pronoun without visual subject introduction.")
            
        # Core archetypal polarity bonus (Juliana vs Gerald / Alexander vs Rupert)
        if any(c in ['LADY JULIANA', 'JULIANA'] for c in characters) and any(c in ['GERALD', 'THE FORMER GROOM', 'CLARISSA', 'MATRIARCH', 'RUPERT'] for c in characters):
            score += 0.8
            
        note_str = "; ".join(notes) if notes else None
        return min(10.0, max(3.0, score)), note_str

    def _evaluate_pacing(self, duration: float, elements: List[ScriptElement]) -> float:
        """Scores duration and conversational density for short-form retention."""
        # Optimal duration bell curve centered around 32-45 seconds
        if 30.0 <= duration <= 45.0:
            dur_score = 10.0
        elif 22.0 <= duration < 30.0:
            dur_score = 8.5
        elif 45.0 < duration <= 55.0:
            dur_score = 8.0
        else:
            dur_score = 6.5
            
        # Dialogue density: ratio of dialogue to total elements
        dialogues = [el for el in elements if el.element_type == 'DIALOGUE']
        if len(dialogues) >= 4:
            density_bonus = 0.5
        else:
            density_bonus = 0.0
            
        return min(10.0, dur_score + density_bonus)

    def _generate_why_it_works(self, hook_type: str, cliff_type: str, duration: float, elements: List[ScriptElement]) -> str:
        """Generates a concise 1-line marketing rationale for the promo."""
        dialogues = [el for el in elements if el.element_type == 'DIALOGUE']
        speakers = list(dict.fromkeys([el.character for el in dialogues if el.character]))
        speaker_str = " vs ".join(speakers[:2]) if len(speakers) >= 2 else (speakers[0] if speakers else "Dramatic conflict")
        
        rationales = {
            "Altar Betrayal": f"Universal moral outrage hook ({speaker_str}) immediately triggers social scrolling stop, building unbearable injustice into a sharp {cliff_type}.",
            "Status Reversal": f"Visceral power reversal creates instant empathy, driving high completion rate ({round(duration)}s) before cutting on an unresolved power shift.",
            "Lethal Threat": f"High physical stakes and impending doom arrest scrolling attention in <2s, ending precisely as the confrontation reaches fever pitch.",
            "Physical Confrontation": f"Shocking physical action breaks feed inertia, compelling viewers to watch the full emotional fallout.",
            "High-Stakes Opening": f"Immediate conflict immersion with clear stakes and zero cognitive load, terminating on an irresistible Zeigarnik cliffhanger."
        }
        return rationales.get(hook_type, f"High-contrast dramatic tension ({round(duration)}s) that establishes clear protagonist-antagonist stakes and cuts on an unresolved cliffhanger.")
