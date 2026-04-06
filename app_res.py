import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Teacher Observation Checklist",
    page_icon="📋",
    layout="wide"
)

# ─────────────────────────────────────────────
# CREDENTIALS  — change passwords as needed
# ─────────────────────────────────────────────
def _h(p): return hashlib.sha256(p.encode()).hexdigest()

CREDENTIALS = {
    "admin":   {"password_hash": _h("admin@123"),   "role": "admin"},
    "teacher": {"password_hash": _h("teacher@123"), "role": "user"},
}

# ─────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────
def login(username, password):
    user = CREDENTIALS.get(username)
    if user and user["password_hash"] == _h(password):
        st.session_state["logged_in"] = True
        st.session_state["username"]  = username
        st.session_state["role"]      = user["role"]
        return True
    return False

def logout():
    for k in ["logged_in", "username", "role"]:
        st.session_state.pop(k, None)

def is_logged_in(): return st.session_state.get("logged_in", False)
def is_admin():     return st.session_state.get("role") == "admin"

# ─────────────────────────────────────────────
# DIFFICULTY / COLOUR CONFIG
# ─────────────────────────────────────────────
LEVEL_INFO = {
    "A": ("No Difficulty",       "85% – 100%"),
    "B": ("Mild Difficulty",     "70% – 84%"),
    "C": ("Moderate Difficulty", "50% – 69%"),
    "D": ("Severe Difficulty",   "0% – 49%"),
}
LEVEL_COLORS = {
    "A": "#2e7d32",
    "B": "#f57c00",
    "C": "#c62828",
    "D": "#6a1b9a",
}

ALL_SUBJECTS = ["English", "EVS", "Kannada", "Math", "Science", "Social Studies", "Art / PE / Other"]

SUBJECT_QUESTIONS = {
    "EVS":     {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57},
    "Kannada": {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,49,50,51,52,53,54,55,56,57,58,59,60,61},
    "English": {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59},
    "Math":    {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56},
}
DEFAULT_QUESTIONS = set(range(1, 78)) - {50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65}

