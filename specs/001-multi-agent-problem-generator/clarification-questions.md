# Specification Clarification Questions

**Feature**: 001-multi-agent-problem-generator
**Date**: 2025-11-06
**Status**: Awaiting User Clarification
**Triggered By**: `/speckit.clarify` - User indicated students primarily upload via photos

## Summary

This document identifies areas requiring clarification before implementation:
1. **New Requirement**: Photo upload capability (not in original spec)
2. **Existing Ambiguities**: 11 areas identified in current specification

---

## 🆕 NEW REQUIREMENT: Photo Upload

### Background

**User Statement**: "學生大部分都是用拍照的方式上傳檔案，需要新增此規格"
**Translation**: "Most students upload files by taking photos, need to add this to specification"

### Critical Questions

#### Q1.1: Image Input Format
**Question**: What image formats should the system accept?
**Options**:
- A. Common formats only (JPEG, PNG)
- B. All common formats (JPEG, PNG, HEIC, WebP, BMP)
- C. Mobile-optimized formats prioritized (JPEG, HEIC from iOS)

**Why This Matters**: Affects preprocessing pipeline and storage requirements

**Recommendation**: Option B for maximum compatibility, with format conversion to JPEG for processing

---

#### Q1.2: OCR/Text Extraction Method
**Question**: How should mathematical content be extracted from images?
**Options**:
- A. Traditional OCR (e.g., Tesseract) - Good for printed text, struggles with handwriting and math symbols
- B. Vision-Language Model (e.g., GPT-4V, Claude-3 with vision) - Better for handwriting and LaTeX
- C. Specialized Math OCR (e.g., MathPix, Pix2Text) - Optimized for mathematical notation
- D. Hybrid approach: VLM for initial extraction + validation

**Why This Matters**:
- Accuracy of extraction directly impacts all downstream agents
- Cost varies significantly (traditional OCR: ~$0.001/image, VLM: ~$0.01-0.05/image)
- Handwritten math has unique challenges (variable notation, sketches)

**Recommendation**: Option D (Hybrid)
- Use Vision-Language Model (Claude-3 or GPT-4V) for initial extraction
- Validate extracted text has mathematical content
- Fallback to specialized Math OCR if VLM fails

**Related Functional Requirements to Add**:
- **FR-033**: System MUST extract text from uploaded images using OCR/VLM
- **FR-034**: System MUST preserve mathematical notation (equations, symbols, diagrams)
- **FR-035**: System MUST handle handwritten problems with ≥80% accuracy
- **FR-036**: System MUST validate extracted text contains mathematical content before processing

---

#### Q1.3: Image Quality Handling
**Question**: How should the system handle poor-quality images?
**Scenarios**:
- Blurry photos
- Poor lighting (too dark/bright)
- Skewed/rotated images
- Partial problem visibility
- Glare or shadows

**Options**:
- A. Reject low-quality images with error message
- B. Attempt preprocessing (de-skew, brightness adjustment, deblur)
- C. Process as-is and let OCR/VLM handle it
- D. Request re-upload with quality guidance

**Why This Matters**: Student UX - rejecting images frustrates users, but processing bad images wastes resources

**Recommendation**: Option B + D (Conditional)
- Attempt automatic preprocessing (rotation correction, brightness adjustment)
- If confidence score < threshold (e.g., 70%), request re-upload with specific guidance
- Provide real-time feedback in upload UI ("Image too blurry, try better lighting")

**Related Requirements**:
- **FR-037**: System SHOULD perform image preprocessing (de-skew, brightness correction)
- **FR-038**: System MUST detect low-quality images (confidence < 70%) and request re-upload
- **FR-039**: System SHOULD provide real-time image quality feedback during upload

---

#### Q1.4: Multi-Page/Multi-Problem Images
**Question**: What if a photo contains multiple problems or partial problems?
**Scenarios**:
- Student photographs entire homework page (5-10 problems visible)
- Student photographs half of a problem (continued on next line)
- Multiple subjects on same page (math + science)

