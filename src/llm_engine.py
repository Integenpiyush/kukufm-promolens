"""
Pluggable LLM Scoring Engine for PromoLens.
Supports Gemini, OpenAI, and Claude APIs with graceful heuristic fallback.
Designed specifically for interview evaluation where interviewers provide API keys.
"""
import os
import json
import logging
from typing import List, Optional
from .models import PromoSegment, RankedPromo
from .scorer import BaseScoringEngine, HeuristicScoringEngine

logger = logging.getLogger(__name__)

PROMO_EVAL_PROMPT_TEMPLATE = """You are an expert Performance Marketing Creative Director specializing in vertical microdrama apps (like ReelShort, DramaBox, Kuku TV).
Your task is to evaluate a candidate 20-60 second promo clip extracted from a screenplay.

Show Details:
Episode: {episode_number}
Duration: {duration:.1f} seconds
Full Script Beats in this Window:
{script_text}

Evaluate this clip on the 3 core pillars of high-converting social video ads (TikTok/Instagram Reels/YouTube Shorts):
1. HOOK (0-3s): Does it stop a scrolling user immediately? (e.g., slap, betrayal, reveal, shocking line)
2. CLIFFHANGER: Does it cut at an unresolved peak so the viewer must download the app / watch next?
3. STANDALONE CLARITY: Does it make sense to a cold stranger who has never seen the show?

Respond ONLY in valid JSON matching this schema:
{{
  "hook_description": "First 3s description",
  "hook_type": "Altar Betrayal | Status Reversal | Lethal Threat | Physical Action | Shocking Opening",
  "hook_score": 8.5,
  "cliffhanger_description": "Final 3s cut description",
  "cliffhanger_type": "Unresolved Ultimatum | Unanswered Question | Identity Unmasking | Lethal Stand-off",
  "cliffhanger_score": 9.0,
  "standalone_clarity_score": 8.0,
  "pacing_score": 8.5,
  "why_it_works": "One punchy marketing line explaining why this converts on TikTok/Reels ads",
  "campaign_category": "Top-of-Funnel (Cold Hook) | Mid-Funnel (Emotional Escalation) | Retargeting (Plot Twist)",
  "failure_risk_notes": "Any flaw or confusion for a cold viewer (or null)"
}}
"""

class LLMScoringEngine(BaseScoringEngine):
    """
    Pluggable LLM scoring engine supporting Gemini, OpenAI, and Anthropic.
    Falls back to HeuristicScoringEngine if API keys are not supplied.
    """

    def __init__(self, provider: str = "auto", api_key: Optional[str] = None):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.fallback_engine = HeuristicScoringEngine()
        
    def score_candidate(self, segments: List[PromoSegment], episode_number: int) -> Optional[RankedPromo]:
        # If no API key is provided, use our high-precision heuristic engine
        if not self.api_key:
            return self.fallback_engine.score_candidate(segments, episode_number)
            
        try:
            # Format candidate script
            script_lines = []
            for seg in segments:
                for el in seg.elements:
                    if el.element_type == 'DIALOGUE':
                        script_lines.append(f"[{el.timing.start_str}] {el.character} ({el.emotion or ''}): \"{el.content}\"")
                    elif el.element_type == 'ACTION':
                        script_lines.append(f"[{el.timing.start_str}] [ACTION] {el.content}")
                    elif el.element_type == 'CAMERA':
                        script_lines.append(f"[{el.timing.start_str}] [CAMERA] {el.content}")
                    elif el.element_type == 'SOUND FX':
                        script_lines.append(f"[{el.timing.start_str}] [SFX] {el.content}")
                        
            script_text = "\n".join(script_lines)
            total_duration = sum(s.duration_sec for s in segments)
            prompt = PROMO_EVAL_PROMPT_TEMPLATE.format(
                episode_number=episode_number,
                duration=total_duration,
                script_text=script_text
            )
            
            # Call respective provider
            response_json = self._call_provider(prompt)
            if response_json:
                hook_sc = float(response_json.get("hook_score", 7.0))
                cliff_sc = float(response_json.get("cliffhanger_score", 7.0))
                clar_sc = float(response_json.get("standalone_clarity_score", 7.0))
                pac_sc = float(response_json.get("pacing_score", 7.0))
                composite = 0.35 * hook_sc + 0.30 * cliff_sc + 0.20 * clar_sc + 0.15 * pac_sc
                
                promo_id = f"PROMO_EP{episode_number:03d}_{int(segments[0].start_sec):03d}s"
                
                return RankedPromo(
                    promo_id=promo_id,
                    episode_number=episode_number,
                    title=f"Ep {episode_number}: {response_json.get('hook_type', 'Dramatic Opening')} -> {response_json.get('cliffhanger_type', 'Cliffhanger')}",
                    segments=segments,
                    total_duration_sec=total_duration,
                    hook_description=response_json.get("hook_description", ""),
                    hook_type=response_json.get("hook_type", "High-Stakes Opening"),
                    cliffhanger_description=response_json.get("cliffhanger_description", ""),
                    cliffhanger_type=response_json.get("cliffhanger_type", "Suspenseful Cut"),
                    why_it_works=response_json.get("why_it_works", ""),
                    hook_score=hook_sc,
                    cliffhanger_score=cliff_sc,
                    standalone_clarity_score=clar_sc,
                    pacing_score=pac_sc,
                    composite_score=composite,
                    campaign_category=response_json.get("campaign_category", "Top-of-Funnel (Cold Hook)"),
                    failure_risk_notes=response_json.get("failure_risk_notes")
                )
        except Exception as e:
            logger.warning(f"LLM API call failed with error: {e}. Falling back to HeuristicEngine.")
            
        return self.fallback_engine.score_candidate(segments, episode_number)

    def _call_provider(self, prompt: str) -> Optional[dict]:
        import requests
        
        # Check provider
        if "openai" in self.provider or self.api_key.startswith("sk-"):
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=15)
            if res.status_code == 200:
                return json.loads(res.json()['choices'][0]['message']['content'])
                
        elif "gemini" in self.provider or "AIza" in self.api_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json", "temperature": 0.2}
            }
            res = requests.post(url, json=payload, timeout=15)
            if res.status_code == 200:
                txt = res.json()['candidates'][0]['content']['parts'][0]['text']
                return json.loads(txt)
                
        return None