CHECKLIST = {
    "DOMAIN 1: ATTENTION & EXECUTIVE FUNCTION": {
        "SUSTAINED ATTENTION": [
            (1, "Sustains attention during tasks", {
                "A": "Sustains attention throughout the task without shifting attention.",
                "B": "Sustains attention with 1-2 brief pauses; resumes independently.",
                "C": "Sustains attention with multiple pauses (>=3); resumes with 1-2 prompts.",
                "D": "Sustains attention only for short segments; requires repeated prompts (>=3).",
            }),
        ],
        "SELECTIVE ATTENTION": [
            (2, "Maintains focus despite distractions", {
                "A": "Maintains focus on the task despite distractions; no shift or one brief shift; returns immediately.",
                "B": "Maintains focus with 1-2 brief shifts; returns independently.",
                "C": "Maintains focus with multiple shifts (>=3); returns with 1-3 prompts.",
                "D": "Shows frequent shifting; requires repeated prompts (>=3) to return.",
            }),
        ],
        "ATTENTION SHIFTING": [
            (3, "Transition between activities", {
                "A": "Transitions independently within the expected classroom cue; begins new task without prompts.",
                "B": "Transitions with one prompt (verbal or gestural); begins new task.",
                "C": "Transitions with 2-3 prompts; shows delay in initiating or completing the shift.",
                "D": "Requires continuous prompts (>=3) or adult assistance to transition.",
            }),
        ],
        "WORKING MEMORY": [
            (4, "Follows instructions (single-step)", {
                "A": "Follows 1-step instructions independently without repetition.",
                "B": "Follows 1-step instructions with 1 repetition.",
                "C": "Follows 1-step instructions with 2-3 repetitions; may require prompts.",
                "D": "Follows 1-step instructions only with repeated repetitions (>=3) and adult support.",
            }),
            (5, "Follows instructions (multi-step)", {
                "A": "Follows 2-3 step instructions independently; completes all steps in sequence.",
                "B": "Follows 2-3 step instructions with 1-2 prompts; completes all steps.",
                "C": "Follows 2-3 step instructions with multiple prompts (>=3); misses or skips steps.",
                "D": "Follows 2-3 step instructions only with continuous prompts; does not complete most steps.",
            }),
        ],
        "TASK EXECUTION": [
            (6, "Completes tasks within time", {
                "A": "Completes the task independently within the allotted time (0 prompts).",
                "B": "Completes within the allotted time with 1-2 prompts/repetitions.",
                "C": "Completes with >=3 prompts/repetitions and/or exceeds the allotted time.",
                "D": "Requires continuous prompting and adult support; unable to complete the task.",
            }),
        ],
    },
    "DOMAIN 2: VISUO-MOTOR INTEGRATION": {
        "VISUAL PERCEPTION": [
            (7, "Colour identification", {
                "A": "Identifies and names all common colours independently across contexts.",
                "B": "Identifies and names common colours with 1-2 prompts.",
                "C": "Identifies and names colours with multiple prompts (>=3); misidentifies.",
                "D": "Identifies colours only with continuous prompts; does not identify correctly.",
            }),
            (8, "Identification of body parts", {
                "A": "Identifies all body parts independently.",
                "B": "Identifies body parts with 1-2 prompts (verbal or gestural).",
                "C": "Identifies body parts with multiple prompts (>=3); misses several.",
                "D": "Identifies body parts only with continuous prompts; does not identify independently.",
            }),
            (9, "Visual discrimination of similar symbols (letters, numbers, patterns)", {
                "A": "Differentiates visually similar symbols (e.g., b/d, p/q, 6/9) independently.",
                "B": "Differentiates with 1-2 prompts; may make 1-2 errors.",
                "C": "Differentiates with multiple prompts (>=3); makes errors in several items.",
                "D": "Differentiates only with continuous prompts; does not differentiate most correctly.",
            }),
        ],
        "VISUO-MOTOR INTEGRATION": [
            (10, "Eye-hand coordination", {
                "A": "Performs tasks requiring eye-hand coordination independently with accurate control.",
                "B": "Performs tasks with 1-2 prompts; shows 1-2 errors in control or coordination.",
                "C": "Performs tasks with multiple prompts (>=3); shows errors in several attempts.",
                "D": "Performs tasks only with continuous prompts; does not complete accurately.",
            }),
        ],
        "MOTOR CONTROL (WRITING READINESS)": [
            (11, "Spacing and alignment", {
                "A": "Maintains appropriate spacing and correct alignment independently.",
                "B": "Maintains spacing and alignment with 1-2 prompts; 1-2 errors.",
                "C": "Maintains spacing and alignment with multiple prompts (>=3); errors in several instances.",
                "D": "Maintains spacing/alignment only with continuous prompts; does not maintain in most instances.",
            }),
            (12, "Sense of direction (left-right, top-bottom)", {
                "A": "Follows directional concepts independently; no errors.",
                "B": "Follows directional concepts with 1-2 prompts; 1-2 errors.",
                "C": "Follows directional concepts with multiple prompts (>=3); >=3 errors.",
                "D": "Follows directions only with continuous prompts; does not follow correctly.",
            }),
            (13, "Letter formation", {
                "A": "Forms letters correctly as per grade expectations independently; no errors.",
                "B": "Forms letters with 1-2 prompts; 1-2 formation errors.",
                "C": "Forms letters with multiple prompts (>=3); >=3 formation errors.",
                "D": "Attempts letter formation only with continuous prompts; does not form most letters correctly.",
            }),
        ],
        "TASK APPLICATION": [
            (14, "Copying from board", {
                "A": "Copies all content accurately with no omissions/substitutions/sequence errors.",
                "B": "Copies content with 1-2 prompts; 1-2 errors.",
                "C": "Copies content with multiple prompts (>=3); >=3 errors; some content incomplete.",
                "D": "Attempts to copy only with continuous prompts; does not complete the task.",
            }),
            (15, "Fine motor task completion (cutting, colouring)", {
                "A": "Completes fine-motor tasks within boundaries independently; no errors.",
                "B": "Completes tasks with 1-2 prompts; goes outside boundaries 1-2 times.",
                "C": "Completes tasks with multiple prompts (>=3); goes outside boundaries >=3 times.",
                "D": "Requires continuous prompts; does not complete the task.",
            }),
            (16, "Visual Memory", {
                "A": "Recalls visual information independently; no errors.",
                "B": "Recalls visual information with 1-2 prompts; 1-2 errors.",
                "C": "Recalls visual information with multiple prompts (>=3); >=3 errors or partial recall.",
                "D": "Requires continuous prompts; does not recall information correctly.",
            }),
        ],
    },
    "DOMAIN 3: LANGUAGE & COMMUNICATION": {
        "COMPREHENSION": [
            (17, "Comprehending oral instructions", {
                "A": "Follows grade-appropriate oral instructions accurately on first presentation.",
                "B": "Follows instructions with 1 repetition or clarification; completes task correctly.",
                "C": "Follows only part of the instruction; requires repeated repetition/simplification.",
                "D": "Does not follow most academic instructions even after repetition and prompts.",
            }),
            (18, "Listening to the graded passage and comprehending", {
                "A": "Answers questions independently; no errors.",
                "B": "Answers questions with 1-2 prompts; responses are correct.",
                "C": "Answers questions with multiple prompts (>=3); >=3 errors or incomplete.",
                "D": "Answers only with continuous prompts; does not answer correctly.",
            }),
        ],
        "EXPRESSION": [
            (19, "Functional communication skill", {
                "A": "Expresses personal needs independently; message is complete and appropriate.",
                "B": "Expresses personal needs with 1-2 prompts; message is complete with 1-2 errors.",
                "C": "Expresses personal needs with multiple prompts (>=3); message is incomplete.",
                "D": "Expresses needs only with continuous prompts; does not express clearly.",
            }),
            (20, "States personal information accurately", {
                "A": "States personal details independently; no errors.",
                "B": "States personal details with 1-2 prompts; 1-2 errors.",
                "C": "States personal details with multiple prompts (>=3); >=3 errors or incomplete.",
                "D": "States details only with continuous prompts; does not state correctly.",
            }),
        ],
        "SENTENCE FORMATION (STRUCTURE)": [
            (21, "Usage of complete sentences to respond", {
                "A": "Uses complete and grammatically correct sentences independently.",
                "B": "Uses complete sentences with 1-2 prompts; 1-2 grammatical errors.",
                "C": "Uses incomplete or fragmented sentences with multiple prompts (>=3).",
                "D": "Uses single words or short phrases only; requires continuous prompts.",
            }),
        ],
        "FLUENCY (FLOW)": [
            (22, "Verbal fluency", {
                "A": "Speaks in connected sentences independently; no pauses interrupting flow.",
                "B": "Speaks with 1-2 prompts; 1-2 pauses or word-finding difficulties.",
                "C": "Speaks with multiple prompts (>=3); >=3 pauses or breaks in flow.",
                "D": "Produces single words or fragmented speech; requires continuous prompts.",
            }),
            (23, "Social communication - Initiates interaction with peers", {
                "A": "Initiates interaction with peers independently.",
                "B": "Initiates interaction with 1-2 prompts.",
                "C": "Initiates interaction with multiple prompts (>=3); may be delayed or incomplete.",
                "D": "Does not initiate interaction; requires continuous prompts.",
            }),
            (24, "Social communication - Responds to interaction appropriately", {
                "A": "Responds to interaction independently; response is appropriate.",
                "B": "Responds to interaction with 1-2 prompts; response is appropriate.",
                "C": "Responds with multiple prompts (>=3); may be delayed or incomplete.",
                "D": "Does not respond; requires continuous prompts.",
            }),
        ],
        "HIGHER ORDER EXPRESSION (NARRATION & IDEAS)": [
            (25, "Narrates instructions or academic concepts", {
                "A": "Explains/retells independently; information is complete and accurate.",
                "B": "Explains/retells with 1-2 prompts; 1-2 errors or omissions.",
                "C": "Explains/retells with multiple prompts (>=3); information is incomplete.",
                "D": "Explains/retells only with continuous prompts; does not provide complete information.",
            }),
        ],
    },
    "DOMAIN 4: READING": {
        "PRE-READING": [
            (26, "Phonemic Awareness", {
                "A": "Performs phonological tasks independently; no errors.",
                "B": "Performs with 1-2 prompts; 1-2 errors.",
                "C": "Performs with multiple prompts (>=3); >=3 errors or incomplete.",
                "D": "Performs only with continuous prompts; does not perform correctly.",
            }),
            (27, "Letter-sound recognition", {
                "A": "Identifies letter-sound correspondences independently; no errors.",
                "B": "Identifies with 1-2 prompts; 1-2 errors.",
                "C": "Identifies with multiple prompts (>=3); >=3 errors.",
                "D": "Identifies only with continuous prompts; does not identify correctly.",
            }),
        ],
        "DECODING": [
            (28, "Blending of sounds", {
                "A": "Blends sounds accurately and independently; no errors.",
                "B": "Blends with 1-2 prompts; 1-2 errors.",
                "C": "Blends with >=3 prompts; >=3 errors or inconsistent responses.",
                "D": "Unable to blend sounds even with continuous prompts.",
            }),
            (29, "Strategy use for unfamiliar words", {
                "A": "Applies decoding strategies (phonics, syllabification) independently; no errors.",
                "B": "Applies strategies with 1-2 prompts; 1-2 errors.",
                "C": "Applies strategies with >=3 prompts; >=3 errors or inconsistent application.",
                "D": "Does not apply decoding strategies even with continuous prompts.",
            }),
        ],
        "WORD RECOGNITION": [
            (30, "Recognition of sight words and common words", {
                "A": "Recognizes sight and common words independently; no errors.",
                "B": "Recognizes words with 1-2 prompts; 1-2 errors.",
                "C": "Recognizes words with multiple prompts (>=3); >=3 errors.",
                "D": "Recognizes words only with continuous prompts.",
            }),
            (31, "Substitution or guessing of words", {
                "A": "Reads words independently; no substitutions or guessing.",
                "B": "Reads with 1-2 prompts; 1-2 substitutions or guesses.",
                "C": "Reads with multiple prompts (>=3); >=3 substitutions or guesses.",
                "D": "Reads only with continuous prompts; substitutes or guesses most words.",
            }),
            (32, "Reversals (b/d, u/n, p/q etc.)", {
                "A": "Uses correct orientation independently; no reversals.",
                "B": "Shows 1-2 reversals; self-corrects with 1-2 prompts.",
                "C": "Shows >=3 reversals; requires multiple prompts (>=3) to correct.",
                "D": "Shows reversals even with continuous prompts; does not correct.",
            }),
            (33, "Transposition while reading", {
                "A": "Reads independently; no transposition errors.",
                "B": "Reads with 1-2 prompts; 1-2 transposition errors.",
                "C": "Reads with multiple prompts (>=3); >=3 transposition errors.",
                "D": "Reads only with continuous prompts; transposition errors persist.",
            }),
        ],
        "FLUENCY": [
            (34, "Tracking words appropriately while reading", {
                "A": "Tracks words independently; no loss of place.",
                "B": "Tracks words with 1-2 prompts; 1-2 instances of losing place.",
                "C": "Tracks words with multiple prompts (>=3); >=3 instances of losing place.",
                "D": "Tracks only with continuous prompts; does not track accurately.",
            }),
            (35, "Reading a sentence/graded passage with intonation", {
                "A": "Reads with appropriate pauses and intonation independently.",
                "B": "Reads with 1-2 prompts; 1-2 errors in pauses or intonation.",
                "C": "Reads with multiple prompts (>=3); limited variation in voice.",
                "D": "Reads only with continuous prompts; does not use pauses/intonation appropriately.",
            }),
        ],
        "COMPREHENSION": [
            (36, "Reading graded passage and comprehension", {
                "A": "Reads the passage independently; answers questions correctly.",
                "B": "Reads with 1-2 prompts; answers with 1-2 errors.",
                "C": "Reads with multiple prompts (>=3); >=3 errors or incomplete responses.",
                "D": "Reads only with continuous prompts; does not answer questions correctly.",
            }),
        ],
    },
    "DOMAIN 5: SPELLING": {
        "PHONOLOGICAL ENCODING": [
            (37, "Letter-sound association and phonological encoding in spelling", {
                "A": "Applies letter-sound correspondence independently; no errors.",
                "B": "Applies with 1-2 prompts; 1-2 errors in sound-letter mapping.",
                "C": "Applies with multiple prompts (>=3); >=3 errors or incomplete spelling.",
                "D": "Applies only with continuous prompts; does not apply correctly.",
            }),
        ],
        "WORD-LEVEL SPELLING": [
            (38, "Accuracy and consistency of spelling", {
                "A": "Spells words independently; no errors.",
                "B": "Spells with 1-2 prompts; 1-2 errors.",
                "C": "Spells with multiple prompts (>=3); >=3 errors or incomplete spelling.",
                "D": "Spells only with continuous prompts; does not spell correctly.",
            }),
        ],
        "STRATEGY USE": [
            (39, "Strategy use to spell a word", {
                "A": "Applies spelling strategies (phonics, chunking, rules) independently; no errors.",
                "B": "Applies strategies with 1-2 prompts; 1-2 errors.",
                "C": "Applies strategies with multiple prompts (>=3); >=3 errors or inconsistent use.",
                "D": "Applies strategies only with continuous prompts; does not apply correctly.",
            }),
        ],
        "SELF CORRECTION": [
            (40, "Self-correction using feedback", {
                "A": "Corrects spelling errors independently; all errors corrected.",
                "B": "Corrects errors with 1-2 prompts; 1-2 errors remain.",
                "C": "Corrects errors with multiple prompts (>=3); >=3 errors remain.",
                "D": "Corrects errors only with continuous prompts; does not correct.",
            }),
            (41, "Transposition of words (e.g., 'was' written as 'saw')", {
                "A": "Spells independently; no transposition errors.",
                "B": "Spells with 1-2 prompts; 1-2 transposition errors.",
                "C": "Spells with multiple prompts (>=3); >=3 transposition errors.",
                "D": "Spells only with continuous prompts; transposition errors persist.",
            }),
        ],
    },
    "DOMAIN 6: WRITING & WRITTEN EXPRESSION": {
        "FINE MOTOR CONTROL": [
            (42, "Pencil Grip", {
                "A": "Uses a functional pencil grip independently; no adjustments needed.",
                "B": "Uses grip with 1-2 prompts; 1-2 adjustments needed.",
                "C": "Uses grip with multiple prompts (>=3); grip affects control in >=3 instances.",
                "D": "Uses grip only with continuous prompts; does not maintain functional grip.",
            }),
            (43, "Letter formation (mixing of cases, improper formation etc.)", {
                "A": "Forms letters independently; no errors.",
                "B": "Forms letters with 1-2 prompts; 1-2 formation errors.",
                "C": "Forms letters with multiple prompts (>=3); >=3 formation errors.",
                "D": "Attempts formation only with continuous prompts; does not form most correctly.",
            }),
            (44, "Writing pressure", {
                "A": "Maintains writing pressure independently; no variation.",
                "B": "Maintains writing pressure with 1-2 prompts; 1-2 instances of light or heavy pressure.",
                "C": "Maintains writing pressure with multiple prompts (>=3); >=3 instances.",
                "D": "Maintains writing pressure only with continuous prompts; pressure is not controlled.",
            }),
        ],
        "WRITTEN CONTENT": [
            (45, "Simple Sentence formation", {
                "A": "Writes sentences independently; no grammatical or structural errors.",
                "B": "Writes sentences with 1-2 prompts; 1-2 errors in grammar or structure.",
                "C": "Writes sentences with multiple prompts (>=3); >=3 errors or incomplete sentences.",
                "D": "Writes sentences only with continuous prompts; does not form correct sentences.",
            }),
            (46, "Ideation or flow of thoughts in writing", {
                "A": "Writes ideas independently; logically connected and sequenced.",
                "B": "Writes ideas with 1-2 prompts; 1-2 gaps in sequence or connection.",
                "C": "Writes ideas with multiple prompts (>=3); ideas are loosely connected or incomplete.",
                "D": "Writes ideas only with continuous prompts; does not connect ideas.",
            }),
            (47, "Use of vocabulary in writing", {
                "A": "Uses vocabulary independently; no repetition errors.",
                "B": "Uses vocabulary with 1-2 prompts; 1-2 repetitions or limited word choice.",
                "C": "Uses vocabulary with multiple prompts (>=3); >=3 repetitions or limited use.",
                "D": "Uses vocabulary only with continuous prompts; does not use appropriate words.",
            }),
            (48, "Use of letter case and punctuation", {
                "A": "Uses capitalization and punctuation independently; no errors.",
                "B": "Uses with 1-2 prompts; 1-2 errors.",
                "C": "Uses with multiple prompts (>=3); >=3 errors.",
                "D": "Uses only with continuous prompts; does not use correctly.",
            }),
            (49, "Completion of writing tasks", {
                "A": "Completes writing tasks independently.",
                "B": "Completes with 1-2 prompts.",
                "C": "Partially completes with multiple prompts (>=3).",
                "D": "Completes only with continuous prompts; does not complete the task.",
            }),
        ],
    },
    "DOMAIN 7: MATHEMATICS": {
        "NUMBER SENSE": [
            (50, "Counting of numbers", {
                "A": "Counts independently; no errors.",
                "B": "Counts with 1-2 prompts; 1-2 errors or skips.",
                "C": "Counts with multiple prompts (>=3); >=3 errors or skips.",
                "D": "Counts only with continuous prompts; does not count correctly.",
            }),
            (51, "Number recognition", {
                "A": "Recognizes numbers independently; no errors.",
                "B": "Recognizes with 1-2 prompts; 1-2 errors.",
                "C": "Recognizes with multiple prompts (>=3); >=3 errors.",
                "D": "Recognizes only with continuous prompts; does not recognize correctly.",
            }),
            (52, "Writing numbers in sequences", {
                "A": "Writes numbers in sequence independently; no errors.",
                "B": "Writes with 1-2 prompts; 1-2 sequencing errors.",
                "C": "Writes with multiple prompts (>=3); >=3 errors or incomplete sequence.",
                "D": "Writes only with continuous prompts; does not write in sequence correctly.",
            }),
            (53, "Number Name", {
                "A": "Writes number names independently; no errors.",
                "B": "Writes with 1-2 prompts; 1-2 errors.",
                "C": "Writes with multiple prompts (>=3); >=3 errors or incomplete.",
                "D": "Writes only with continuous prompts; does not write correctly.",
            }),
        ],
        "NUMBER RELATIONSHIPS": [
            (54, "Comparison of numbers", {
                "A": "Compares numbers using symbols (>, <, =) independently; no errors.",
                "B": "Compares with 1-2 prompts; 1-2 errors.",
                "C": "Compares with multiple prompts (>=3); >=3 errors.",
                "D": "Compares only with continuous prompts; does not compare correctly.",
            }),
            (55, "Arranging numbers in order (as per grade level)", {
                "A": "Arranges numbers (ascending/descending) independently; no errors.",
                "B": "Arranges with 1-2 prompts; 1-2 errors.",
                "C": "Arranges with multiple prompts (>=3); >=3 errors or incomplete order.",
                "D": "Arranges only with continuous prompts; does not arrange correctly.",
            }),
        ],
        "OPERATIONS": [
            (56, "Recognition/use of symbols", {
                "A": "Identifies and uses symbols (+, -, x, divide, =, >, <) independently; no errors.",
                "B": "Identifies/uses with 1-2 prompts; 1-2 errors.",
                "C": "Identifies/uses with multiple prompts (>=3); >=3 errors.",
                "D": "Identifies/uses only with continuous prompts; does not use correctly.",
            }),
            (57, "Simple addition (without carryover)", {
                "A": "Solves addition independently; no errors.",
                "B": "Solves with 1-2 prompts; 1-2 errors.",
                "C": "Solves with multiple prompts (>=3); >=3 errors or incomplete steps.",
                "D": "Solves only with continuous prompts; does not solve correctly.",
            }),
            (58, "Addition with Carryover (Grade Level)", {
                "A": "Performs addition with carryover independently; no errors.",
                "B": "Performs with 1-2 prompts; 1-2 procedural errors.",
                "C": "Performs with multiple prompts (>=3); >=3 errors or incomplete steps.",
                "D": "Performs only with continuous prompts; does not perform correctly.",
            }),
            (59, "Simple Subtraction (without borrowing)", {
                "A": "Solves subtraction independently; no errors.",
                "B": "Solves with 1-2 prompts; 1-2 errors.",
                "C": "Solves with multiple prompts (>=3); >=3 errors or incomplete steps.",
                "D": "Solves only with continuous prompts; does not solve correctly.",
            }),
            (60, "Subtraction with Borrowing (Grade Level)", {
                "A": "Performs subtraction with borrowing independently; no errors.",
                "B": "Performs with 1-2 prompts; 1-2 procedural errors.",
                "C": "Performs with multiple prompts (>=3); >=3 errors or incomplete steps.",
                "D": "Performs only with continuous prompts; does not perform correctly.",
            }),
            (61, "Multiplication Table sequencing (grade level)", {
                "A": "Recalls and sequences tables independently; no errors.",
                "B": "Recalls with 1-2 prompts; 1-2 errors.",
                "C": "Recalls with multiple prompts (>=3); >=3 errors or incomplete recall.",
                "D": "Recalls only with continuous prompts; does not recall correctly.",
            }),
            (62, "Multiplication (Grade Level)", {
                "A": "Solves multiplication independently; no errors.",
                "B": "Solves with 1-2 prompts; 1-2 errors.",
                "C": "Solves with multiple prompts (>=3); >=3 errors or incomplete steps.",
                "D": "Solves only with continuous prompts; does not solve correctly.",
            }),
            (63, "Division (Grade Level)", {
                "A": "Solves division problems independently; no errors.",
                "B": "Solves with 1-2 prompts; 1-2 errors.",
                "C": "Solves with multiple prompts (>=3); >=3 errors or incomplete steps.",
                "D": "Solves only with continuous prompts; does not solve correctly.",
            }),
        ],
        "APPLICATION": [
            (64, "Solving word problems", {
                "A": "Solves word problems independently; no errors in operation or calculation.",
                "B": "Solves with 1-2 prompts; 1-2 errors.",
                "C": "Solves with multiple prompts (>=3); partial solution or >=3 errors.",
                "D": "Solves only with continuous prompts; does not solve correctly.",
            }),
            (65, "Recall of math properties/facts", {
                "A": "Recalls and applies facts/properties independently; no errors.",
                "B": "Recalls/applies with 1-2 prompts; 1-2 errors.",
                "C": "Recalls/applies with multiple prompts (>=3); >=3 errors or incomplete recall.",
                "D": "Recalls/applies only with continuous prompts; does not apply correctly.",
            }),
        ],
    },
    "DOMAIN 8: SOCIO-EMOTIONAL BEHAVIOUR": {
        "PERSISTENCE AND MOTIVATION": [
            (66, "Behaviour During Challenging Tasks", {
                "A": "Persists in tasks independently without prompts.",
                "B": "Persists with 1-2 prompts or reassurance.",
                "C": "Persists with multiple prompts (>=3); may stop before completing.",
                "D": "Requires continuous prompts; does not continue the task.",
            }),
            (67, "Task Initiation (Motivation)", {
                "A": "Initiates tasks independently.",
                "B": "Initiates tasks with 1-2 prompts.",
                "C": "Initiates tasks with multiple prompts (>=3).",
                "D": "Requires continuous prompts; does not initiate tasks.",
            }),
        ],
        "SELF AWARENESS": [
            (68, "Awareness of Own Behaviour", {
                "A": "Identifies own behaviour and corrects it appropriately.",
                "B": "Identifies and corrects with 1-2 prompts.",
                "C": "Identifies and corrects with multiple prompts (>=3); correction may be incomplete.",
                "D": "Requires continuous prompts; does not identify or correct own behaviour.",
            }),
        ],
        "SELF REGULATION": [
            (69, "Emotional control", {
                "A": "Regulates emotions and returns to task independently.",
                "B": "Regulates with 1-2 prompts; returns to task.",
                "C": "Regulates with multiple prompts (>=3); delay in returning.",
                "D": "Requires continuous prompts; does not return to task.",
            }),
            (70, "Impulse control (e.g., interrupting, leaving seat without permission)", {
                "A": "Controls actions independently.",
                "B": "Controls actions with 1-2 prompts; 1-2 impulsive actions.",
                "C": "Controls actions with multiple prompts (>=3); >=3 impulsive actions.",
                "D": "Requires continuous prompts; does not control actions.",
            }),
        ],
        "SOCIAL BEHAVIOUR": [
            (71, "Empathy", {
                "A": "Responds to others' emotions independently.",
                "B": "Responds with 1-2 prompts.",
                "C": "Responds with multiple prompts (>=3); response may be delayed or limited.",
                "D": "Requires continuous prompts; does not respond to others' emotions.",
            }),
            (72, "Peer interactions", {
                "A": "Interacts with peers independently.",
                "B": "Interacts with 1-2 prompts; 1-2 difficulties (sharing, turn-taking).",
                "C": "Interacts with multiple prompts (>=3); limited or incomplete interaction.",
                "D": "Requires continuous prompts; does not interact appropriately.",
            }),
            (73, "Turn Taking", {
                "A": "Waits and takes turns independently.",
                "B": "Waits and takes turns with 1-2 prompts.",
                "C": "Waits and takes turns with multiple prompts (>=3); interrupts or skips turn.",
                "D": "Requires continuous prompts; does not wait or take turns.",
            }),
        ],
        "CLASSROOM FUNCTIONING": [
            (74, "Participation in Group Activities", {
                "A": "Participates and contributes independently.",
                "B": "Participates with 1-2 prompts.",
                "C": "Participates with multiple prompts (>=3); participation is limited.",
                "D": "Requires continuous prompts; does not participate.",
            }),
            (75, "Follows Classroom Routine", {
                "A": "Follows classroom routines independently.",
                "B": "Follows routines with 1-2 prompts.",
                "C": "Follows routines with multiple prompts (>=3).",
                "D": "Requires continuous prompts; does not follow routines.",
            }),
            (76, "Communication of needs", {
                "A": "Communicates needs independently; message is clear.",
                "B": "Communicates with 1-2 prompts.",
                "C": "Communicates with multiple prompts (>=3); message is unclear or incomplete.",
                "D": "Requires continuous prompts; does not communicate needs.",
            }),
            (77, "Response to corrections", {
                "A": "Accepts and responds to correction independently.",
                "B": "Accepts and responds with 1-2 prompts.",
                "C": "Accepts and responds with multiple prompts (>=3); delay or resistance.",
                "D": "Requires continuous prompts; does not respond to correction.",
            }),
        ],
    },
}

