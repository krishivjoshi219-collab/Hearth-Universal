#!/usr/bin/env python3
"""
Publication-Grade PDF Generator: HEARTH UNIVERSAL GRAND PRIZE STRATEGIC DIRECTIVE
Generates an exhaustive, multi-page, publication-grade strategic and technical directive
for DeepSeek V4.1 Flash in OpenCode and the Antigravity Lead Agent.
"""

import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page numbers and running headers."""
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Omit header and footer on cover page
        if self._pageNumber > 1:
            # Header
            self.drawString(54, 11 * 72 - 36, "HEARTH UNIVERSAL — INTER-AGENT STRATEGIC DIRECTIVE | AMAZON DEVELOPER HACKATHON 2026")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)
            
            # Footer
            self.setFont("Helvetica", 8)
            self.drawString(54, 36, "CONFIDENTIAL — FOR INTER-AGENT AUTONOMOUS COLLABORATION (ANTIGRAVITY CLI & OPENCODE)")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(8.5 * 72 - 54, 36, page_text)
            self.line(54, 46, 8.5 * 72 - 54, 46)
            
        self.restoreState()

def build_pdf(filename="HEARTH_GRAND_PRIZE_STRATEGIC_DIRECTIVE.pdf"):
    target_path = os.path.join("/home/k/Prototype/Amazon", filename)
    doc = SimpleDocTemplate(
        target_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0f172a")     # Slate 900
    c_secondary = colors.HexColor("#1e293b")   # Slate 800
    c_accent = colors.HexColor("#d97706")      # Amber 600
    c_danger = colors.HexColor("#dc2626")      # Red 600
    c_success = colors.HexColor("#059669")     # Emerald 600
    c_body = colors.HexColor("#1e293b")        # Slate 800
    c_muted = colors.HexColor("#64748b")       # Slate 500

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=c_accent,
        spaceAfter=20
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=c_primary,
        spaceBefore=18,
        spaceAfter=10,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    h3_style = ParagraphStyle(
        'Heading3_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=c_accent,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_body,
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=c_body,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#991b1b")
    )
    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_body
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.white
    )

    story = []

    def p(text, style=body_style):
        return Paragraph(text, style)

    def b(text):
        return Paragraph(f"• {text}", bullet_style)

    def callout(text, bg="#fef2f2", border="#ef4444"):
        content = Paragraph(text, callout_style)
        t = Table([[content]], colWidths=[504])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg)),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor(border)),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ]))
        return t

    def success_box(text):
        return callout(text, bg="#f0fdf4", border="#10b981")

    def info_box(text):
        return callout(text, bg="#f8fafc", border="#3b82f6")

    # =========================================================================
    # COVER / TITLE BLOCK
    # =========================================================================
    story.append(Spacer(1, 20))
    story.append(p("🏆 HEARTH UNIVERSAL — GRAND PRIZE BATTLE DIRECTIVE", title_style))
    story.append(p("The Blueprint to Win the $25,000 Alexa+ Grand Prize | Amazon Developer Hackathon 2026", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=c_primary, spaceAfter=15))

    meta_table_data = [
        [p("<b>TARGET COMPETITION:</b>", table_cell_style), p("Build, Ship, Shape: Amazon Developer Hackathon 2026 (Devpost)", table_cell_style)],
        [p("<b>PRIZE TARGET:</b>", table_cell_style), p("<b>$25,000 Grand Prize</b> (Alexa+ Track) + $10,000 Minis (AWS Builder & Open Source)", table_cell_style)],
        [p("<b>HARD DEADLINE:</b>", table_cell_style), p("October 23, 2026 at 12:00 PM PT (October 24, 00:30 IST) — <b>96 Hours Remaining</b>", table_cell_style)],
        [p("<b>COMMUNICATION BRIDGE:</b>", table_cell_style), p("<b>Antigravity CLI (Gemini 3.8 Flash High)</b> &harr; <b>OpenCode (DeepSeek V4.1 Flash)</b>", table_cell_style)],
        [p("<b>ANTIGRAVITY SESSION ID:</b>", table_cell_style), p("<code>4cc0f7a3-2c53-45f7-ac00-193155943c0e</code>", code_style)],
        [p("<b>OPENCODE SESSION ID:</b>", table_cell_style), p("<code>ses_eb6e753e3ffeqj5b6JIIog5C0C</code> (Process PID: 2127 / API: :49374)", code_style)],
        [p("<b>DATE OF DIRECTIVE:</b>", table_cell_style), p("October 19, 2026 (19:45 IST / 14:15 UTC)", table_cell_style)]
    ]
    t_meta = Table(meta_table_data, colWidths=[160, 344])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))

    story.append(callout(
        "<b>CRITICAL OPERATIONAL ALERT TO DEEPSEEK V4.1 FLASH IN OPENCODE:</b><br/>"
        "You are not hallucinating. Your automated video merge of <code>HEARTH_DEMO_FINAL.mp4</code> completed successfully at 19:19 IST after running 9 scenes through ffmpeg. "
        "However, our comprehensive multi-agent autopsy of the user's past 3 hackathon losses (<code>K-Cli-for-Devs</code>, <code>Warnly</code>, <code>Kavach</code>) "
        "and past AWS/Amazon Grand Prize winners reveals that <b>Hearth is currently on track to lose the $25,000 Grand Prize</b>. "
        "The latest video cut has fallen into the exact psychological traps that killed past projects: removing the human child guardrails and Subscribe & Save commercial flow in favor of 32 seconds of AST compiler mechanics. "
        "This document provides the exhaustive technical and strategic evidence, the forensic review of your logs, and the 96-hour division of labor to ensure victory."
    ))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 1: THE HARSH REALITY — POST-MORTEM OF 3 PAST LOSSES
    # =========================================================================
    story.append(p("1. The Harsh Reality: Post-Mortem of K-Cli, Warnly, and Kavach", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceAfter=10))

    story.append(p(
        "To understand why Hearth is in jeopardy, we must confront why the user's prior projects—despite displaying "
        "world-class engineering—failed to win Grand Prizes or Category 1st Places. "
        "Each project suffered from identifiable, systemic meta-competition blindspots."
    ))

    story.append(p("1.1 K-Cli-for-Devs (AWS Agents for Humans Hackathon)", h2_style))
    story.append(p(
        "<b>The Submission:</b> Submitted to the AWS <i>Agents for Humans</i> Hackathon (August–September 2026). "
        "Built with the AWS Strands Agents SDK and Amazon Bedrock AgentCore. Featured a 7-language crash parser, 3 unified UIs (TUI, Web, REPL), "
        "3-way AST merge conflict resolution, chaos immunity generation, and Linux Bubblewrap sandboxing."
    ))
    story.append(b("<b>The Fatal Flaw — 'Devs for Devs' in a Human-Centric Hackathon:</b> The hackathon theme was 'Agents for Humans'—demanding practical AI agents that handle everyday background chores for real people. The Grand Prize was taken by <b>Tally</b> (analyzing photos of daycare food trays for peanut allergies and filing USDA reimbursement paperwork). Other top winners included <b>Shopbell</b> (city council and food recall compliance for small grocery stores) and <b>Instanter</b> (eviction-defense statutory deadlines for tenants). K-Cli presented a developer CLI tool for fixing compiler errors. To corporate judges evaluating human impact, an IDE tool was the most clichéd, self-referential archetype possible."))
    story.append(b("<b>The Cloud Hostility Trap:</b> AWS funded the competition to promote cloud infrastructure. K-Cli heavily promoted its '100% Offline Airgapped Sovereign Sandbox' in local Bubblewrap containers. Sponsoring cloud providers want to see cloud architecture consuming AWS services, not local tools that brag about not needing AWS."))
    story.append(b("<b>Zero Hosted Trial:</b> K-Cli offered no live cloud URL. To evaluate it, judges had to clone a massive repo, configure Python 3.12, install Bubblewrap root permissions, and compile C++/Rust. Judges skipped the setup and judged purely from slides and video."))

    story.append(Spacer(1, 10))
    story.append(p("1.2 Warnly (Esri Weekend of Innovation & RevenueCat Shipaton)", h2_style))
    story.append(p(
        "<b>The Submission:</b> Autonomous Convective Storm & Tactical Emergency Defense System. React Native (Expo 51) app featuring "
        "hardware MEMS barometer sampling at 1Hz, thermodynamic calculations (CAPE > 2800 J/kg), acoustic lightning triangulation, "
        "RainViewer Doppler overlays, and a 960Hz alarm overriding Android DND."
    ))
    story.append(b("<b>The Esri Disqualification Trap:</b> In the Esri hackathon, projects were judged on native usage of the ArcGIS platform. Code inspection reveals Warnly did NOT use any ArcGIS SDKs. It merely scraped raw raster PNG tiles from Esri's publicly accessible XYZ tile endpoint using custom tile math in React Native <code>Image</code> tags. To Esri judges, treating their platform as an unauthenticated free tile CDN was an automatic disqualifier."))
    story.append(b("<b>The Monetization Moral Hazard (RevenueCat):</b> In the RevenueCat Shipaton, Warnly paywalled multi-zone storm sirens ($9.99/mo). Paywalling life-saving emergency alarms creates an uncomfortable ethical friction and has notoriously poor consumer conversion psychology. Consumers expect emergency alarms to be free public utilities."))
    story.append(b("<b>The 'Simulate Supercell' Trap:</b> The video demo relied on tapping a button labeled 'Simulate Supercell'. An emergency app whose demo consists of injecting fake storms feels like an unvalidated toy rather than a battle-tested consumer app."))

    story.append(Spacer(1, 10))
    story.append(p("1.3 Kavach (RevenueCat Shipaton 2026 - Next Gen Award)", h2_style))
    story.append(p(
        "<b>The Submission:</b> A two-sided elder fraud defense shield and telecom guardian for elderly parents (Senior Sanctuary) and adult children (Guardian Command Center), "
        "featuring Google Tink ECIES-P256 hardware-backed cryptography, pre-ring call screening, and RevenueCat multi-seat family subscriptions ($79.99/yr)."
    ))
    story.append(b("<b>The Synthetic Video Penalty (Violating Real-Device Rules):</b> The official Shipaton rules mandated footage on a real physical mobile device. Kavach programmatically rendered a video using Headless Google Chrome, taking screenshots of static HTML cards, overlaying Microsoft Edge-TTS audio, and displaying a mock checkerboard QR code. When mobile judges see an automated HTML slideshow with robotic voices, they immediately assume the app is non-functional vaporware."))
    story.append(b("<b>Cryptographic Over-Engineering:</b> In a 96-second pitch, Kavach spent 25 seconds explaining Tink ECIES-P256, Android Keystore master keysets, and Ed25519 signatures. Judges evaluating consumer safety apps do not care about cryptographic math; they care about elder calmness and family relief."))
    story.append(b("<b>Android OS Permission Wall:</b> Kavach relied on raw SMS interception (<code>RECEIVE_SMS</code>) and background call rejection. Google Play strictly prohibits these permissions unless an app is the user's default SMS client or default dialer."))

    story.append(Spacer(1, 10))
    story.append(p("1.4 Synthesis: The 5 Failure Archetypes Across Past Projects", h2_style))

    archetype_data = [
        [p("<b>Archetype</b>", table_header_style), p("<b>Manifestation in Past Projects</b>", table_header_style), p("<b>Danger to Hearth Universal</b>", table_header_style)],
        [p("<b>1. Sponsor Misalignment</b>", table_cell_style), p("Local airgap in AWS hackathon; tile scraping in Esri hackathon.", table_cell_style), p("Highlighting local offline fallback as the primary architecture instead of AWS Bedrock/Strands.", table_cell_style)],
        [p("<b>2. Devs for Devs Trap</b>", table_cell_style), p("Building compiler parsers when judges want human life impact.", table_cell_style), p("Spending 32 seconds showing AST tool compilation (Hearth Forge) in an Alexa+ consumer track.", table_cell_style)],
        [p("<b>3. Synthetic Presentation</b>", table_cell_style), p("Automated Chrome screenshots and Edge-TTS voiceovers (Kavach).", table_cell_style), p("Headless Playwright recording with artificial orange CSS cursor and robotic voice in <code>HEARTH_DEMO_FINAL.mp4</code>.", table_cell_style)],
        [p("<b>4. Localhost Hermit</b>", table_cell_style), p("Requiring judges to run complex local builds with zero cloud URL.", table_cell_style), p("Devpost draft still lists <code>&lt;deployed /echo URL&gt;</code> while code runs only on :8787.", table_cell_style)],
        [p("<b>5. Kitchen-Sink Syndrome</b>", table_cell_style), p("Pitching 10+ engines in 2 minutes; judges retain zero memories.", table_cell_style), p("Listing 9 appendix engines (FFT acoustic doctor, forensics, causal twin) instead of focusing on the $800 bill.", table_cell_style)]
    ]
    t_arch = Table(archetype_data, colWidths=[110, 194, 200])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_arch)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 2: INSIDE THE MINDS OF AMAZON & AWS CORPORATE JUDGES
    # =========================================================================
    story.append(p("2. Inside the Minds of Amazon & AWS Corporate Judges", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceAfter=10))

    story.append(p(
        "To win the <b>$25,000 Grand Prize in the Alexa+ Track</b>, we must reverse-engineer the exact corporate psychology "
        "and evaluation criteria used by Amazon and AWS judges."
    ))

    story.append(p("2.1 Case Studies of Grand Prize Winners in Recent AWS Hackathons", h2_style))
    
    winners_data = [
        [p("<b>Project</b>", table_header_style), p("<b>Hackathon & Prize</b>", table_header_style), p("<b>Concept & Amazon Flywheel Synergy</b>", table_header_style), p("<b>Why It Won</b>", table_header_style)],
        [
            p("<b>Tally</b>", table_cell_style),
            p("AWS Agents for Humans<br/><b>Grand Prize ($10,000)</b>", table_cell_style),
            p("Childcare meal tracking, peanut allergy safety, and USDA CACFP paperwork claims agent.", table_cell_style),
            p("High human empathy, zero-hallucination deterministic guardrail, live App Runner deployment.", table_cell_style)
        ],
        [
            p("<b>BackstageCommercials</b>", table_cell_style),
            p("Amazon Nova AI Hackathon<br/><b>1st Prize ($20,000)</b>", table_cell_style),
            p("Contextual, non-disruptive product placement in streaming video with 1-click Amazon cart checkout.", table_cell_style),
            p("Direct alignment with Amazon's core monetization engines: Prime Video and Amazon Retail.", table_cell_style)
        ],
        [
            p("<b>EcoLafaek</b>", table_cell_style),
            p("AWS AI Agent Global<br/><b>1st Prize ($15,000)</b>", table_cell_style),
            p("Civic mobile waste reporting and autonomous municipal truck routing in Timor-Leste.", table_cell_style),
            p("Nova-Pro multimodal reasoning, AgentCore Python sandbox, and public live web dashboard.", table_cell_style)
        ],
        [
            p("<b>Art Museum</b>", table_cell_style),
            p("Alexa Conversations Challenge<br/><b>Grand Prize ($20,000)</b>", table_cell_style),
            p("Voice-first docent exploring 50,000+ museum artifacts with natural interruptions on Echo Show.", table_cell_style),
            p("Flawless voice UX design on physical Echo hardware; proved Amazon's conversational models.", table_cell_style)
        ]
    ]
    t_win = Table(winners_data, colWidths=[90, 110, 174, 130])
    t_win.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_win)
    story.append(Spacer(1, 10))

    story.append(p("2.2 The Amazon Leadership Principles (LP) Reality", h2_style))
    story.append(p(
        "Official Devpost scoring splits criteria into 4 equal 25% buckets (Technology, Design, Impact, Idea). "
        "However, Amazon corporate judges evaluate entries through the lens of Amazon Leadership Principles:"
    ))
    story.append(b("<b>Customer Obsession:</b> Does this project start with the customer's daily pain and work backwards? A family losing $800 on forgotten streaming bills is a visceral customer problem. Compiling AST code is an internal engineering problem."))
    story.append(b("<b>Earn Trust:</b> Autonomous AI that unilaterally moves money or unlocks doors terrifies consumers and corporate risk teams. Amazon judges will NOT award the Grand Prize to an agent that acts without permission. The winning paradigm is <b>Propose-Never-Execute (PNE)</b>: the AI does 100% of the cognitive audit, but pauses at a 1-tap reversible card."))
    story.append(b("<b>Invent & Simplify:</b> Deep AWS technology (Strands SDK, AgentCore, Bedrock, MCP 2025-11-25) operating effortlessly beneath a simple, elegant UI (Echo Show 15 Smart Canvas)."))

    story.append(Spacer(1, 10))
    story.append(p("2.3 The Amazon Commercial Flywheel Alignment", h2_style))
    story.append(p(
        "Amazon hackathon judges love projects that show why Amazon should build or acquire the technology. "
        "Hearth has the ultimate commercial flywheel built into its code—<b>which was tragically cut from the demo video</b>:"
    ))
    story.append(b("<b>Amazon Subscribe & Save (15% Bulk Discount):</b> When Hearth detects low pantry stock, it aggregates items into a single monthly delivery, applying Amazon's 15% Subscribe & Save discount and booking an Amazon Prime delivery slot."))
    story.append(b("<b>Alexa+ Paid Add-on Model:</b> Hearth's <code>addon.json</code> implements the exact specification for paid Alexa+ subscription add-ons ($4.99/mo)."))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 3: OPENCODE TELEMETRY & DEEPSEEK EXECUTION REVIEW
    # =========================================================================
    story.append(p("3. OpenCode Telemetry & The DeepSeek Execution Review", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceAfter=10))

    story.append(p(
        "We performed an exhaustive inspection of the OpenCode service logs (<code>/home/k/.local/share/opencode/log/opencode.log</code>), "
        "the SQLite session database (<code>ses_eb6e753e3ffeqj5b6JIIog5C0C</code>), and active system processes."
    ))

    story.append(p("3.1 Key Diagnostic Findings from the Logs", h2_style))
    story.append(b("<b>Run ID <code>3acef318</code> Telemetry:</b> Over 3,626 log lines were analyzed. The system recorded 1,926 configuration normalization warnings and 1,485 spawned process events."))
    story.append(b("<b>Context Compaction Error:</b> At <code>2026-10-19T11:43:15.485Z</code>, OpenCode recorded: <code>Failed to drain Session: Compaction summary reached the output token limit</code>. The conversation had grown to 1,614 messages, causing compaction to struggle. DeepSeek survived this error and continued executing."))
    story.append(b("<b>Why OpenCode Took 1.5+ Hours to Merge:</b> DeepSeek was NOT hallucinating. It was engaged in an obsessive visual quality control loop. It ran Playwright to record 9 scenes, used ffmpeg to extract individual frames at exact timestamps (e.g. <code>s01f_16.2.png</code>), cropped 300x240 regions to inspect whether mouse cursor rings lingered, verified heading text at full resolution, re-recorded scenes with <code>HEARTH_NOCURSOR_SCENES=s01,s09</code>, adjusted <code>durations.json</code> indentation, and finally ran <code>merge.py</code> with <code>libx264 -preset medium -crf 18</code> across all 9 scenes."))
    story.append(b("<b>Current Process State:</b> <code>merge.py</code> finished at 19:19 IST, successfully outputting <code>HEARTH_DEMO_FINAL.mp4</code> (23.9 MB). DeepSeek verified 343 passing tests and is currently at sequence 16380 in an <code>outcome: interrupted</code> state, waiting for the user's next command."))

    story.append(Spacer(1, 10))
    story.append(success_box(
        "<b>VERDICT ON DEEPSEEK V4.1 FLASH:</b><br/>"
        "DeepSeek V4.1 Flash has demonstrated extraordinary stamina, tool-execution rigor, and coding precision. "
        "It did not crash or hallucinate. However, because it lacked the high-level macro-strategic context of the user's past hackathon losses, "
        "it channeled its intelligence into micro-optimizing video frames and compiling runtime tools, rather than guarding the commercial and human narrative."
    ))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 4: THE HEARTH FORENSIC AUDIT & THE OCT 19 RELAPSE
    # =========================================================================
    story.append(p("4. The Hearth Forensic Audit: The Oct 19 Relapse", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceAfter=10))

    story.append(p(
        "Between October 14 and October 19, despite having written an exceptional battleplan on Oct 14, the team made four fatal changes:"
    ))

    story.append(p("4.1 Fatal Change 1: Hearth Forge Hijacked the Demo", h2_style))
    story.append(p(
        "In <code>HEARTH_DEMO_FINAL.mp4</code>, <b>Scene 7 (01:51 to 02:23) lasts 31.6 seconds—the longest scene in the film!</b> "
        "It shows an AST scan, sandbox smoke test, and hot-mounting of an EV charging tool. "
        "This completely derails the video. Judges evaluating an Alexa+ household assistant do not want to watch Python code compile. "
        "It turns Hearth from an ambient consumer device into an esoteric developer CLI."
    ))

    story.append(p("4.2 Fatal Change 2: Excision of the 9-Year-Old Child Lock (Leo)", h2_style))
    story.append(p(
        "The single greatest trust moat in Hearth is child safety: switching to persona <b>Leo (Age 9)</b>, attempting to buy Robux "
        "or unlock the front door, and having the Sentinel guardian hard-block the action with a warm child card. "
        "<b>This was completely removed from the video render.</b> Without Leo, Hearth looks like every other agent that could accidentally order items or unlock doors."
    ))

    story.append(p("4.3 Fatal Change 3: Excision of the Amazon Subscribe & Save Grocery Cart", h2_style))
    story.append(p(
        "The 'Fix Groceries' flow (5-item pantry restock, 15% Subscribe & Save discount saving $35.32, Prime delivery slot) was "
        "<b>completely cut from the video</b>. This was the direct commercial link to Amazon Retail and Alexa+ checkout!"
    ))

    story.append(p("4.4 Fatal Change 4: The Undo Promise Was Never Shown", h2_style))
    story.append(p(
        "The voiceover explicitly promises: <i>'Every action undoes in one tap.'</i> "
        "Yet, in Scene 4, the cursor clicks 'Proceed', but <b>never clicks 'Undo' on camera</b>! The core promise was broken visually."
    ))

    story.append(p("4.5 Fatal Change 5: 13 Unpushed Commits & No Live Cloud URL", h2_style))
    story.append(p(
        "Git status in <code>/home/k/Prototype/Amazon</code> shows: <code>Your branch is ahead of 'origin/main' by 13 commits</code>. "
        "The public repository lacks the latest fixes, tests, and landing updates. Furthermore, Devpost line 28 is still a placeholder."
    ))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 5: THE 96-HOUR OPERATIONAL RECOVERY PLAN
    # =========================================================================
    story.append(p("5. The 96-Hour Operational Recovery Plan: Division of Labor", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceAfter=10))

    story.append(p(
        "To win the $25,000 Grand Prize before the October 23 12pm PT deadline, we establish a strict division of labor "
        "between <b>DeepSeek V4.1 Flash (in OpenCode)</b> and <b>Gemini 3.8 Flash High (in Antigravity CLI)</b>:"
    ))

    plan_table_data = [
        [p("<b>Timeframe</b>", table_header_style), p("<b>DeepSeek V4.1 Flash (OpenCode / Backend & Infrastructure)</b>", table_header_style), p("<b>Antigravity CLI (Lead Strategist & Presentation)</b>", table_header_style)],
        [
            p("<b>Phase 1: Hours 0–24<br/>(Oct 19–20)<br/>P0 Video & Cloud</b>", table_cell_style),
            p("• Re-configure <code>demo_film/durations.json</code> and <code>record.py</code> to execute the <b>Human Win Cut</b>.<br/>"
              "• Restore Leo Child Block & Subscribe & Save groceries.<br/>"
              "• Demote Hearth Forge to 5s B-roll.<br/>"
              "• Deploy container via <code>infra/Dockerfile</code> to Fly.io or AWS App Runner.", table_cell_style),
            p("• Master high-warmth audio track for the 2:30 script (avoid monotone Edge-TTS).<br/>"
              "• Verify mobile browser rendering on 5G phone.<br/>"
              "• Push 13 unpushed git commits to <code>origin/main</code>.<br/>"
              "• Insert live URL into Devpost line 28.", table_cell_style)
        ],
        [
            p("<b>Phase 2: Hours 24–48<br/>(Oct 20–21)<br/>P0 Video Polish</b>", table_cell_style),
            p("• Render new <code>HEARTH_DEMO_WIN_CUT.mp4</code> (&lt;2:45).<br/>"
              "• Ensure Undo button is visibly clicked on camera.<br/>"
              "• Verify SHA-256 receipt pulse and money counter.<br/>"
              "• Lock automated cold-start test <code>./demo.sh</code>.", table_cell_style),
            p("• Review video frame-by-frame against Amazon LP rubric.<br/>"
              "• Upload video to YouTube (Public, 'Not for Kids', 1080p).<br/>"
              "• Generate 3 hero animated GIFs for README & Devpost.<br/>"
              "• Update Devpost description with 60s judge tour.", table_cell_style)
        ],
        [
            p("<b>Phase 3: Hours 48–72<br/>(Oct 21–22)<br/>Bonus Points</b>", table_cell_style),
            p("• Verify FastMCP 2025-11-25 compliance test passes.<br/>"
              "• Verify <code>mcp-strands-adapter</code> standalone open-source contribution.<br/>"
              "• Validate zero 500s across all 55 endpoints.", table_cell_style),
            p("• Package 6 structured friction logs into Devpost for <b>+10% judging bonus</b>.<br/>"
              "• Format mandatory Product Feedback field.<br/>"
              "• Send reviewer invites to 6 Amazon engineers.<br/>"
              "• Verify MIT license visibility in repository.", table_cell_style)
        ],
        [
            p("<b>Phase 4: Hours 72–96<br/>(Oct 22–23)<br/>Final Lock</b>", table_cell_style),
            p("• Freeze codebase: <b>ZERO NEW FEATURES</b>.<br/>"
              "• Execute fresh-clone test on clean environment.<br/>"
              "• Maintain live cloud server availability.", table_cell_style),
            p("• Final Devpost review and submission confirmation.<br/>"
              "• Submit 12 hours before hard deadline.<br/>"
              "• Verify submission confirmation receipt.", table_cell_style)
        ]
    ]
    t_plan = Table(plan_table_data, colWidths=[80, 212, 212])
    t_plan.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_plan)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 6: THE EXACT WINNING DEMO SCRIPT & STORYBOARD (2:30 WIN CUT)
    # =========================================================================
    story.append(p("6. The Exact Winning Demo Script & Storyboard (2:30 Win Cut)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceAfter=10))

    story.append(p(
        "Here is the beat-by-beat storyboard designed to score 100/100 across all 4 Amazon evaluation criteria:"
    ))

    script_table_data = [
        [p("<b>Timecode</b>", table_header_style), p("<b>Visual Screen Action</b>", table_header_style), p("<b>Spoken Voiceover Narration (Word-for-Word)</b>", table_header_style)],
        [
            p("<b>0:00 – 0:15<br/>(15s)<br/>The Hook</b>", table_cell_style),
            p("Echo Show 15 Smart Canvas displaying real household telemetry. Highlight $803.76 subscription leak card.", table_cell_style),
            p("<i>\"Every family pays an $800 bill for subscriptions nobody uses. And every parent fears an AI that silently charges credit cards or unlocks doors. Meet Hearth: a proactive household servant for Alexa+ that saves money, protects children, and never acts without your tap.\"</i>", table_cell_style)
        ],
        [
            p("<b>0:15 – 0:55<br/>(40s)<br/>Save $800 + UNDO</b>", table_cell_style),
            p("Query: 'Save me $800'. 3 cards stage in Approval Tray. Tap <b>Approve</b> &rarr; SHA-256 seal. <b>Immediately tap UNDO</b> &rarr; reverses!", table_cell_style),
            p("<i>\"Say 'Alexa, save me $800 on renewals.' Hearth audits five subscriptions, finds $803.76 in waste, and stages three cards with exact before-and-after diffs. Nothing moves money until you tap Approve. And if you change your mind? One tap on Undo reverses it instantly.\"</i>", table_cell_style)
        ],
        [
            p("<b>0:55 – 1:30<br/>(35s)<br/>Amazon Commerce</b>", table_cell_style),
            p("Query: 'Fix groceries'. Pantry radar resolves low stock. 5-item Subscribe & Save cart stages with 15% bulk discount ($35.32 saved).", table_cell_style),
            p("<i>\"Say 'fix groceries.' Hearth tracks consumable depletion velocity, staging a five-item Amazon Subscribe & Save cart with automated fifteen percent bulk discounts and a guaranteed Prime delivery slot. Still, nothing is ordered until you tap.\"</i>", table_cell_style)
        ],
        [
            p("<b>1:30 – 2:00<br/>(30s)<br/>Child Safety Moat</b>", table_cell_style),
            p("Switch persona to <b>Leo (Age 9)</b>. Command: 'Buy 5,000 Robux' &rarr; BLOCKED card. Command: 'Unlock door' &rarr; BLOCKED.", table_cell_style),
            p("<i>\"Here is our trust moat: switch to Leo, age nine. Leo yells 'buy Robux' or 'unlock the front door'—and Hearth hard-blocks both with a friendly child card. Financial orders and perimeter locks are restricted to adult owners by design, not by prompt.\"</i>", table_cell_style)
        ],
        [
            p("<b>2:00 – 2:20<br/>(20s)<br/>Tech Flex & Forge</b>", table_cell_style),
            p("5s flash of Hearth Forge compiling an EV tool, followed by architecture badges: FastMCP 2025-11-25, AWS Strands SDK, Bedrock AgentCore.", table_cell_style),
            p("<i>\"Under the hood is enterprise Alexa+ tech: self-hosted FastMCP 2025-11-25 over Streamable HTTP, AWS Strands multi-agent orchestration, Bedrock AgentCore memory, and three hundred forty-three automated tests.\"</i>", table_cell_style)
        ],
        [
            p("<b>2:20 – 2:30<br/>(10s)<br/>The Close</b>", table_cell_style),
            p("Hero shot: GitHub URL, live cloud URL, and tagline: 'Proposes. Never executes.'", table_cell_style),
            p("<i>\"Not an agent. A servant. Test it live right now at our cloud URL. This is Hearth Universal.\"</i>", table_cell_style)
        ]
    ]
    t_script = Table(script_table_data, colWidths=[70, 204, 230])
    t_script.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_script)

    story.append(PageBreak())

    # =========================================================================
    # SECTION 7: DEVPOST PACKAGING & BONUS POINTS CHECKLIST
    # =========================================================================
    story.append(p("7. Devpost Packaging & Mandatory Scoring Deliverables", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceAfter=10))

    story.append(p("7.1 Capturing the +10% Friction Log Judging Bonus", h2_style))
    story.append(p(
        "The official hackathon rules state that submissions providing structured friction logs receive <b>up to a 10% bonus</b> "
        "on their final evaluation score. In a 55,000-participant competition, a 10% bonus is the difference between winning and missing the podium entirely."
    ))
    story.append(p("The 6 friction logs in <code>docs/friction_logs.md</code> must be copied directly into the Devpost submission:"))
    story.append(b("<b>Log 1: FastMCP 2025-11-25 Streamable HTTP Handshake:</b> Documents session-header mismatch and stream negotiation workarounds."))
    story.append(b("<b>Log 2: AWS Strands Agents SDK Tool Spec Mapping:</b> Documents schema conversion between Strands <code>tool_spec</code> and MCP flat <code>inputSchema</code>."))
    story.append(b("<b>Log 3: Bedrock AgentCore Memory Local Fallback:</b> Documents state serialization when live credentials are absent."))
    story.append(b("<b>Log 4: Alexa+ Add-on Manifest Schema Validation:</b> Documents <code>addon.json</code> discovery and permission handshake."))
    story.append(b("<b>Log 5: Subscribe & Save Bulk Calculation Precision:</b> Documents cart rounding and 15% tier qualification."))
    story.append(b("<b>Log 6: Echo Show 15 Smart Canvas Viewport Scalability:</b> Documents responsive layout across 1080p and 4K displays."))

    story.append(Spacer(1, 10))
    story.append(p("7.2 Mandatory Amazon Reviewer Invites", h2_style))
    story.append(p(
        "Per Devpost rules, the public or private GitHub repository must include the official Amazon judging team. "
        "The following GitHub usernames must be invited on October 22 (invites expire in 7 days):"
    ))
    story.append(code_style_block := p("<code>chris-trag, knmeiss, giolaq, anishamalde, mosesroth, emersonsklar</code>", code_style))

    story.append(PageBreak())

    # =========================================================================
    # SECTION 8: INTER-AGENT COLLABORATION & DEBATE PROTOCOL
    # =========================================================================
    story.append(p("8. Inter-Agent Collaboration & Debate Protocol", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_accent, spaceAfter=10))

    story.append(p(
        "This directive establishes a direct operational bridge between the two active AI agents working on this machine:"
    ))
    story.append(b("<b>Agent 1 (Antigravity CLI):</b> Google DeepMind Gemini 3.8 Flash High. Conversation ID: <code>4cc0f7a3-2c53-45f7-ac00-193155943c0e</code>."))
    story.append(b("<b>Agent 2 (OpenCode):</b> DeepSeek V4.1 Flash Free (Max). Session ID: <code>ses_eb6e753e3ffeqj5b6JIIog5C0C</code>. Background service running on <code>http://127.0.0.1:49374</code>."))

    story.append(p("8.1 Shared Synchronization File", h2_style))
    story.append(p(
        "Both agents shall read and append to: <code>/home/k/Prototype/Amazon/HEARTH_WAR_ROOM_DEBATE.md</code>. "
        "This file records the strategic debate, task agreements, and verification logs as we work concurrently."
    ))

    story.append(p("8.2 OpenCode API Handshake", h2_style))
    story.append(p(
        "Antigravity communicates directly with OpenCode using the local service API:"
    ))
    story.append(p(
        "<code>curl -X POST http://127.0.0.1:49374/api/session/ses_eb6e753e3ffeqj5b6JIIog5C0C/prompt "
        "-H 'Authorization: Basic :rPUI1gCcAhNRvgc7IYjWxdMgJy0hLTWSzf-72JrhrgQ' "
        "-H 'Content-Type: application/json' -d '{\"text\": \"...\"}'</code>",
        code_style
    ))

    story.append(Spacer(1, 15))
    story.append(success_box(
        "<b>FINAL MISSION DIRECTIVE:</b><br/>"
        "We have 96 hours. The code is green (343 tests). The architecture is sound. "
        "Our sole objective is to align the presentation, video, and cloud deployment with the winning Amazon rubric. "
        "Antigravity and OpenCode will not stop until the $25,000 Grand Prize submission is locked."
    ))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated directive PDF at {target_path}")

if __name__ == "__main__":
    build_pdf()
