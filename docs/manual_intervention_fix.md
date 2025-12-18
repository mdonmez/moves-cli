# Manual Intervention & Synchronization Strategy

**Date:** 2025-12-19
**Status:** Approved Design
**Context:** Presentation Control System

## 1. Problem Definition

When a supervisor manually intervenes (e.g., changes slides via keyboard), the system's Speech-to-Text (STT) buffer often retains words from the _previous_ slide. This "stale buffer" causes the system to immediately issue a navigation command back to the old slide, fighting the supervisor's action.

### Scenario

1.  **Context:** Speaker is on Slide 14.
2.  **Action:** Supervisor manually moves to Slide 12 (e.g., to answer a question about a past topic).
3.  **System State:** `current_section` updates to 12.
4.  **Buffer State:** STT buffer still contains ~10 words from Slide 14.
5.  **Conflict:**
    - `CandidateChunkGenerator` creates candidates around Slide 12.
    - However, due to transition chunks (e.g., chunks spanning 12-14), the stale words from Slide 14 still trigger a high similarity score for Slide 14.
    - **Result:** System navigates back to Slide 14, overriding the supervisor.

## 2. Root Cause Analysis

- **Stale Buffer:** The STT buffer is a sliding window of the last 12 words. It takes time for new context to flush out old words.
- **Candidate Overlap:** While `CandidateChunkGenerator` correctly filters out distant slides (e.g., Slide 14 pure chunks are not candidates when on Slide 11), "transition chunks" spanning slides (e.g., 12-13, 13-14) can still bridge the gap and cause false positives.
- **Autonomous Authority:** The system currently assumes its calculated top match is always the "truth," ignoring the signal inherent in the supervisor's manual override.

## 3. Discarded Solutions

The following solutions were considered and rejected:

- **Ghost Mode / Disabling System:** Disabling the system for X seconds. (Rejected: Arbitrary timeouts are unreliable).
- **Buffer Clearing:** Clearing the STT buffer on intervention. (Rejected: Causes recalibration delay and loss of potentially valid context).
- **Window Expansion:** Expanding search window after intervention. (Rejected: Not necessary because the window naturally follows the `current_section`).
- **Top-N Consistency:** Analyzing gap between Top 1 and Top 2 results. (Rejected: Ineffective because the false positive (Slide 14) is often dominant in the results).

## 4. The Solution: "Sync Lock" (Synchronization Lock)

### Core Principle

**"If the supervisor moves to a location, the system must not navigate elsewhere until it confirms that location via audio."**

The system and supervisor are collaborators. When the supervisor intervenes, the system enters a "verify" mode rather than a "drive" mode.

### Mechanism

1.  **Trigger:** Manual intervention (keyboard/API) updates `current_section`.
2.  **Lock Activation:** System enters `SYNC_LOCKED` state.
    - `target_lock_section` = New `current_section` (e.g., Slide 12).
3.  **Navigation Logic (in `_navigator_task`):**
    - Calculate similarity scores as usual.
    - Identify `top_result_section`.
    - **CHECK:**
      - IF `top_result_section` == `target_lock_section` (or very close/adjacent):
        - **UNLOCK.** (Audio confirms we are indeed at Slide 12).
        - Resume normal autonomous navigation.
      - IF `top_result_section` != `target_lock_section`:
        - **WAIT.** (Do NOT navigate).
        - Audio indicates we are at Slide 14, but Supervisor put us at Slide 12. Trust Supervisor. Wait for audio to catch up.

### Edge Cases & Handling

#### A. "Excited Speaker" (Jump from 12 to 20)

- **Scenario:** Speaker jumps to topic on Slide 20. Supervisor manually goes to Slide 20.
- **Handling:**
  - `current_section` becomes 20.
  - `CandidateChunkGenerator` generates candidates around 20 ([18...22]).
  - Speaker reads Slide 20.
  - System matches audio to Slide 20 candidates.
  - Result: `top_result` (20) == `lock` (20). Unlock & Resume. **Works perfectly.**

#### B. "Supervisor Mistake" (Wrong Slide)

- **Scenario:** Speaker on 14. Supervisor accidentally clicks 11.
- **Handling:**
  - System sees audio match for 14.
  - Lock is for 11.
  - Mismatch -> System WAITS.
  - **Outcome:** System does NOT fight the supervisor. It allows the supervisor to realize the mistake and correct it (click 14).
  - **Philosophy:** "Collaboration." False positives (fighting the user) are worse than false negatives (waiting).

#### C. "Deadlock" Prevention

- **Risk:** What if the system _never_ gets a good match for Slice 12 (e.g., very short slide, noise)?
- **Mitigation:** Implement a `LOCK_TIMEOUT` (e.g., 10 seconds). If lock isn't cleared by audio confirmation within X seconds, force unlock or clear buffer to prevent permanent paralysis.

## 5. Implementation Plan

1.  **Class Update:** Add `self.sync_lock_active: bool` and `self.sync_lock_target: int` to `PresentationController`.
2.  **Input Handler:** When processing manual keys (Left/Right), set `sync_lock_active = True`.
3.  **Navigator Task:**
    - Inside the decision loop, check `if self.sync_lock_active`.
    - Apply logic: `if top_match != current_section: continue (WAIT)`.
    - `else: self.sync_lock_active = False`.

## 6. Verification

Use the existing reproduction scripts (`tests/test_12_14_problem.py`) to verify that with this logic applied, the system returns `WAIT` instead of `NAVIGATE -> 14` in the conflict scenario.