GRADE_OPTIONS    = ["A", "B", "C", "D"]
RESPONSES_FILE   = "responses.csv"


# ─────────────────────────────────────────────
# SHARED HELPERS
# ─────────────────────────────────────────────
def get_allowed_questions(subject):
    return SUBJECT_QUESTIONS.get(subject, DEFAULT_QUESTIONS)

def get_visible_domains(subject):
    allowed = get_allowed_questions(subject)
    visible = []
    for domain, sub_domains in CHECKLIST.items():
        for questions in sub_domains.values():
            for (q_no, _, _) in questions:
                if q_no in allowed:
                    visible.append(domain)
                    break
            else:
                continue
            break
    return visible

def save_response(data: dict):
    df_new = pd.DataFrame([data])
    if os.path.exists(RESPONSES_FILE):
        df_old = pd.read_csv(RESPONSES_FILE)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new
    df.to_csv(RESPONSES_FILE, index=False)

def compute_summary(responses: dict):
    counts = {"A": 0, "B": 0, "C": 0, "D": 0}
    for v in responses.values():
        if v in counts:
            counts[v] += 1
    return counts, sum(counts.values())

def level_card(lvl, count, total=0):
    color = LEVEL_COLORS[lvl]
    desc, pct_range = LEVEL_INFO[lvl]
    pct_str = f"<div style='font-size:0.75em;color:#aaa;'>{round(count/total*100,1)}% of items</div>" if total else ""
    return (
        f"<div style='border-top:4px solid {color};padding:10px 12px;background:#fafafa;"
        f"border-radius:8px;text-align:center;margin:4px 0;'>"
        f"<div style='font-weight:bold;color:{color};font-size:1em;'>Level {lvl}</div>"
        f"<div style='font-size:0.78em;color:#555;margin:2px 0;'>{desc}</div>"
        f"<div style='font-size:0.72em;color:#999;'>{pct_range}</div>"
        f"<div style='font-size:2em;font-weight:bold;color:{color};margin:4px 0;'>{count}</div>"
        f"{pct_str}</div>"
    )


# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def show_login():
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: linear-gradient(135deg,#e8eaf6 0%,#fce4ec 100%); }
    </style>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='background:#fff;border-radius:18px;padding:40px 36px;"
            "box-shadow:0 6px 32px rgba(0,0,0,0.12);'>"
            "<div style='text-align:center;margin-bottom:8px;font-size:2.2em;'>📋</div>"
            "<div style='text-align:center;font-size:1.4em;font-weight:700;color:#1a237e;'>"
            "Teacher Observation Checklist</div>"
            "<div style='text-align:center;font-size:0.88em;color:#888;margin-bottom:24px;'>"
            "Early Identification of Learning Difficulties — Grade 1 &amp; 2</div>"
            "<hr style='margin-bottom:24px;'>",
            unsafe_allow_html=True
        )
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Login", type="primary", use_container_width=True):
            if login(username.strip(), password):
                st.rerun()
            else:
                st.error("Invalid username or password. Please try again.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;color:#bbb;font-size:0.78em;margin-top:18px;'>"
            "Contact your administrator if you have trouble logging in.</p>",
            unsafe_allow_html=True
        )


# ─────────────────────────────────────────────
# SHARED HEADER BAR
# ─────────────────────────────────────────────
def render_header(title, subtitle, icon):
    col_t, col_u, col_lo = st.columns([5, 2, 1])
    with col_t:
        st.markdown(f"## {icon} {title}")
        st.caption(subtitle)
    with col_u:
        role_label = "🛡️ Admin" if is_admin() else "👤 Teacher"
        st.markdown(
            f"<div style='text-align:right;padding-top:18px;color:#666;font-size:0.9em;'>"
            f"{role_label}: <strong>{st.session_state['username']}</strong></div>",
            unsafe_allow_html=True
        )
    with col_lo:
        st.markdown("<div style='padding-top:14px;'>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            logout(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# USER (TEACHER) PAGE — checklist only, NO results
# ─────────────────────────────────────────────
def show_user_page():
    render_header(
        "Teacher Observation Checklist",
        "Early Identification of Learning Difficulties — Grade 1 & 2",
        "📋"
    )

    with st.expander("📊 Level Descriptor Reference", expanded=False):
        cols = st.columns(4)
        for i, (lvl, (desc, pct)) in enumerate(LEVEL_INFO.items()):
            c = LEVEL_COLORS[lvl]
            cols[i].markdown(
                f"<div style='border-left:5px solid {c};padding:8px 12px;background:#f9f9f9;border-radius:6px;'>"
                f"<strong style='color:{c};'>Level {lvl}</strong><br>"
                f"<span style='font-size:0.9em;'>{desc}</span><br>"
                f"<span style='font-size:0.8em;color:#999;'>{pct}</span></div>",
                unsafe_allow_html=True
            )

    st.divider()
    st.subheader("👤 Teacher & Student Information")

    c1, c2, c3 = st.columns(3)
    with c1:
        teacher_name  = st.text_input("Subject Teacher Name *")
        subject       = st.selectbox("Subject *", ["— Select —"] + ALL_SUBJECTS)
    with c2:
        student_name  = st.text_input("Student Name *")
        class_section = st.text_input("Class / Section *", placeholder="e.g. Grade 1 – A")
    with c3:
        obs_date = st.date_input("Observation Date *", value=datetime.today())
        roll_no  = st.text_input("Roll Number (optional)")

    if subject == "— Select —":
        st.info("Please select your subject to load the appropriate checklist.")
        return

    allowed_q      = get_allowed_questions(subject)
    visible_domains = get_visible_domains(subject)
    total_q = sum(1 for d in visible_domains for qs in CHECKLIST[d].values()
                  for (q,_,_) in qs if q in allowed_q)

    st.info(f"ℹ️ As a **{subject}** teacher you will complete **{total_q} items** across applicable domains.")
    st.divider()
    st.subheader("📝 Observation Checklist")
    st.caption("Select the level (A / B / C / D) that best describes the student's performance for each item.")

    responses = {}
    for domain in visible_domains:
        d_count = sum(1 for qs in CHECKLIST[domain].values() for (q,_,_) in qs if q in allowed_q)
        with st.expander(f"**{domain}** ({d_count} items)", expanded=False):
            for sub_name, questions in CHECKLIST[domain].items():
                applicable = [(q,qu,d) for (q,qu,d) in questions if q in allowed_q]
                if not applicable: continue
                st.markdown(f"**{sub_name}**")
                for (q_no, question, descriptors) in applicable:
                    key = f"q{q_no}"
                    st.markdown(f"**{q_no}. {question}**")
                    st.dataframe(
                        pd.DataFrame([(l, LEVEL_INFO[l][0], t) for l, t in descriptors.items()],
                                     columns=["Level","Difficulty","Descriptor"]),
                        hide_index=True, use_container_width=True,
                        column_config={
                            "Level":      st.column_config.TextColumn(width="small"),
                            "Difficulty": st.column_config.TextColumn(width="medium"),
                            "Descriptor": st.column_config.TextColumn(width="large"),
                        }
                    )
                    grade = st.radio(f"Q{q_no}", GRADE_OPTIONS, horizontal=True,
                                     key=key, label_visibility="collapsed")
                    responses[key] = grade
                    st.markdown("---")

    st.subheader("🔍 Additional Observations")
    other = st.radio("Any other behaviour observed?", ["No","Yes"], horizontal=True, key="other_b")
    other_det = ""
    if other == "Yes":
        other_det = st.text_area("Please specify:", key="other_d", height=100)

    st.divider()
    if st.button("✅ Submit Checklist", type="primary", use_container_width=True):
        if not teacher_name.strip(): st.error("Please enter the Teacher Name."); return
        if not student_name.strip(): st.error("Please enter the Student Name."); return
        if not class_section.strip(): st.error("Please enter the Class / Section."); return

        record = {
            "Submission Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Teacher Name": teacher_name.strip(),
            "Subject": subject,
            "Student Name": student_name.strip(),
            "Class / Section": class_section.strip(),
            "Roll Number": roll_no.strip(),
            "Observation Date": str(obs_date),
            "Other Behaviour": other,
            "Other Behaviour Details": other_det.strip(),
        }
        record.update(responses)
        save_response(record)

        # ── Teachers see ONLY a thank-you — NO analysis ──
        st.success("✅ Checklist submitted successfully! Thank you for completing the observation.")
        st.info(
            "📌 Your responses have been recorded and will be reviewed by the school administrator. "
            "Please contact your school coordinator for any follow-up or support."
        )


# ─────────────────────────────────────────────
# ADMIN DASHBOARD — full analysis visible
# ─────────────────────────────────────────────
def show_admin_page():
    render_header(
        "Admin Dashboard — Evaluation Results",
        "Teacher Observation Checklist · Grade 1 & 2",
        "🛡️"
    )

    if not os.path.exists(RESPONSES_FILE):
        st.warning("No submissions found yet. Waiting for teachers to submit checklists.")
        return

    df_all = pd.read_csv(RESPONSES_FILE)
    if df_all.empty:
        st.warning("No submissions found yet.")
        return

    # ── Filters ──
    st.subheader("🔎 Filter Submissions")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        sel_student = st.selectbox("Student", ["All"] + sorted(df_all["Student Name"].dropna().unique().tolist()))
    with fc2:
        sel_subject = st.selectbox("Subject",  ["All"] + sorted(df_all["Subject"].dropna().unique().tolist()))
    with fc3:
        sel_class   = st.selectbox("Class / Section", ["All"] + sorted(df_all["Class / Section"].dropna().unique().tolist()))

    df = df_all.copy()
    if sel_student != "All": df = df[df["Student Name"]     == sel_student]
    if sel_subject != "All": df = df[df["Subject"]          == sel_subject]
    if sel_class   != "All": df = df[df["Class / Section"]  == sel_class]

    st.markdown(f"**{len(df)} submission(s) found.**")
    st.divider()

    # ── Raw submissions table ──
    with st.expander("📂 All Submissions (raw data)", expanded=False):
        meta = ["Submission Timestamp","Teacher Name","Subject","Student Name",
                "Class / Section","Roll Number","Observation Date","Other Behaviour","Other Behaviour Details"]
        st.dataframe(df[[c for c in meta if c in df.columns]], hide_index=True, use_container_width=True)
        st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode(),
                           "checklist_responses.csv", "text/csv")

    st.divider()

    # ── Per-submission detailed analysis ──
    st.subheader("📊 Detailed Evaluation per Submission")

    for _, row in df.iterrows():
        student  = row.get("Student Name", "Unknown")
        subj     = row.get("Subject", "Unknown")
        teacher  = row.get("Teacher Name", "")
        cls      = row.get("Class / Section", "")
        obs_date = row.get("Observation Date", "")

        with st.expander(f"📄 {student}  |  {subj}  |  {cls}  |  {obs_date}  |  Teacher: {teacher}", expanded=False):
            responses = {c: str(row[c]) for c in df.columns
                         if c.startswith("q") and c[1:].isdigit()
                         and pd.notna(row.get(c)) and str(row.get(c)) in ["A","B","C","D"]}

            if not responses:
                st.warning("No question responses recorded for this submission.")
                continue

            allowed_q       = get_allowed_questions(subj)
            visible_domains = get_visible_domains(subj)
            counts, total   = compute_summary(responses)

            # Overall cards
            st.markdown("#### Overall Summary")
            oc = st.columns(4)
            for i, lvl in enumerate(["A","B","C","D"]):
                oc[i].markdown(level_card(lvl, counts[lvl], total), unsafe_allow_html=True)

            dominant = max(counts, key=counts.get)
            dc = LEVEL_COLORS[dominant]
            dd, _ = LEVEL_INFO[dominant]
            pv = round(counts[dominant]/total*100, 1) if total else 0
            st.markdown(
                f"<div style='margin:12px 0;padding:12px 16px;background:{dc}15;"
                f"border-left:5px solid {dc};border-radius:8px;'>"
                f"<strong>Overall Profile:</strong> Most frequent rating — "
                f"<span style='color:{dc};font-weight:bold;'>Level {dominant}: {dd}</span> "
                f"({counts[dominant]}/{total} items, {pv}%)</div>",
                unsafe_allow_html=True
            )

            # Domain breakdown
            st.markdown("#### Domain-wise Analysis")
            for domain in visible_domains:
                d_keys = [f"q{q}" for qs in CHECKLIST[domain].values()
                          for (q,_,_) in qs if q in allowed_q]
                dc_map = {"A":0,"B":0,"C":0,"D":0}
                for k in d_keys:
                    if k in responses: dc_map[responses[k]] += 1
                d_total = sum(dc_map.values())
                if d_total == 0: continue

                dlvl  = max(dc_map, key=dc_map.get)
                dclr  = LEVEL_COLORS[dlvl]
                dlbl  = LEVEL_INFO[dlvl][0]
                st.markdown(
                    f"<div style='margin-top:10px;padding:8px 12px;background:{dclr}12;"
                    f"border-left:4px solid {dclr};border-radius:6px;'>"
                    f"<strong>{domain}</strong> &nbsp;|&nbsp; "
                    f"<span style='color:{dclr};font-weight:bold;'>Dominant: Level {dlvl} — {dlbl}</span>"
                    f"</div>", unsafe_allow_html=True
                )
                dcols = st.columns(4)
                for i, lvl in enumerate(["A","B","C","D"]):
                    dcols[i].markdown(level_card(lvl, dc_map[lvl], d_total), unsafe_allow_html=True)

            # Flagged items
            st.markdown("#### ⚠️ Items Requiring Attention (Level C or D)")
            flagged = []
            for domain in visible_domains:
                for sub_name, questions in CHECKLIST[domain].items():
                    for (q_no, question, _) in questions:
                        if q_no not in allowed_q: continue
                        rating = responses.get(f"q{q_no}", "")
                        if rating in ["C","D"]:
                            flagged.append({
                                "Q#": q_no,
                                "Domain": domain.split(":")[0].strip(),
                                "Sub-domain": sub_name,
                                "Question": question,
                                "Level": rating,
                                "Difficulty": LEVEL_INFO[rating][0],
                            })

            if flagged:
                fdf = pd.DataFrame(flagged)
                def hl(r):
                    bg = "#fce4e4" if r["Level"] == "D" else "#fff8e1"
                    return [f"background-color:{bg}"] * len(r)
                st.dataframe(fdf.style.apply(hl, axis=1), hide_index=True, use_container_width=True)
                sev = sum(1 for x in flagged if x["Level"] == "D")
                mod = sum(1 for x in flagged if x["Level"] == "C")
                st.markdown(
                    f"**{sev}** item(s) — Severe Difficulty (D) &nbsp;|&nbsp; "
                    f"**{mod}** item(s) — Moderate Difficulty (C)"
                )
            else:
                st.success("No items flagged at Moderate or Severe Difficulty.")

    st.divider()

    # ── Aggregate stats ──
    st.subheader("📈 Aggregate Statistics Across Filtered Submissions")
    q_cols = [c for c in df.columns if c.startswith("q") and c[1:].isdigit()]
    agg = {"A":0,"B":0,"C":0,"D":0}
    for v in df[q_cols].values.flatten():
        if str(v) in agg: agg[str(v)] += 1
    agg_total = sum(agg.values())

    if agg_total > 0:
        ac = st.columns(4)
        for i, lvl in enumerate(["A","B","C","D"]):
            ac[i].markdown(level_card(lvl, agg[lvl], agg_total), unsafe_allow_html=True)

        agg_df = pd.DataFrame([{
            "Level": lvl, "Label": LEVEL_INFO[lvl][0],
            "Count": agg[lvl],
            "Percentage": f"{round(agg[lvl]/agg_total*100,1)}%"
        } for lvl in ["A","B","C","D"]])
        st.dataframe(agg_df, hide_index=True, use_container_width=True)
    else:
        st.info("No rated items found in filtered submissions.")


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
def main():
    if not is_logged_in():
        show_login()
    elif is_admin():
        show_admin_page()
    else:
        show_user_page()

if __name__ == "__main__":
    main()
