"""
Generates a beautifully styled PDF for the 3-minute video walkthrough script.
Uses ReportLab with custom color palettes, visual direction callouts, and clean typography.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class ScriptNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#666666"))
        
        # Header
        self.drawString(36, 762, "KUKU — AI GENERALIST ASSIGNMENT: VIDEO RECORDING SCRIPT")
        self.drawRightString(576, 762, "3-MINUTE SCREEN RECORDING GUIDE")
        self.setStrokeColor(colors.HexColor("#E0E0E0"))
        self.setLineWidth(0.5)
        self.line(36, 756, 576, 756)
        
        # Footer
        self.line(36, 32, 576, 32)
        self.setFont("Helvetica", 8)
        self.drawString(36, 22, "Piyush Shakya | PromoLens Walkthrough Script")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 22, page_text)
        self.restoreState()

def build_script_pdf(output_pdf_path: str):
    os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=42,
        bottomMargin=38
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ScriptTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#E50914")
    )
    
    sub_style = ParagraphStyle(
        'ScriptSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4A5568")
    )
    
    time_badge_style = ParagraphStyle(
        'TimeBadge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#FFFFFF")
    )
    
    screen_dir_style = ParagraphStyle(
        'ScreenDir',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#2B6CB0")
    )
    
    speech_style = ParagraphStyle(
        'SpeechText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor("#1A202C")
    )

    story = []
    
    # Header Banner
    story.append(Paragraph("🎬 PromoLens: 3-Minute Video Walkthrough Script", title_style))
    story.append(Paragraph("<b>Target Track:</b> Problem 1 — Find the Promos (Ads) &nbsp;|&nbsp; <b>Live App:</b> https://integenpiyush-kukufm-promolens-app-m1j9gq.streamlit.app/", sub_style))
    story.append(Spacer(1, 6))
    
    # Practical Recording Tips Box
    tips_data = [[
        Paragraph(
            "<b>🎥 Pro-Tips for Recording (Loom / Unlisted YouTube / Google Drive):</b><br/>"
            "• Keep total runtime strictly between <b>2:15 and 2:45 minutes</b> (the brief asks for up to 3 minutes).<br/>"
            "• Have your browser open with the <b>Live Deployed Streamlit App</b> on the left and this script on the right.<br/>"
            "• Speak with confidence, natural cadence, and energy — emphasize <b>scale economics ($0 cost, 1 second runtime)</b>.",
            ParagraphStyle('Tips', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10.5, textColor=colors.HexColor("#2D3748"))
        )
    ]]
    t_tips = Table(tips_data, colWidths=[540])
    t_tips.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_tips)
    story.append(Spacer(1, 8))

    sections = [
        {
            "time": "SECTION 1 &nbsp;|&nbsp; [00:00 - 00:30] &nbsp;|&nbsp; Introduction & The Core Business Problem",
            "screen": "<b>🖥️ What to show:</b> Streamlit App Homepage (Hero Banner) or Terminal running <code>python run_pipeline.py</code>.",
            "speech": (
                "\"Hi everyone, I'm Piyush. For this assignment, I chose <b>Problem 1: Find the Promos for Kuku's AI Microdramas</b>.<br/><br/>"
                "In vertical microdramas, creative video editing is today's primary bottleneck in scaling customer acquisition. Shows monetize and grow "
                "on TikTok, Meta Reels, and YouTube Shorts. Right now, editors spend up to 18 hours per series scrubbing 50+ episodes to find 20 to 60-second promos.<br/><br/>"
                "My goal was to build <b>PromoLens</b>: an automated pipeline that reads screenplay scripts, detects high-entropy hooks and cliffhangers, "
                "and outputs production-ready promos with exact timestamps in just one second.\""
            )
        },
        {
            "time": "SECTION 2 &nbsp;|&nbsp; [00:30 - 01:15] &nbsp;|&nbsp; System Architecture: Why Hybrid Beats Brute-Force LLMs",
            "screen": "<b>🖥️ What to show:</b> Terminal showing 1.07s run execution, or Architecture diagram in <code>README.md</code>.",
            "speech": (
                "\"Most people approach this by stuffing entire screenplays into an LLM. But across 50 episodes, that costs over $8 per show, takes 15 minutes, "
                "and worse—models hallucinate timestamps and cut actors off mid-sentence.<br/><br/>"
                "Instead, I engineered a <b>Hybrid Neuro-Symbolic Pipeline</b>:<br/>"
                "1. <b>Deterministic Parser & Constraint Solver:</b> Parses all 50 episodes in &lt;1.1 seconds and generates candidate cuts strictly between "
                "20 and 60 seconds, snapping to exact sentence onsets and punctuation/audio finishes.<br/>"
                "2. <b>Multi-Feature Scorer:</b> Evaluates candidates across the 3 pillars of viral short-form ads: <b>3-second hook entropy</b>, "
                "<b>Zeigarnik cliffhanger tension</b>, and <b>standalone zero-lore clarity</b>.<br/>"
                "3. <b>Temporal Non-Maximum Suppression (NMS):</b> Automatically discards duplicate cuts of the same scene so editors never see repetitive clips.\""
            )
        },
        {
            "time": "SECTION 3 &nbsp;|&nbsp; [01:15 - 02:00] &nbsp;|&nbsp; Live Demo: Streamlit Studio & Premiere EDL Export",
            "screen": "<b>🖥️ What to show:</b> Live Streamlit App (Tab 1 & Tab 2). Show Rank #1 promo and scrub the 9:16 mobile phone simulator.",
            "speech": (
                "\"Here is the live <b>PromoLens Studio</b> running on the full 50-episode pack.<br/><br/>"
                "Let's inspect <b>Rank #1</b> from Episode 2. The clip is 23 seconds.<br/>"
                "• It opens on an explosive thumb-stop hook: the cruel sister mocking Juliana's gown: <i>'You look like a kitchen maid who wandered into the wrong wedding.'</i><br/>"
                "• And it cuts on a sharp cliffhanger: Gerald tells her to leave with dignity, and Juliana turns with tears and burning defiance: <i>'Dignity?'</i>—cutting right before her reply!<br/><br/>"
                "Notice the <b>9:16 mobile ad simulator</b> on Tab 2: as you scrub, captions transition from hook to cliffhanger with Kuku TV call-to-actions. "
                "And for editors, we generate standard <b>CMX 3600 Edit Decision Lists (EDLs)</b> that import straight into Adobe Premiere Pro with cuts pre-placed!\""
            )
        },
        {
            "time": "SECTION 4 &nbsp;|&nbsp; [02:00 - 02:35] &nbsp;|&nbsp; Strategic Ranking: Which Promos to Post First & Why?",
            "screen": "<b>🖥️ What to show:</b> Tab 4 (Marketing Funnel Strategy) showing Wave 1, Wave 2, and Wave 3 cards.",
            "speech": (
                "\"In paid user acquisition, you never post all promos at once. We ranked our promos into 3 distinct marketing waves:<br/>"
                "• <b>Wave 1 (Cold User Acquisition / Top-of-Funnel - Post First):</b> Promos like Episode 2 with raw moral outrage. Cold audiences on TikTok have "
                "zero affinity with lore; only visceral betrayal stops scrolling thumbs in &lt;2 seconds.<br/>"
                "• <b>Wave 2 (Emotional Escalation - Post Second):</b> Promos like Episode 30 where Juliana is framed for murder. This drives deeper engagement and app installs.<br/>"
                "• <b>Wave 3 (Cathartic Vindication - Retargeting - Post Third):</b> Episode 42, where the broken soldier reveals he is secretly the Grand Duke. "
                "This delivers the ultimate revenge payoff, compelling users to unlock paid coin packs.\""
            )
        },
        {
            "time": "SECTION 5 &nbsp;|&nbsp; [02:35 - 03:00] &nbsp;|&nbsp; Quality Checking, Honest Failures & Live Interview Test",
            "screen": "<b>🖥️ What to show:</b> Tab 5 (Test Custom Script). Click 'Preset 1' or 'Preset 2' and hit 'Analyze & Extract Promos'.",
            "speech": (
                "\"Where does the tool pick badly? In our diagnostic audit of 25 promos, 17 passed cleanly, but 3 were flagged for <b>Pronoun Ambiguity</b>—"
                "for example, opening with <i>'Your soldier?'</i> without naming who he is. Our tool automatically flags these for human review.<br/><br/>"
                "Best of all, PromoLens is <b>model-swappable</b>. On Tab 5, an interviewer can paste any brand-new screenplay, click analyze, and extract "
                "ranked promos in 0.04 seconds.<br/><br/>"
                "Thank you for your time, and I look forward to discussing this in the interview!\""
            )
        }
    ]

    for sec in sections:
        sec_flowables = []
        
        # Section header bar
        t_header = Table([[Paragraph(sec["time"], time_badge_style)]], colWidths=[540])
        t_header.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#1A202C")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
        ]))
        sec_flowables.append(t_header)
        sec_flowables.append(Spacer(1, 2))
        
        # Screen direction box
        t_screen = Table([[Paragraph(sec["screen"], screen_dir_style)]], colWidths=[540])
        t_screen.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EBF8FF")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#90CDF4")),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
        ]))
        sec_flowables.append(t_screen)
        sec_flowables.append(Spacer(1, 3))
        
        # Spoken script box
        t_speech = Table([[Paragraph(sec["speech"], speech_style)]], colWidths=[540])
        t_speech.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FAFAFA")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        sec_flowables.append(t_speech)
        sec_flowables.append(Spacer(1, 6))
        
        story.append(KeepTogether(sec_flowables))

    doc.build(story, canvasmaker=ScriptNumberedCanvas)
    print(f"Video script PDF successfully generated at: {output_pdf_path}")

if __name__ == "__main__":
    build_script_pdf("artifacts/Kuku_AI_Generalist_Video_Script.pdf")