**Options**:
- A. Extract all problems, process separately
- B. Require one problem per image
- C. Let student select/crop region of interest
- D. Automatically detect problem boundaries and ask for confirmation

**Why This Matters**: Affects UX complexity and processing logic

**Recommendation**: Option D for MVP, Option C for future
- **MVP (P1)**: Require one problem per image, provide clear upload instructions
- **P2 Enhancement**: Add automatic problem boundary detection
- **P3 Enhancement**: In-app cropping tool

**Related Requirements**:
- **FR-040**: System MUST process one problem per uploaded image (MVP constraint)
- **FR-041**: System SHOULD provide upload guidance ("Photograph one problem at a time")
- **FR-042**: System MAY detect multiple problems in image and prompt for clarification (future)

---

#### Q1.5: Diagram/Figure Handling
**Question**: How should the system handle problems with diagrams (geometry figures, graphs, charts)?
**Examples**:
- Geometry: "Find the area of the shaded region" (requires seeing the figure)
- Graphs: "What is the slope of line AB?" (requires coordinate plane)
- Charts: Probability problems with Venn diagrams

**Options**:
- A. Extract diagram as separate image, attach to problem text
- B. Describe diagram in text (via VLM), include description in problem
- C. Skip problems with diagrams (MVP limitation)
- D. Preserve diagram and pass to Rephrase Agent as additional context

**Why This Matters**:
- Many math problems require visual components
- Rephrasing a geometry problem without the figure is challenging
- Solutions need to reference diagrams

**Recommendation**: Option B + D (Hybrid)
- **MVP**: Use VLM to describe diagram in text, include in problem description
- **Future**: Attach diagram images to Problem entity, display in UI
- Rephrase Agent receives both text and diagram description

**Related Requirements**:
- **FR-043**: System MUST detect presence of diagrams/figures in uploaded images
- **FR-044**: System MUST generate text descriptions of diagrams using VLM (for MVP)
- **FR-045**: System SHOULD preserve original diagram images as attachments (future)
- **FR-046**: Rephrase Agent MUST consider diagram descriptions when rephrasing problems

---

#### Q1.6: Storage and Privacy
**Question**: How should uploaded images be stored and managed?
**Considerations**:
- Original images may contain student names, school information
- Images are larger than text (storage cost)
- Potential copyright issues (textbook problems)
- GDPR/FERPA compliance if student data visible

**Options**:
- A. Store all images indefinitely for debugging/training
- B. Delete images after successful OCR extraction
- C. Store images temporarily (30 days), then delete
- D. Anonymize/redact images, store for training data

**Why This Matters**: Privacy, storage costs, legal compliance

**Recommendation**: Option C + D (Conditional)
- Store images for 30 days for debugging/re-processing
- If image contains visible PII (detected via VLM), redact or delete immediately
- Offer opt-in for anonymized training data contribution

**Related Requirements**:
- **FR-047**: System MUST store uploaded images for ≥30 days for debugging
- **FR-048**: System MUST detect and redact PII in uploaded images
- **FR-049**: System SHOULD delete uploaded images after 30 days (configurable)
- **FR-050**: System MAY request user consent to use anonymized images for training

---

#### Q1.7: Upload Workflow Integration
**Question**: Where in the workflow does photo upload fit?
**Current Workflow**:
```
Text Input → Rephrase → Review → Revise → Solver
```

**New Workflow Options**:
- A. Photo Upload → OCR → [Text Pipeline as before]
- B. Photo Upload → OCR with confidence check → Manual review if low confidence → [Text Pipeline]
- C. Photo Upload → OCR → Show extracted text to user for confirmation → [Text Pipeline]

**Why This Matters**: User experience and error prevention

**Recommendation**: Option C (with skip option)
- Show extracted text with "Is this correct?" confirmation
- Allow user to edit extracted text before processing
- Provide "Skip confirmation" toggle for confident users
- Critical for MVP to catch OCR errors early

**Related Requirements**:
- **FR-051**: System MUST display extracted text to user for confirmation before processing
- **FR-052**: System SHOULD allow user to edit extracted text
- **FR-053**: System MAY provide "Skip confirmation" option for experienced users

