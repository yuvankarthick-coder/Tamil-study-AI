import streamlit as st
import re
import random
from datetime import datetime

# Optional PDF support
try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Tamil Study AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main {
        background: #f7f8fc;
    }

    .hero {
        padding: 2rem;
        border-radius: 22px;
        background: linear-gradient(
            135deg,
            #eef2ff 0%,
            #f8fafc 55%,
            #ecfeff 100%
        );
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        margin-bottom: 0.35rem;
        font-size: 2.4rem;
    }

    .hero p {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 0.3rem;
    }

    .card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 1.2rem;
        margin: 0.7rem 0;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }

    .question-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.65rem 0;
    }

    .flashcard {
        min-height: 190px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 20px;
        padding: 2rem;
    }

    .flashcard .front {
        font-size: 1.35rem;
        font-weight: 700;
    }

    .flashcard .back {
        margin-top: 1rem;
        color: #475569;
        font-size: 1.05rem;
    }

    .tag {
        display: inline-block;
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        background: #eef2ff;
        margin: 0.15rem;
        font-size: 0.82rem;
    }

    .footer {
        text-align: center;
        color: #94a3b8;
        padding: 2rem 0 1rem;
        font-size: 0.85rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# CONSTANTS
# =========================================================

SUBJECTS = [
    "Tamil",
    "English",
    "Mathematics",
    "Science",
    "Social Science",
    "Computer Science",
    "General",
]

EXAM_GOALS = [
    "General Revision",
    "Unit Test",
    "Quarterly",
    "Half-Yearly",
    "Annual Exam",
    "Exam Tomorrow",
]


# =========================================================
# SESSION STATE
# =========================================================

defaults = {
    "page": "Home",

    "profile": {
        "class": "10",
        "board": "Tamil Nadu State Board",
        "medium": "Tamil Medium",
        "subject": "Science",
        "exam": "General Revision",
    },

    "study_text": "",
    "chapter_title": "",
    "source_name": "",

    "exam_pack": None,

    "flashcards": [],
    "flashcard_index": 0,
    "flashcard_revealed": False,

    "quiz_questions": [],
    "quiz_answers": {},
    "quiz_submitted": False,
    "quiz_result_recorded": False,
    "quiz_version": 0,

    "quiz_history": [],

    "bookmarks": [],
    "difficult_topics": [],

    "study_sessions": 0,
    "completed_packs": 0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# TEXT HELPERS
# =========================================================

def clean_text(text):
    if not text:
        return ""

    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def sentences_from_text(text):
    text = clean_text(text)

    if not text:
        return []

    parts = re.split(
        r"(?<=[.!?。！？])\s+|\n+",
        text
    )

    return [
        part.strip()
        for part in parts
        if len(part.strip()) > 20
    ]


def words(text):
    return re.findall(
        r"[A-Za-zÀ-ÿ\u0B80-\u0BFF0-9]+",
        text or ""
    )


def word_count(text):
    return len(words(text))


def safe_title(text, fallback="Untitled Chapter"):
    text = clean_text(text)

    if not text:
        return fallback

    first = re.split(
        r"[.!?\n]",
        text
    )[0].strip()

    if len(first) > 80:
        first = first[:80].rsplit(" ", 1)[0]

    return first.title()


# =========================================================
# PDF
# =========================================================

def extract_pdf_text(uploaded_file):

    if not PDF_AVAILABLE:
        return ""

    try:
        data = uploaded_file.read()

        document = fitz.open(
            stream=data,
            filetype="pdf"
        )

        pages = []

        for page in document:
            pages.append(page.get_text())

        document.close()

        return clean_text(
            "\n".join(pages)
        )

    except Exception:
        return ""


# =========================================================
# KEY POINT EXTRACTION
# =========================================================

def extract_key_points(text, limit=10):

    sentences = sentences_from_text(text)

    if not sentences:
        return []

    keywords = [
        "important",
        "main",
        "defined",
        "means",
        "because",
        "therefore",
        "process",
        "function",
        "causes",
        "result",
        "used",
        "called",
        "known",
        "consists",
        "includes",

        "முக்கிய",
        "என்பது",
        "ஆகும்",
        "காரணம்",
        "செயல்முறை",
        "பயன்பாடு",
        "வகைகள்",
        "வரையறை",
    ]

    scored = []

    for index, sentence in enumerate(sentences):

        score = 0

        lower = sentence.lower()

        for keyword in keywords:

            if keyword in lower:
                score += 2

        if 45 <= len(sentence) <= 240:
            score += 1

        scored.append(
            (
                score,
                index,
                sentence
            )
        )

    scored.sort(
        key=lambda item: (
            -item[0],
            item[1]
        )
    )

    selected = []
    seen = set()

    for _, _, sentence in scored:

        normalized = sentence.lower()

        if normalized not in seen:

            selected.append(sentence)
            seen.add(normalized)

        if len(selected) >= limit:
            break

    return selected


# =========================================================
# KEY TERMS
# =========================================================

def extract_key_terms(text, limit=12):

    stopwords = {
        "this",
        "that",
        "with",
        "from",
        "have",
        "were",
        "which",
        "their",
        "there",
        "about",
        "into",
        "also",
        "than",
        "then",
        "they",
        "them",
        "these",
        "those",
        "will",
        "would",
        "could",
        "should",
        "being",
        "been",
        "such",
        "each",
        "other",
        "and",
        "the",
        "for",
        "are",
        "was",
        "has",
        "not",
        "but",

        "ஒரு",
        "இந்த",
        "அது",
        "என்று",
        "மற்றும்",
        "ஆகும்",
        "உள்ள",
        "என்பது",
        "மூலம்",
        "மேலும்",
    }

    frequency = {}

    for word in words(text):

        normalized = word.lower()

        if (
            len(normalized) >= 4
            and normalized not in stopwords
        ):
            frequency[normalized] = (
                frequency.get(normalized, 0) + 1
            )

    ranked = sorted(
        frequency.items(),
        key=lambda item: (
            -item[1],
            item[0]
        )
    )

    return [
        term
        for term, _ in ranked[:limit]
    ]


# =========================================================
# FORMULA EXTRACTION
# =========================================================

def extract_formulas(text, limit=10):

    found = []

    lines = re.split(
        r"[\n.;]",
        text or ""
    )

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if (
            "=" in line
            or "formula" in line.lower()
            or "equation" in line.lower()
            or "சூத்திரம்" in line.lower()
        ):

            if len(line) <= 180:
                found.append(line)

        if len(found) >= limit:
            break

    return found


# =========================================================
# SIMPLE TAMIL EXPLANATION
# =========================================================

def tamil_explanation(text, subject):

    points = extract_key_points(
        text,
        limit=6
    )

    if not points:

        return (
            "இந்தப் பாடத்திற்கான உரை போதுமானதாக இல்லை. "
            "மேலும் chapter content-ஐ சேர்க்கவும்."
        )

    lower = text.lower()

    special_explanations = {

        "photosynthesis":
            "ஒளிச்சேர்க்கை என்பது தாவரங்கள் சூரிய ஒளியின் உதவியுடன் "
            "கார்பன் டைஆக்சைடு மற்றும் நீரைப் பயன்படுத்தி உணவை உருவாக்கும் "
            "செயல்முறை. இந்த செயல்முறையில் ஆக்சிஜன் வெளியிடப்படுகிறது.",

        "gravity":
            "ஈர்ப்பு விசை என்பது பொருட்களை ஒன்றை ஒன்று நோக்கி இழுக்கும் விசை. "
            "பூமியின் ஈர்ப்பு விசை காரணமாக பொருட்கள் கீழ்நோக்கி விழுகின்றன.",

        "atom":
            "அணு என்பது ஒரு தனிமத்தின் பண்புகளைத் தக்கவைக்கும் மிகச் சிறிய அலகு. "
            "அணுவில் புரோட்டான், நியூட்ரான் மற்றும் எலக்ட்ரான் போன்ற துகள்கள் உள்ளன.",

        "democracy":
            "ஜனநாயகம் என்பது மக்கள் தங்களின் பிரதிநிதிகளைத் தேர்ந்தெடுத்து "
            "ஆட்சியில் பங்கேற்கும் அரசியல் முறை.",
    }

    for keyword, explanation in special_explanations.items():

        if keyword in lower:
            return explanation

    bullets = "\n".join(
        f"• {point}"
        for point in points[:5]
    )

    return (
        "**எளிய விளக்கம்**\n\n"
        f"{bullets}\n\n"
        "👉 ஒவ்வொரு கருத்தையும் உங்கள் சொந்த வார்த்தைகளில் "
        "சொல்லிப் பாருங்கள். பின்னர் mark-wise questions-ஐ practice செய்யுங்கள்."
    )


# =========================================================
# ENGLISH SUMMARY
# =========================================================

def english_summary(text):

    points = extract_key_points(
        text,
        limit=5
    )

    if not points:
        return "Add more chapter content."

    return "\n".join(
        f"• {point}"
        for point in points
    )


# =========================================================
# MARK-WISE QUESTIONS
# =========================================================

def make_mark_questions(text, mark, count=5):

    points = extract_key_points(
        text,
        limit=12
    )

    terms = extract_key_terms(
        text,
        limit=12
    )

    questions = []

    for point in points:

        if mark == 1:

            question = (
                "Define or identify the main idea in this statement: "
                f"{point}"
            )

        elif mark == 2:

            question = (
                f"Write two important points about: {point}"
            )

        elif mark == 3:

            question = (
                f"Explain the idea clearly and give relevant details: "
                f"{point}"
            )

        else:

            question = (
                "Explain the following topic in a structured answer "
                "with definition, key points and relevant details: "
                f"{point}"
            )

        questions.append(question)

        if len(questions) >= count:
            break

    for term in terms:

        if mark == 1:
            question = f"What is {term}?"

        elif mark == 2:
            question = f"Write two points about {term}."

        elif mark == 3:
            question = f"Explain {term} briefly."

        else:
            question = f"Write a detailed answer about {term}."

        if question not in questions:
            questions.append(question)

        if len(questions) >= count:
            break

    fallbacks = {

        1: [
            "What is the main definition from this chapter?",
            "Name one important term from the chapter.",
        ],

        2: [
            "Write any two important points from the chapter.",
            "State two key facts you learned.",
        ],

        3: [
            "Explain one major concept from the chapter.",
            "Describe an important process from the chapter.",
        ],

        5: [
            "Write a detailed answer covering the main concepts in this chapter.",
            "Explain the most important topic from this chapter with suitable points.",
        ],
    }

    for question in fallbacks[mark]:

        if len(questions) >= count:
            break

        if question not in questions:
            questions.append(question)

    return questions[:count]


# =========================================================
# MODEL ANSWER GUIDANCE
# =========================================================

def model_answer_for_question(
    question,
    text,
    mark
):

    if mark == 1:

        return (
            "Answer format: give one precise definition, "
            "name or fact. Keep it short and direct."
        )

    if mark == 2:

        return (
            "Answer format:\n"
            "1. State the main point.\n"
            "2. Add one supporting point.\n\n"
            "Use chapter terminology where possible."
        )

    if mark == 3:

        return (
            "Answer format:\n"
            "• Definition/main idea\n"
            "• 2–3 important details\n"
            "• Example or result if supported by the chapter."
        )

    return (
        "Answer format:\n"
        "• Introduction/definition\n"
        "• Main explanation\n"
        "• Supporting points\n"
        "• Example/process/result when supported\n"
        "• Short conclusion"
    )


# =========================================================
# FLASHCARDS
# =========================================================

def make_flashcards(
    text,
    count=10
):

    cards = []

    points = extract_key_points(
        text,
        count
    )

    for point in points:

        cards.append(
            {
                "front": "What is the key idea here?",
                "back": point,
            }
        )

    return cards


# =========================================================
# REVISION PLAN
# =========================================================

def make_revision_plan(
    exam_goal
):

    if exam_goal == "Exam Tomorrow":

        return [
            "30 min — Understand the chapter.",
            "25 min — Learn key points and terms.",
            "30 min — Practice 1/2-mark questions.",
            "35 min — Practice 3/5-mark questions.",
            "20 min — Take the mock test.",
            "10 min — Review mistakes.",
        ]

    return [
        "Understand the chapter.",
        "Review key points and terms.",
        "Practice questions by marks.",
        "Use flashcards for active recall.",
        "Take the mock test.",
        "Review mistakes.",
    ]


# =========================================================
# BUILD EXAM PACK
# =========================================================

def build_exam_pack(
    text,
    profile,
    title
):

    return {

        "chapter_title": title,

        "profile": profile.copy(),

        "tamil_explanation":
            tamil_explanation(
                text,
                profile["subject"]
            ),

        "english_summary":
            english_summary(text),

        "key_points":
            extract_key_points(
                text,
                10
            ),

        "key_terms":
            extract_key_terms(
                text,
                12
            ),

        "formulas":
            extract_formulas(
                text,
                10
            ),

        "questions": {

            1: make_mark_questions(
                text,
                1,
                6
            ),

            2: make_mark_questions(
                text,
                2,
                5
            ),

            3: make_mark_questions(
                text,
                3,
                5
            ),

            5: make_mark_questions(
                text,
                5,
                5
            ),
        },

        "flashcards":
            make_flashcards(text),

        "revision_plan":
            make_revision_plan(
                profile["exam"]
            ),

        "quick_revision":
            extract_key_points(
                text,
                7
            ),

        "created_at":
            datetime.now().strftime(
                "%d %b %Y, %I:%M %p"
            ),
    }


# =========================================================
# MOCK TEST
# =========================================================

def build_quiz_questions(
    text,
    count=8
):

    points = extract_key_points(
        text,
        12
    )

    questions = []

    for index, point in enumerate(
        points[:count]
    ):

        if len(point) > 115:

            correct = (
                point[:115]
                .rsplit(" ", 1)[0]
                + "..."
            )

        else:

            correct = point

        distractors = []

        for other in points:

            if other == point:
                continue

            if len(other) > 115:

                distractor = (
                    other[:115]
                    .rsplit(" ", 1)[0]
                    + "..."
                )

            else:

                distractor = other

            if distractor not in distractors:
                distractors.append(
                    distractor
                )

            if len(distractors) >= 3:
                break

        while len(distractors) < 3:

            distractors.append(
                "Not stated in the supplied chapter."
            )

        options = [
            correct
        ] + distractors[:3]

        random.Random(
            index + 42
        ).shuffle(options)

        questions.append(
            {
                "question":
                    "Which option best represents an important point from the chapter?",

                "options":
                    options,

                "answer":
                    correct,
            }
        )

    return questions


# =========================================================
# ACTIONS
# =========================================================

def load_material(
    text,
    source="",
    title=""
):

    text = clean_text(text)

    st.session_state.study_text = text

    st.session_state.source_name = source

    st.session_state.chapter_title = (
        title.strip()
        if title.strip()
        else safe_title(text)
    )

    st.session_state.exam_pack = None

    st.session_state.flashcards = []

    st.session_state.quiz_questions = []

    st.session_state.quiz_answers = {}

    st.session_state.quiz_submitted = False

    st.session_state.quiz_result_recorded = False


def create_exam_pack():

    if not st.session_state.study_text:
        return False

    st.session_state.exam_pack = build_exam_pack(
        st.session_state.study_text,
        st.session_state.profile,
        st.session_state.chapter_title
    )

    st.session_state.flashcards = (
        st.session_state.exam_pack["flashcards"]
    )

    st.session_state.flashcard_index = 0

    st.session_state.flashcard_revealed = False

    st.session_state.quiz_questions = (
        build_quiz_questions(
            st.session_state.study_text
        )
    )

    st.session_state.quiz_answers = {}

    st.session_state.quiz_submitted = False

    st.session_state.quiz_result_recorded = False

    st.session_state.study_sessions += 1

    st.session_state.completed_packs += 1

    return True


def save_bookmark(
    label,
    content
):

    item = {

        "label": label,

        "content": content,

        "subject":
            st.session_state.profile["subject"],

        "created_at":
            datetime.now().strftime(
                "%d %b %Y"
            ),
    }

    if item not in st.session_state.bookmarks:

        st.session_state.bookmarks.append(
            item
        )


def add_difficult_topic(
    topic
):

    topic = clean_text(topic)

    existing = [
        item["topic"]
        for item in st.session_state.difficult_topics
    ]

    if topic and topic not in existing:

        st.session_state.difficult_topics.append(
            {
                "topic": topic,

                "subject":
                    st.session_state.profile["subject"],

                "created_at":
                    datetime.now().strftime(
                        "%d %b %Y"
                    ),
            }
        )


def record_quiz_result():

    if (
        not st.session_state.quiz_questions
        or st.session_state.quiz_result_recorded
    ):
        return

    score = sum(

        st.session_state.quiz_answers.get(
            index
        ) == question["answer"]

        for index, question
        in enumerate(
            st.session_state.quiz_questions
        )
    )

    total = len(
        st.session_state.quiz_questions
    )

    st.session_state.quiz_history.append(
        {
            "chapter":
                st.session_state.chapter_title,

            "subject":
                st.session_state.profile["subject"],

            "score":
                score,

            "total":
                total,

            "date":
                datetime.now().strftime(
                    "%d %b %Y %I:%M %p"
                ),
        }
    )

    st.session_state.quiz_result_recorded = True


# =========================================================
# EXPORT
# =========================================================

def build_text_export(
    pack
):

    lines = [

        "TAMIL STUDY AI — EXAM PACK",

        "=" * 60,

        f"Chapter: {pack['chapter_title']}",

        f"Class: {pack['profile']['class']}",

        f"Board: {pack['profile']['board']}",

        f"Medium: {pack['profile']['medium']}",

        f"Subject: {pack['profile']['subject']}",

        f"Exam Goal: {pack['profile']['exam']}",

        "",

        "SIMPLE TAMIL EXPLANATION",

        "-" * 60,

        re.sub(
            r"[*#]",
            "",
            pack["tamil_explanation"]
        ),

        "",

        "ENGLISH SUMMARY",

        "-" * 60,

        pack["english_summary"],

        "",

        "KEY POINTS",

        "-" * 60,
    ]

    for point in pack["key_points"]:

        lines.append(
            f"- {point}"
        )

    lines.extend(
        [
            "",
            "KEY TERMS",
            "-" * 60,
            ", ".join(
                pack["key_terms"]
            ),
            "",
            "FORMULAS / EQUATIONS",
            "-" * 60,
        ]
    )

    for formula in pack["formulas"]:

        lines.append(
            f"- {formula}"
        )

    for mark in [1, 2, 3, 5]:

        lines.extend(
            [
                "",
                f"{mark}-MARK PRACTICE",
                "-" * 60,
            ]
        )

        for question in pack["questions"][mark]:

            lines.append(
                f"- {question}"
            )

    lines.extend(
        [
            "",
            "REVISION PLAN",
            "-" * 60,
        ]
    )

    for item in pack["revision_plan"]:

        lines.append(
            f"- {item}"
        )

    return "\n".join(lines)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        "## 📚 Tamil Study AI"
    )

    st.caption(
        "Chapter → Exam Preparation"
    )

    pages = [

        "Home",

        "Create Exam Pack",

        "Chapter Workspace",

        "Practice by Marks",

        "Flashcards",

        "Mock Test",

        "My Progress",

        "Saved & Difficult",

        "About V6",
    ]

    st.session_state.page = st.radio(
        "Study",
        pages,
        index=pages.index(
            st.session_state.page
        ),
    )

    st.divider()

    st.markdown(
        "### 🎯 Study Profile"
    )

    profile = st.session_state.profile

    profile["class"] = st.selectbox(
        "Class",
        [str(i) for i in range(1, 13)],
        index=int(profile["class"]) - 1,
    )

    profile["board"] = st.selectbox(
        "Board",
        [
            "Tamil Nadu State Board",
            "CBSE",
            "Other",
        ],
        index=[
            "Tamil Nadu State Board",
            "CBSE",
            "Other",
        ].index(
            profile["board"]
        ),
    )

    profile["medium"] = st.selectbox(
        "Medium",
        [
            "Tamil Medium",
            "English Medium",
            "Bilingual",
        ],
        index=[
            "Tamil Medium",
            "English Medium",
            "Bilingual",
        ].index(
            profile["medium"]
        ),
    )

    profile["subject"] = st.selectbox(
        "Subject",
        SUBJECTS,
        index=SUBJECTS.index(
            profile["subject"]
        ),
    )

    profile["exam"] = st.selectbox(
        "Exam / Goal",
        EXAM_GOALS,
        index=EXAM_GOALS.index(
            profile["exam"]
        ),
    )

    st.divider()

    st.metric(
        "Study sessions",
        st.session_state.study_sessions
    )

    st.metric(
        "Exam packs",
        st.session_state.completed_packs
    )

    st.metric(
        "Mock tests",
        len(
            st.session_state.quiz_history
        )
    )

    st.caption(
        "V6 • No API • No payments"
    )


# =========================================================
# HERO
# =========================================================

st.markdown(
    f"""
    <div class="hero">

        <h1>📚 Tamil Study AI</h1>

        <p>
            <strong>
                Turn one chapter into a structured
                exam-preparation pack.
            </strong>
        </p>

        <p>
            Class {profile["class"]} ·
            {profile["board"]} ·
            {profile["subject"]} ·
            {profile["exam"]}
        </p>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HOME
# =========================================================

if st.session_state.page == "Home":

    st.markdown(
        "## Start with a chapter"
    )

    st.info(
        "Best workflow: add one chapter → create an Exam Pack → "
        "practice by marks → flashcards → mock test → review mistakes."
    )

    col1, col2 = st.columns(
        [1.35, 1]
    )

    with col1:

        st.markdown(
            "### 📥 Add your study material"
        )

        title = st.text_input(
            "Chapter title",
            value=st.session_state.chapter_title,
            placeholder="Example: Photosynthesis",
        )

        input_mode = st.radio(
            "Input",
            [
                "Paste / type text",
                "Upload PDF",
            ],
            horizontal=True,
        )

        if input_mode == "Paste / type text":

            text_input = st.text_area(
                "Paste your textbook/chapter content",
                value=st.session_state.study_text,
                height=280,
                placeholder=(
                    "Paste the chapter content here. "
                    "For the best result, include the complete lesson."
                ),
            )

            if st.button(
                "📥 Load Chapter",
                type="primary",
                use_container_width=True,
            ):

                if len(
                    clean_text(text_input)
                ) < 80:

                    st.warning(
                        "Please add more chapter content."
                    )

                else:

                    load_material(
                        text_input,
                        "Pasted text",
                        title
                    )

                    st.success(
                        "Chapter loaded."
                    )

                    st.session_state.page = (
                        "Create Exam Pack"
                    )

                    st.rerun()

        else:

            uploaded = st.file_uploader(
                "Upload a PDF chapter",
                type=["pdf"],
            )

            if uploaded:

                if not PDF_AVAILABLE:

                    st.error(
                        "PDF support is unavailable. "
                        "Add PyMuPDF to requirements.txt."
                    )

                elif st.button(
                    "📥 Read PDF",
                    type="primary",
                    use_container_width=True,
                ):

                    extracted = extract_pdf_text(
                        uploaded
                    )

                    if len(extracted) < 80:

                        st.warning(
                            "Very little text was found in this PDF."
                        )

                    else:

                        load_material(
                            extracted,
                            uploaded.name,
                            title
                        )

                        st.success(
                            "PDF chapter loaded."
                        )

                        st.session_state.page = (
                            "Create Exam Pack"
                        )

                        st.rerun()

    with col2:

        st.markdown(
            "### 🚀 What you get"
        )

        features = [

            (
                "🧠",
                "Simple understanding",
                "Structured explanation from your supplied chapter."
            ),

            (
                "📝",
                "1 / 2 / 3 / 5-mark practice",
                "Practice in mark-based format."
            ),

            (
                "🃏",
                "Flashcards",
                "Active-recall cards from your chapter."
            ),

            (
                "🎯",
                "Mock test",
                "Check understanding and review mistakes."
            ),

            (
                "📈",
                "Progress",
                "Quiz history and difficult topics."
            ),

            (
                "⬇️",
                "Export",
                "Download your Exam Pack as text."
            ),
        ]

        for icon, title_text, description in features:

            st.markdown(
                f"""
                <div class="card">

                    <h4>
                        {icon} {title_text}
                    </h4>

                    <p>
                        {description}
                    </p>

                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        "## The core workflow"
    )

    st.markdown(
        """
        **Understand → Learn key points → Practice by marks →
        Recall → Test → Review mistakes**
        """
    )


# =========================================================
# CREATE EXAM PACK
# =========================================================

elif st.session_state.page == "Create Exam Pack":

    st.markdown(
        "## 🎯 Create My Exam Pack"
    )

    if not st.session_state.study_text:

        st.warning(
            "Load a chapter first from Home."
        )

    else:

        st.markdown(
            f"""
            <div class="card">

                <h3>
                    {st.session_state.chapter_title}
                </h3>

                <p>
                    {word_count(st.session_state.study_text):,}
                    words ·
                    {st.session_state.source_name or "Study material"}
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "1-mark",
            "6"
        )

        c2.metric(
            "2-mark",
            "5"
        )

        c3.metric(
            "3-mark",
            "5"
        )

        c4.metric(
            "5-mark",
            "5"
        )

        st.markdown(
            "### Your Exam Pack includes"
        )

        st.write(
            "🧠 Simple Tamil · "
            "📌 Key points · "
            "🔑 Terms · "
            "📐 Formulas · "
            "📝 Mark-wise practice · "
            "🃏 Flashcards · "
            "🎯 Mock test · "
            "📈 Revision plan"
        )

        if st.button(
            "🚀 Build My Exam Pack",
            type="primary",
            use_container_width=True,
        ):

            create_exam_pack()

            st.success(
                "Exam Pack created."
            )

            st.rerun()

        if st.session_state.exam_pack:

            pack = st.session_state.exam_pack

            st.divider()

            left, right = st.columns(2)

            with left:

                st.markdown(
                    "### 🧠 Simple Tamil Explanation"
                )

                st.markdown(
                    pack["tamil_explanation"]
                )

            with right:

                st.markdown(
                    "### 🇬🇧 Quick English Summary"
                )

                st.markdown(
                    pack["english_summary"]
                )

            st.markdown(
                "### 📌 Key Points"
            )

            for point in pack["key_points"]:

                st.markdown(
                    f"- {point}"
                )

            st.markdown(
                "### 🔑 Key Terms"
            )

            if pack["key_terms"]:

                st.markdown(
                    " ".join(
                        f'<span class="tag">{term}</span>'
                        for term in pack["key_terms"]
                    ),
                    unsafe_allow_html=True,
                )

            if pack["formulas"]:

                st.markdown(
                    "### 📐 Formulas / Equations"
                )

                for formula in pack["formulas"]:

                    st.code(
                        formula
                    )

            st.markdown(
                "### ⚡ Quick Revision"
            )

            for item in pack["quick_revision"]:

                st.markdown(
                    f"- {item}"
                )

            st.markdown(
                "### 🗓️ Revision Plan"
            )

            for item in pack["revision_plan"]:

                st.markdown(
                    f"- {item}"
                )

            st.download_button(
                "⬇️ Download Exam Pack (.txt)",
                data=build_text_export(pack),
                file_name="tamil_study_ai_exam_pack.txt",
                mime="text/plain",
                use_container_width=True,
            )


# =========================================================
# CHAPTER WORKSPACE
# =========================================================

elif st.session_state.page == "Chapter Workspace":

    st.markdown(
        "## 📖 Chapter Workspace"
    )

    if not st.session_state.study_text:

        st.warning(
            "Load a chapter first."
        )

    else:

        st.markdown(
            f"### {st.session_state.chapter_title}"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Words",
            f"{word_count(st.session_state.study_text):,}"
        )

        c2.metric(
            "Key points",
            len(
                extract_key_points(
                    st.session_state.study_text
                )
            )
        )

        c3.metric(
            "Key terms",
            len(
                extract_key_terms(
                    st.session_state.study_text
                )
            )
        )

        st.divider()

        st.markdown(
            "### 🧠 Simple Tamil Explanation"
        )

        st.markdown(
            tamil_explanation(
                st.session_state.study_text,
                profile["subject"]
            )
        )

        st.markdown(
            "### 📌 Key Points"
        )

        for point in extract_key_points(
            st.session_state.study_text,
            10
        ):

            st.markdown(
                f"- {point}"
            )

        st.markdown(
            "### 🔑 Key Terms"
        )

        st.write(
            ", ".join(
                extract_key_terms(
                    st.session_state.study_text
                )
            )
        )

        st.markdown(
            "### 🇬🇧 English Summary"
        )

        st.markdown(
            english_summary(
                st.session_state.study_text
            )
        )

        if st.button(
            "🔖 Save chapter as bookmark"
        ):

            save_bookmark(
                st.session_state.chapter_title,
                st.session_state.study_text[:1200]
            )

            st.success(
                "Saved."
            )


# =========================================================
# PRACTICE BY MARKS
# =========================================================

elif st.session_state.page == "Practice by Marks":

    st.markdown(
        "## 📝 Practice by Marks"
    )

    if not st.session_state.exam_pack:

        st.warning(
            "Create an Exam Pack first."
        )

    else:

        pack = st.session_state.exam_pack

        tabs = st.tabs(
            [
                "1 Mark",
                "2 Marks",
                "3 Marks",
                "5 Marks",
            ]
        )

        for tab, mark in zip(
            tabs,
            [1, 2, 3, 5]
        ):

            with tab:

                st.caption(
                    "Exam-style practice generated from your supplied chapter. "
                    "These are not predictions of actual exam questions."
                )

                for index, question in enumerate(
                    pack["questions"][mark],
                    start=1
                ):

                    with st.container(
                        border=True
                    ):

                        st.markdown(
                            f"**Q{index}. {question}**"
                        )

                        with st.expander(
                            "💡 Model-answer guidance"
                        ):

                            st.write(
                                model_answer_for_question(
                                    question,
                                    st.session_state.study_text,
                                    mark
                                )
                            )

                        if st.button(
                            "🔖 Save question",
                            key=f"save_{mark}_{index}",
                        ):

                            save_bookmark(
                                f"{mark}-mark: {question}",
                                model_answer_for_question(
                                    question,
                                    st.session_state.study_text,
                                    mark
                                )
                            )

                            st.success(
                                "Saved."
                            )


# =========================================================
# FLASHCARDS
# =========================================================

elif st.session_state.page == "Flashcards":

    st.markdown(
        "## 🃏 Flashcards"
    )

    if not st.session_state.flashcards:

        st.warning(
            "Create an Exam Pack first."
        )

    else:

        cards = st.session_state.flashcards

        index = st.session_state.flashcard_index

        card = cards[index]

        st.caption(
            f"Card {index + 1} of {len(cards)}"
        )

        answer = (
            card["back"]
            if st.session_state.flashcard_revealed
            else "Click Reveal Answer"
        )

        st.markdown(
            f"""
            <div class="flashcard">

                <div class="front">
                    {card["front"]}
                </div>

                <div class="back">
                    {answer}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        c1, c2, c3 = st.columns(3)

        if c1.button(
            "⬅️ Previous",
            use_container_width=True
        ):

            st.session_state.flashcard_index = max(
                0,
                index - 1
            )

            st.session_state.flashcard_revealed = False

            st.rerun()

        if c2.button(
            "🙈 Hide"
            if st.session_state.flashcard_revealed
            else "👀 Reveal Answer",
            type="primary",
            use_container_width=True,
        ):

            st.session_state.flashcard_revealed = (
                not st.session_state.flashcard_revealed
            )

            st.rerun()

        if c3.button(
            "Next ➡️",
            use_container_width=True
        ):

            st.session_state.flashcard_index = min(
                len(cards) - 1,
                index + 1
            )

            st.session_state.flashcard_revealed = False

            st.rerun()


# =========================================================
# MOCK TEST
# =========================================================

elif st.session_state.page == "Mock Test":

    st.markdown(
        "## 🎯 Mock Test"
    )

    if not st.session_state.study_text:

        st.warning(
            "Load a chapter first."
        )

    else:

        if not st.session_state.quiz_questions:

            st.session_state.quiz_questions = (
                build_quiz_questions(
                    st.session_state.study_text
                )
            )

        questions = (
            st.session_state.quiz_questions
        )

        st.caption(
            "Questions are generated from your supplied material. "
            "They are for practice, not exam prediction."
        )

        if st.button(
            "🔄 New Mock Test"
        ):

            st.session_state.quiz_questions = (
                build_quiz_questions(
                    st.session_state.study_text
                )
            )

            st.session_state.quiz_answers = {}

            st.session_state.quiz_submitted = False

            st.session_state.quiz_result_recorded = False

            st.session_state.quiz_version += 1

            st.rerun()

        for index, question in enumerate(
            questions
        ):

            st.markdown(
                f"""
                <div class="question-box">

                    <strong>
                        Q{index + 1}.
                        {question["question"]}
                    </strong>

                </div>
                """,
                unsafe_allow_html=True,
            )

            selected = st.radio(
                "Choose one",
                question["options"],
                index=None,
                key=(
                    f"quiz_"
                    f"{st.session_state.quiz_version}_"
                    f"{index}"
                ),
                label_visibility="collapsed",
            )

            st.session_state.quiz_answers[
                index
            ] = selected

        if st.button(
            "✅ Submit Test",
            type="primary",
            use_container_width=True,
        ):

            unanswered = any(
                st.session_state.quiz_answers.get(
                    index
                ) is None

                for index in range(
                    len(questions)
                )
            )

            if unanswered:

                st.warning(
                    "Please answer every question."
                )

            else:

                st.session_state.quiz_submitted = True

                record_quiz_result()

                st.rerun()

        if st.session_state.quiz_submitted:

            score = sum(

                st.session_state.quiz_answers.get(
                    index
                ) == question["answer"]

                for index, question
                in enumerate(questions)
            )

            total = len(questions)

            percentage = round(
                score / total * 100
            )

            st.success(
                f"Score: {score}/{total} "
                f"({percentage}%)"
            )

            st.markdown(
                "### 🔍 Review"
            )

            for index, question in enumerate(
                questions
            ):

                user_answer = (
                    st.session_state.quiz_answers.get(
                        index
                    )
                )

                if user_answer == question["answer"]:

                    st.markdown(
                        f"✅ Q{index + 1}: Correct"
                    )

                else:

                    st.markdown(
                        f"""
                        ❌ Q{index + 1}: Review this question

                        **Correct answer:**
                        {question["answer"]}
                        """
                    )

                    if st.button(
                        "📌 Mark as difficult",
                        key=f"difficult_{index}",
                    ):

                        add_difficult_topic(
                            f"{st.session_state.chapter_title} "
                            f"— Q{index + 1}"
                        )

                        st.success(
                            "Added to difficult topics."
                        )


# =========================================================
# PROGRESS
# =========================================================

elif st.session_state.page == "My Progress":

    st.markdown(
        "## 📈 My Progress"
    )

    history = (
        st.session_state.quiz_history
    )

    total_tests = len(history)

    total_questions = sum(
        item["total"]
        for item in history
    )

    total_correct = sum(
        item["score"]
        for item in history
    )

    average = (
        round(
            total_correct /
            total_questions *
            100
        )
        if total_questions
        else 0
    )

    best = max(
        [
            round(
                item["score"] /
                item["total"] *
                100
            )

            for item in history
            if item["total"]
        ]
        or [0]
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Mock tests",
        total_tests
    )

    c2.metric(
        "Questions",
        total_questions
    )

    c3.metric(
        "Average",
        f"{average}%"
    )

    c4.metric(
        "Best",
        f"{best}%"
    )

    st.markdown(
        "### 📚 Study activity"
    )

    c1, c2 = st.columns(2)

    c1.metric(
        "Study sessions",
        st.session_state.study_sessions
    )

    c2.metric(
        "Exam packs",
        st.session_state.completed_packs
    )

    if history:

        st.markdown(
            "### 🧪 Quiz history"
        )

        for item in reversed(history):

            percentage = round(
                item["score"] /
                item["total"] *
                100
            )

            st.markdown(
                f"""
                <div class="card">

                    <strong>
                        {item["chapter"]}
                    </strong>

                    <br>

                    {item["subject"]}
                    ·
                    {item["date"]}

                    <br>

                    Score:
                    <strong>
                        {item["score"]}/{item["total"]}
                        ({percentage}%)
                    </strong>

                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.info(
            "Take your first mock test to start building progress."
        )

    if st.session_state.difficult_topics:

        st.markdown(
            "### 🔁 Topics to revisit"
        )

        for item in (
            st.session_state.difficult_topics
        ):

            st.markdown(
                f"- {item['topic']} "
                f"({item['subject']})"
            )


# =========================================================
# SAVED & DIFFICULT
# =========================================================

elif st.session_state.page == "Saved & Difficult":

    st.markdown(
        "## 🔖 Saved & Difficult"
    )

    tab1, tab2 = st.tabs(
        [
            "Saved",
            "Difficult Topics",
        ]
    )

    with tab1:

        if not st.session_state.bookmarks:

            st.info(
                "Nothing saved yet."
            )

        else:

            for index, item in enumerate(
                st.session_state.bookmarks
            ):

                with st.expander(
                    f"{item['label']} — "
                    f"{item['subject']}"
                ):

                    st.write(
                        item["content"]
                    )

                    st.caption(
                        item["created_at"]
                    )

                    if st.button(
                        "Remove",
                        key=f"remove_bookmark_{index}",
                    ):

                        st.session_state.bookmarks.pop(
                            index
                        )

                        st.rerun()

    with tab2:

        if not st.session_state.difficult_topics:

            st.info(
                "No difficult topics yet."
            )

        else:

            for index, item in enumerate(
                st.session_state.difficult_topics
            ):

                with st.container(
                    border=True
                ):

                    st.write(
                        f"📌 **{item['topic']}**"
                    )

                    st.caption(
                        f"{item['subject']} · "
                        f"{item['created_at']}"
                    )

                    if st.button(
                        "Remove",
                        key=f"remove_difficult_{index}",
                    ):

                        st.session_state.difficult_topics.pop(
                            index
                        )

                        st.rerun()


# =========================================================
# ABOUT
# =========================================================

elif st.session_state.page == "About V6":

    st.markdown(
        "## ℹ️ About Tamil Study AI V6"
    )

    st.markdown(
        """
### 🎯 Product workflow

**Chapter → Exam Pack → Practice → Recall → Test → Review**

### V6 includes

- No API key required
- No payment system
- Chapter text input
- Text-based PDF input
- Simple Tamil explanation
- English summary
- Key points
- Key terms
- Formula/equation extraction
- 1-mark practice
- 2-mark practice
- 3-mark practice
- 5-mark practice
- Model-answer guidance
- Flashcards
- Chapter-based mock tests
- Quiz history
- Difficult-topic tracking
- Saved study items
- Exam Pack export

### ⚠️ Important limitation

This is intentionally the **no-API version**.

It uses local rule-based processing instead of a cloud AI model.

Therefore, it does **not** claim to predict the real exam or guarantee that a generated question will appear in an exam.

The questions are practice questions generated from the material supplied by the student.

### 🚀 Future upgrades

Later versions can add:

- Secure student accounts
- Cloud-saved progress
- Tamil Nadu syllabus/chapter mapping
- Previous-year question-paper analysis
- Stronger AI generation
- Better Tamil explanations
- Teacher/parent features
- Paid plans

Payments are intentionally **not included in V6**.
"""
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">

        Tamil Study AI V6 ·
        No API key required ·
        No payment system ·
        Chapter-based exam preparation

    </div>
    """,
    unsafe_allow_html=True,
)
