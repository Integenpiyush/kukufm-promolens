# 3-Minute Video Walkthrough Script: PromoLens (Kuku AI Generalist)

Use this script for your screen recording (Loom, unlisted YouTube, or Google Drive). 
Keep it natural, energetic, and under 3 minutes.

---

### [00:00 - 00:30] Introduction & The Business Problem
**Screen to show:** Show the terminal with `python run_pipeline.py` or the Streamlit app homepage.

**Spoken Script:**
> "Hi everyone, I'm Piyush. For this assignment, I chose **Problem 1: Find the Promos for Kuku's AI Microdramas**.
> 
> In microdramas, creative editing is the single biggest bottleneck in scaling customer acquisition. Shows live or die on TikTok, Meta Reels, and YouTube Shorts. Today, editors spend up to 18 hours per show scrubbing 50+ episodes to find 20 to 60-second clips. 
> 
> My goal was to build **PromoLens**: an automated pipeline that ingests raw screenplays, detects high-entropy hooks and cliffhangers, and outputs ready-to-run promos with exact timestamps in just one second."

---

### [00:30 - 01:15] System Architecture: Why Hybrid Beats Brute-Force LLMs
**Screen to show:** Terminal running `python run_pipeline.py` or architecture diagram in `solution_doc.md`.

**Spoken Script:**
> "Most people approach this by stuffing entire screenplays into an LLM. But across 50 episodes, that costs over $8 per show, takes 15 minutes, and worse—models hallucinate timestamps and cut actors off mid-word.
> 
> Instead, I built a **Hybrid Neuro-Symbolic Architecture**:
> 1. **Deterministic Parser & Constraint Solver**: Parses all 50 episodes in under a second and generates candidate windows strictly between 20 and 60 seconds, snapping cuts to exact sentence onsets and breath/audio finishes.
> 2. **Multi-Feature Scorer**: Scores candidates across the 3 pillars of viral vertical video: 
>    - **3-Second Hook Entropy** (slaps, public humiliation, moral betrayal)
>    - **Zeigarnik Cliffhanger Tension** (unanswered questions and ultimatums)
>    - **Standalone Clarity** (ensuring cold viewers understand the stakes without backstory)
> 3. **Temporal Non-Maximum Suppression (NMS)**: Eliminates duplicate cuts of the same scene so editors don't see 5 slightly different versions of the same 30 seconds."

---

### [01:15 - 02:00] Live Demo: Streamlit Studio & Premiere EDL Export
**Screen to show:** Switch to the interactive Streamlit UI (`streamlit run app.py`). Click on Rank #1 and Rank #2 promos. Show the visual timeline and scores.

**Spoken Script:**
> "Here is the interactive **PromoLens Studio** running on the full 50-episode pack.
> 
> Let's look at **Rank #1** from Episode 2. The clip is 23 seconds. 
> - It opens on an explosive thumb-stop hook: the cruel sister mocking Juliana's mother's gown: *'You look like a kitchen maid who wandered into the wrong wedding.'*
> - And it ends on a sharp cliffhanger: Gerald tells her to leave with some dignity, and Juliana turns with tears and fury: *'Dignity?'*—cutting right before her reply.
> 
> For editors, we don't just output text. In `raw_outputs/edl_exports`, the tool generates **CMX 3600 Edit Decision Lists**. Editors can drag and drop this straight into Adobe Premiere Pro or DaVinci Resolve, and the cuts populate automatically on their timeline."

---

### [02:00 - 02:35] Strategic Ranking: Which Promos to Post First?
**Screen to show:** Switch to Tab 3: "Marketing Campaign Strategy" in the Streamlit app.

**Spoken Script:**
> "In paid marketing, you don't post all promos at once. We ranked them into 3 distinct waves:
> - **Wave 1 (Cold User Acquisition / Top-of-Funnel - Post First)**: Promos like Episode 2 with raw moral outrage. Cold audiences on TikTok have zero affinity with lore; only visceral betrayal stops the scroll in under 2 seconds.
> - **Wave 2 (Mid-Funnel Escalation - Post Second)**: Promos like Episode 30 where Juliana is framed for murder. This drives deeper engagement and app installs.
> - **Wave 3 (Cathartic Vindication - Retargeting - Post Third)**: Episode 42, where the broken soldier reveals he is the Grand Duke. This delivers the ultimate revenge payoff, driving paid episode unlocks."

---

### [02:35 - 03:00] Honest Failures & Interview Readiness
**Screen to show:** Switch to Tab 4 ("Test Custom Script") or the diagnostic table in terminal.

**Spoken Script:**
> "Where does the tool pick badly? In our diagnostic audit of 25 promos, 17 passed cleanly, but 3 were flagged for **Pronoun Ambiguity**—for instance, opening with *'Your soldier?'* without naming who he is. Our tool automatically flags these for human review.
> 
> Best of all, PromoLens is **model-swappable**. On Tab 4, an interviewer can paste any brand-new screenplay, plug in their own API key, and test it live.
> 
> Thank you, and I look forward to discussing this in the interview!"