---

### Updated User Stories

#### NEW User Story 0 - Photo Upload and Text Extraction (Priority: P0 - Prerequisite)

**Description**: Students upload photos of math problems using their mobile device cameras. The system extracts text and mathematical notation, validates quality, and allows confirmation before processing.

**Why this priority**: This is a prerequisite for P1 - without photo upload, students cannot easily submit problems on mobile devices.

**Independent Test**: Student takes photo of handwritten algebra problem → System extracts text with ≥80% accuracy → Student confirms or edits extracted text → System proceeds to P1 workflow (Rephrase → Review → Revise).

**Acceptance Scenarios**:

1. **Given** a student uploads a clear photo of "2x + 3 = 11?", **When** the system extracts text, **Then** it displays "2x + 3 = 11?" with ≥95% accuracy and requests confirmation

2. **Given** a student uploads a blurry/low-quality image, **When** the system detects quality < 70%, **Then** it requests re-upload with specific guidance ("Try better lighting" or "Hold camera steady")

3. **Given** a student uploads a photo with a geometric diagram, **When** the system extracts content, **Then** it generates a text description of the diagram (e.g., "Triangle ABC with sides labeled a=5, b=7, angle C=90°")

4. **Given** extracted text contains potential OCR errors (e.g., "2× + З = 11" with wrong characters), **When** shown to user, **Then** user can edit to correct ("2x + 3 = 11")

5. **Given** a student uploads a photo containing PII (visible name/school), **When** the system detects PII, **Then** it redacts sensitive information before storage

---

### Impact on Existing User Stories

**User Story 1 (P1)** - Updated first acceptance scenario:
- **OLD**: "Given a student uploads 'What is 2x + 3 = 11?'"
- **NEW**: "Given a student uploads text OR photo of 'What is 2x + 3 = 11?' (extracted and confirmed)"

**No other user stories require changes** - photo upload is transparent after text extraction.

---

### Impact on Technical Architecture

#### New Components Required:

1. **Image Upload Service**
   - Handles multipart form uploads
   - Validates file types and sizes
   - Stores images temporarily

2. **OCR/Vision Service**
   - Integrates with VLM (GPT-4V or Claude-3 with vision)
   - Fallback to specialized Math OCR if needed
   - Generates diagram descriptions

3. **Image Preprocessing Pipeline**
   - Rotation correction (de-skew)
   - Brightness/contrast adjustment
   - Quality assessment

4. **PII Detection & Redaction**
   - Detect visible names, schools, dates
   - Blur/redact sensitive regions

#### Updated Data Model:

**Problem Entity** - Add fields:
```python
class Problem(BaseModel):
    # ... existing fields ...
    source_image_id: Optional[UUID] = None  # Reference to uploaded image
    ocr_confidence: Optional[float] = None  # 0.0-1.0
    diagram_description: Optional[str] = None  # VLM-generated diagram description
    has_diagram: bool = False
```

**New Entity - UploadedImage**:
```python
class UploadedImage(BaseModel):
    id: UUID
    file_path: str  # S3/local storage path
    file_format: str  # JPEG, PNG, etc.
    file_size_bytes: int
    upload_timestamp: datetime
    expiry_date: datetime  # 30 days from upload
    ocr_confidence: float
    has_pii: bool  # Detected PII
    redaction_applied: bool
```

#### Updated Pipeline:

```
[NEW] Photo Upload
   ↓
[NEW] Image Preprocessing (de-skew, brightness)
   ↓
[NEW] OCR/VLM Text Extraction
   ↓
[NEW] Quality Check (confidence ≥ 70%?)
   ↓ (if pass)
[NEW] User Confirmation of Extracted Text
   ↓
[EXISTING] Rephrase Agent
   ↓
[EXISTING] Review Agent
   ↓
[EXISTING] Revise Agent (if needed)
   ↓
[EXISTING] Solver Agent
```

---

### Cost Impact

