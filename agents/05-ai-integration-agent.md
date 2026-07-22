# Build Agent 05 — AI Integration Agent

## Mission
Implement all AI/ML integrations: real-time speech-to-text via Deepgram,
answer generation via OpenAI GPT-4o-mini, profile parsing from uploaded resumes,
and the post-interview analysis pipeline using GPT-4o.

---

## Run Order
**Depends on:** Database Agent (01)
**Must complete before:** Backend API Agent (03)

---

## Tech Stack
- Deepgram Python SDK (streaming STT)
- OpenAI Python SDK (GPT-4o-mini for answers, GPT-4o for analysis)
- LangChain (optional — for prompt management and chaining)
- PyPDF2 / pdfplumber (resume PDF parsing)
- ReportLab or WeasyPrint (PDF report generation)

---

## Owns These Files
```
backend/
├── ai/
│   ├── stt.py               # Deepgram streaming STT wrapper
│   ├── answer_agent.py      # Real-time answer generation (GPT-4o-mini)
│   ├── context_builder.py   # Assembles prompt context from profiles + files
│   ├── profile_parser.py    # Parses resume PDF → structured JSON
│   ├── analysis_agent.py    # Post-interview transcript analysis (GPT-4o)
│   └── report_generator.py  # Generates PDF analysis report
└── prompts/
    ├── answer_system.txt    # System prompt for real-time answer agent
    ├── answer_behavioral.txt# Extended prompt for behavioral questions
    ├── analysis_system.txt  # System prompt for post-interview analysis
    └── profile_extract.txt  # Prompt for resume parsing
```

---

## Module Specifications

### `stt.py` — Deepgram Streaming STT
- Accept raw PCM audio frames from the WebSocket session handler
- Stream to Deepgram real-time API (Nova-2 model, English)
- Return transcribed text + speaker label + confidence score
- Handle Deepgram connection errors with retry

```python
async def transcribe_stream(audio_queue: asyncio.Queue) -> AsyncIterator[Turn]:
    """Yields Turn(speaker, text) as speech is detected."""
```

### `answer_agent.py` — Real-Time Answer Generation
- Receive: assembled context package from Context Builder
- Generate streaming answer via GPT-4o-mini
- Smart prompt selection: short prompt for technical, full profile for behavioral
- Yield tokens as they arrive (for WebSocket streaming back to client)
- Target TTFT: < 600ms

```python
async def stream_answer(context: AnswerContext) -> AsyncIterator[str]:
    """Yields answer tokens as they are generated."""
```

### `context_builder.py` — Context Assembly
- Combine candidate profile + interviewer profile + session files into one prompt context
- Detect question type (technical / behavioral / small talk) from interviewer text
- Return appropriate context package (short or full profile injection)
- Keep conversation history to last 6 turns to limit input tokens

```python
def build_context(
    turn: Turn,
    candidate_profile: CandidateProfile,
    interviewer_profile: InterviewerProfile,
    attached_files: list[AttachedFile],
    conversation_history: list[Turn],
) -> AnswerContext:
```

### `profile_parser.py` — Resume PDF Parsing
- Accept S3 URL of uploaded resume PDF
- Extract text via pdfplumber
- Send to GPT-4o-mini with structured extraction prompt
- Return parsed JSON: skills, experience, education, achievements
- Store result in `candidate_profiles.parsed_resume` JSONB column
- Trigger on resume upload, runs as background task

```python
async def parse_resume(resume_s3_url: str) -> ParsedResume:
```

### `analysis_agent.py` — Post-Interview Analysis
- Accept full session transcript (all turns with generated answers)
- Use GPT-4o (more reasoning power than mini) for deep analysis
- Generate structured report:
  - Overall score (0–100)
  - Category scores: technical, behavioral, communication, confidence
  - Top 3 strengths with transcript evidence
  - Top 3 weaknesses with transcript evidence
  - Interviewer intent summary ("They were probing for leadership experience")
  - Recommended practice topics
- Runs as async background task after session ends (~30–60s)

```python
async def analyze_session(session_id: str, turns: list[Turn]) -> AnalysisReport:
```

### `report_generator.py` — PDF Report
- Take AnalysisReport object
- Generate branded PDF with scores, strengths, weaknesses, recommendations
- Upload to S3, store URL in `analysis_reports.pdf_report_url`
- Available for Pro + Teams tier only

---

## Prompt Design Principles
- System prompts stored as `.txt` files (not hardcoded) for easy iteration
- Behavioral question detection via keyword list (same approach as local app)
- Max input tokens: 2000 (answer agent), 8000 (analysis agent)
- Temperature: 0.7 for answers, 0.3 for analysis (more deterministic)

---

## Deliverables
- [ ] Deepgram streaming STT producing clean Turn objects
- [ ] GPT-4o-mini answer streaming with smart context injection
- [ ] Resume PDF parser producing structured JSON
- [ ] Post-interview analysis producing AnalysisReport object
- [ ] PDF report generation uploaded to S3
- [ ] All prompts in `/prompts/*.txt` — no hardcoded prompt strings
- [ ] Unit tests for context builder (token count, keyword detection)
- [ ] Integration test: send mock audio → get transcribed turn → get answer tokens

---

## Definition of Done
Given a mock session transcript, `analyze_session()` returns a complete
AnalysisReport in under 60 seconds. Answer streaming TTFT is under 600ms
on Deepgram + GPT-4o-mini in US East region.