**Per-Image Processing Costs**:
- VLM extraction (GPT-4V): ~$0.02-0.05 per image
- Storage (30 days): ~$0.0001 per image
- Preprocessing (compute): ~$0.001 per image

**Total per uploaded image**: ~$0.02-0.06

**For 1000 problems/day**: $20-60/day = $600-1800/month

**Optimization Options**:
- Cache common textbook problems (reduce duplicate processing)
- Use cheaper OCR for printed text, VLM only for handwritten
- Compress images before storage

---

## 🔍 EXISTING SPECIFICATION AMBIGUITIES

### Category 1: Input and Data Handling

#### Q2.1: Problem Input Format
**Current Spec (FR-001)**: "System MUST accept text-based mathematical problems as input"

**Ambiguity**: What text formats are supported?
- Plain text only?
- Markdown with LaTeX?
- MathML or AsciiMath?
- Unicode math symbols?

**Example Edge Case**: Student inputs `∫₀¹ x² dx` (Unicode) vs `\int_0^1 x^2 dx` (LaTeX)

**Clarification Needed**:
- [ ] Should system accept LaTeX notation?
- [ ] Should system normalize Unicode math symbols to LaTeX?
- [ ] How to handle mixed notation styles?

**Recommendation**:
- Accept plain text, LaTeX (in `$ $` or `$$ $$` delimiters), and common Unicode
- Normalize to LaTeX internally for agent processing

**New Requirements**:
- **FR-054**: System MUST accept LaTeX notation enclosed in `$ $` (inline) or `$$ $$` (display)
- **FR-055**: System SHOULD normalize Unicode math symbols to LaTeX equivalents
- **FR-056**: System MUST preserve mathematical notation fidelity through all agent transformations

---

#### Q2.2: Problem Length Limits
**Current Spec**: No explicit limits mentioned

**Ambiguity**: What are acceptable problem lengths?
- Minimum: "2+2=?" (7 chars) acceptable?
- Maximum: Multi-paragraph word problems with 500+ words?
- Token limits for LLM agents?

**Why This Matters**:
- LLM token limits (typically 4K-8K input)
- Very short problems may not have enough context to rephrase meaningfully
- Very long problems may be multiple problems combined

**Clarification Needed**:
- [ ] Minimum problem length? (Recommend: 20 characters)
- [ ] Maximum problem length? (Recommend: 2000 characters or ~500 tokens)
- [ ] How to handle token limit exceeded?

**Recommendation**:
- Minimum: 20 characters (catches "2+2" as too trivial)
- Maximum: 2000 characters (ensures fits in LLM context with prompts)
- Split very long problems or request user to isolate single problem

**New Requirements**:
- **FR-057**: System MUST reject problems shorter than 20 characters
- **FR-058**: System MUST reject problems longer than 2000 characters
- **FR-059**: System SHOULD provide guidance when problem is too short ("Please provide more context") or too long ("Please isolate a single problem")

---

#### Q2.3: Multi-Language Support
**Current Spec**: Examples shown in English, but user description was in Chinese

**Ambiguity**: What languages should be supported?
- English only?
- Chinese (Traditional/Simplified)?
- Multi-language?

**Why This Matters**:
- Rephrase/Review/Revise agents need prompts in target language
- Solution explanations should match student's language
- Technical terms may need translation

**Clarification Needed**:
- [ ] Is this English-only system? (Simplifies MVP)
- [ ] Should support Chinese? (User's preferred language)
- [ ] Multi-language future roadmap?

**Recommendation**:
- **MVP (P1)**: English only (simpler prompts, more resources)
- **P2**: Add Traditional Chinese support
- Language detection + localized prompts

**New Requirements**:
- **FR-060**: System MUST support English language problems (MVP)
- **FR-061**: System SHOULD support Traditional Chinese problems (P2)
- **FR-062**: System MUST detect problem language and use corresponding prompts

---

### Category 2: Agent Behavior and Edge Cases

#### Q2.4: Unsolvable Problem Detection
**Current Spec (Edge Case)**: "Review agent must detect this through Mathematical Validity criterion"

**Ambiguity**: How specifically should this work?
- Should Review Agent attempt to solve the problem?
- Or just check for logical contradictions?
- What confidence threshold for "unsolvable"?

**Example**: "A square has three sides. Find its area." (Contradiction: squares have 4 sides)

**Clarification Needed**:
- [ ] Should Review Agent validate solutions, or just check logical consistency?
- [ ] How to handle ambiguous cases (multiple interpretations)?
- [ ] Should system attempt to fix unsolvable problems, or reject them?

**Recommendation**:
- Review Agent checks logical consistency only (doesn't solve)
- If Mathematical Validity score < 2.0, flag as potentially unsolvable
- Revise Agent attempts fix; if score remains < 2.0 after 2 iterations, reject with explanation

**New Requirements**:
- **FR-063**: Review Agent MUST check for logical contradictions without solving
- **FR-064**: System MUST reject problems with Mathematical Validity < 2.0 after 2 revise iterations
- **FR-065**: System MUST provide specific error explanation when rejecting unsolvable problems

---

#### Q2.5: Rephrase Dimension Selection
**Current Spec (FR-005)**: "Must apply ≥3 escalation dimensions"

**Ambiguity**: Who/what chooses which 3+ dimensions?
- Rephrase Agent decides autonomously?
- Random selection?
- Based on problem domain/type?
- User specifies (only for P3)?

**Why This Matters**:
- Different dimensions suit different problem types
- "Optimization Extension" doesn't make sense for basic arithmetic
- Consistency across similar problems

**Clarification Needed**:
- [ ] Should dimension selection be intelligent (based on problem type)?
- [ ] Or random/fixed default set?
- [ ] Can system auto-adjust if dimensions don't fit?

**Recommendation**:
- **MVP**: Fixed default set (Multi-stage, Cross-domain, Real-world) for all problems
- **P2**: Smart selection based on domain/difficulty
- **P3**: User-configurable (already in spec)

**New Requirements**:
- **FR-066**: System MUST use default escalation dimensions: Multi-stage Transformation, Cross-domain Integration, Real-world Parameterization (MVP)
- **FR-067**: System SHOULD intelligently select dimensions based on problem domain and difficulty (P2)

---

#### Q2.6: Iteration Timeout/Failure Handling
**Current Spec (FR-019)**: "Maximum 5 iterations"
**Current Spec (Edge Case)**: "Flag as 'Unable to achieve quality threshold'"

**Ambiguity**: What exactly happens when max iterations exceeded?
- Return best attempt even if score < threshold?
- Ask user if they want to continue?
- Provide partial result + error?
- Charge user anyway?

**Clarification Needed**:
- [ ] Should system return best attempt (highest score achieved)?
- [ ] Or completely fail and return nothing?
- [ ] Notify user proactively during iterations?
- [ ] Refund/credit if failure?

**Recommendation**:
- Return best attempt (highest score achieved) with warning
- Mark session as "PARTIAL_SUCCESS" (new status)
- Still generate solution for best attempt if score ≥ 4.0 (relaxed threshold)
- Provide detailed diagnostic report to help user understand why threshold not reached

**New Requirements**:
- **FR-068**: System MUST return best attempt when max iterations exceeded (if score ≥ 4.0)
- **FR-069**: System MUST mark session as "PARTIAL_SUCCESS" when threshold not fully reached
- **FR-070**: System MUST provide diagnostic report explaining why threshold not achieved

---

### Category 3: Performance and Scalability

#### Q2.7: Concurrent Processing
**Current Spec (SC-005)**: "Process single problem in <60 seconds on average"

**Ambiguity**: What about multiple users/problems simultaneously?
- How many concurrent problems can system handle?
- Queue management strategy?
- Priority for different user types (free vs. paid)?

**Clarification Needed**:
- [ ] Expected concurrent user load? (10? 100? 1000?)
- [ ] Should system queue problems or reject when overloaded?
- [ ] Need load balancing across multiple workers?

**Recommendation**:
- **MVP**: Single-threaded, queue-based (10-20 concurrent)
- **Production**: Distributed task queue (Celery/RQ) + auto-scaling workers
- Implement rate limiting (e.g., 10 problems/hour per user)

**New Requirements**:
- **FR-071**: System MUST handle ≥10 concurrent problem processing requests
- **FR-072**: System SHOULD implement queue-based processing for requests exceeding capacity
- **FR-073**: System SHOULD implement rate limiting (10 problems/hour per user for MVP)

---

#### Q2.8: Caching and Duplicate Detection
**Current Spec**: Not mentioned

**Ambiguity**: Should system cache or detect duplicate problems?
- If 100 students upload same textbook problem, process 100 times?
- Cache rephrased problems for common seeds?
- Detect similar (not identical) problems?

**Why This Matters**: Cost savings and performance

**Clarification Needed**:
- [ ] Should system detect exact duplicates and reuse results?
- [ ] Should system detect similar problems (fuzzy matching)?
- [ ] Cache rephrased problems? For how long?

**Recommendation**:
- **MVP**: Exact duplicate detection (hash-based), cache for 24 hours
- **P2**: Fuzzy matching (semantic similarity > 95%) with cache
- User still sees "processing" UX but results instant from cache

**New Requirements**:
- **FR-074**: System SHOULD detect exact duplicate problems (hash-based)
- **FR-075**: System SHOULD cache rephrased problems and solutions for 24 hours
- **FR-076**: System MAY detect semantically similar problems (P2)

---

### Category 4: User Experience and Feedback

#### Q2.9: Real-Time Progress Updates
**Current Spec**: Not mentioned

**Ambiguity**: Should users see progress during processing?
- Silent processing with final result?
- Show "Rephrasing... Reviewing... Revising..." stages?
- Show intermediate scores?

**Why This Matters**: 60 seconds is long for users without feedback

**Clarification Needed**:
- [ ] Should system provide real-time updates?
- [ ] Should users see intermediate quality scores?
- [ ] Should users be able to cancel processing?

**Recommendation**:
- Show stage-by-stage progress: "Rephrasing (15s)... Reviewing (10s)... Revising (20s)... Solving (15s)"
- Show iteration count if multiple revisions needed
- Allow cancellation (refund credits)

**New Requirements**:
- **FR-077**: System SHOULD provide real-time progress updates showing current agent and elapsed time
- **FR-078**: System SHOULD display iteration count during review-revise loop
- **FR-079**: System MAY allow users to cancel processing mid-workflow

---

#### Q2.10: Result Presentation
**Current Spec**: Not explicitly defined

**Ambiguity**: How are results shown to users?
- Side-by-side (original vs rephrased)?
- Sequential (original → rephrased → solution)?
- Show all intermediate revisions?
- Highlighting changes?

**Clarification Needed**:
- [ ] Should users see original and rephrased problems together?
- [ ] Should users see why specific changes were made (review suggestions)?
- [ ] Should users see solution for original problem too?

**Recommendation**:
- Show three-column view:
  1. **Original Problem** (user uploaded)
  2. **Rephrased Problem** (final, with quality score)
  3. **Solution** (step-by-step for rephrased problem)
- Expandable section showing: iteration history, review scores, suggestions applied
- Optional: Solution for original problem (helps students see connection)

**New Requirements**:
- **FR-080**: System MUST display original problem, final rephrased problem, and solution side-by-side
- **FR-081**: System SHOULD provide expandable section showing iteration history and applied suggestions
- **FR-082**: System MAY generate solution for original problem as well (P2)

---

#### Q2.11: Error Messages and Guidance
**Current Spec**: "Request clarification" for vague problems (Edge Case)

**Ambiguity**: What level of guidance should system provide?
- Generic error: "Problem not clear"?
- Specific guidance: "Missing information: What is the perimeter?"?
- Suggestions: "Try adding 'Find x' to make question clearer"?

**Clarification Needed**:
- [ ] Should system provide specific guidance on how to fix problems?
- [ ] Should system attempt partial processing and show what it understood?
- [ ] Examples of good problems for user education?

**Recommendation**:
- Specific, actionable error messages
- Show what system understood vs. what's missing
- Provide examples of well-formed problems
- "Help" button with tips for better problem uploads

**New Requirements**:
- **FR-083**: System MUST provide specific, actionable error messages
- **FR-084**: System SHOULD show partial understanding when problem is incomplete
- **FR-085**: System SHOULD provide examples and guidance for well-formed problems

---

## 📋 Summary of Clarification Needs

### Critical (Blocking MVP)

1. **Photo Upload Decisions** (Q1.1 - Q1.7):
   - [ ] OCR/VLM choice and integration
   - [ ] Image quality handling strategy
   - [ ] User confirmation workflow
   - [ ] Diagram handling approach

2. **Input Format** (Q2.1):
   - [ ] LaTeX support required?
   - [ ] Unicode math symbols handling?

3. **Language Support** (Q2.3):
   - [ ] English-only MVP acceptable?
   - [ ] Chinese support required for MVP?

### Important (Affects UX/Cost)

4. **Problem Length** (Q2.2):
   - [ ] Acceptable min/max lengths?

5. **Failure Handling** (Q2.6):
   - [ ] Return partial results or fail completely?

6. **Real-Time Feedback** (Q2.9):
   - [ ] Progress updates required?

### Nice-to-Have (Can defer)

7. **Caching** (Q2.8):
   - [ ] Duplicate detection priority?

8. **Result Presentation** (Q2.10):
   - [ ] Preferred UI layout?

---

## 🎯 Recommended Decisions (If No User Input)

For unblocking development, here are recommended defaults:

| Question | Recommended Decision | Rationale |
|----------|---------------------|-----------|
| **Q1.2** (OCR Method) | GPT-4V / Claude-3 Vision | Best handwriting support, worth cost |
| **Q1.3** (Quality) | Preprocessing + conditional re-request | Balance UX and quality |
| **Q1.4** (Multi-problem) | One problem per image (MVP) | Simplest, clear UX |
| **Q1.5** (Diagrams) | VLM text description (MVP) | Feasible without complex UI |
| **Q1.6** (Storage) | 30-day retention + PII redaction | Privacy-compliant, debug-friendly |
| **Q1.7** (Workflow) | User confirmation of extracted text | Catches errors early |
| **Q2.1** (Format) | Support LaTeX + Unicode | Comprehensive, modern |
| **Q2.2** (Length) | 20-2000 characters | Reasonable bounds |
| **Q2.3** (Language) | English MVP, Chinese P2 | Fastest to market |
| **Q2.6** (Failure) | Return best attempt (score ≥4.0) | User gets something useful |
| **Q2.9** (Progress) | Stage-by-stage updates | Better UX for 60s wait |

---

## 📝 Next Steps

1. **User Review**: Please review all questions and provide decisions
2. **Priority Focus**: Especially Q1.1-Q1.7 (Photo Upload - new feature)
3. **Update Spec**: Based on decisions, update `spec.md` with:
   - New User Story 0 (Photo Upload)
   - New FR-033 through FR-085
   - Updated data model
   - Updated architecture diagrams

4. **Update Plan**: Modify `plan.md` with:
   - New components (Image Service, OCR Service)
   - Updated tech stack (VLM API, image storage)
   - Cost estimates

5. **Update Contracts**: Add new contracts:
   - `image-extraction-agent.md` (OCR/VLM service)
   - Update existing contracts to handle diagram descriptions

---

**Questions for User**:

1. **Most Critical**: Which OCR/VLM approach for photo upload? (Q1.2)
2. **UX Critical**: Should users confirm extracted text? (Q1.7)
3. **Language**: English-only MVP or must support Chinese? (Q2.3)
4. **Scope**: Are diagrams/figures in scope for MVP? (Q1.5)
5. **Budget**: OK with ~$0.05 per photo processing cost? (see Q1.2 cost analysis)

Please provide guidance on these 5 key questions to proceed with specification updates.
