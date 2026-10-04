import streamlit as st
import fitz
import random
import re

# =========================================================
# Tamil Study AI V5.1
# Subject Dashboard + Exam Revision • No API key required
# =========================================================

st.set_page_config(
    page_title="Tamil Study AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------
# CSS
# -------------------------
st.markdown(
    """
    <style>
    .main {
        padding-top: 1rem;
    }

    .hero {
        padding: 2.2rem 2rem;
        border-radius: 24px;
        border: 1px solid rgba(128,128,128,.20);
        margin-bottom: 1.5rem;
    }

    .hero h1 {
        font-size: 3rem;
        margin-bottom: .35rem;
    }

    .hero p {
        font-size: 1.15rem;
        opacity: .82;
        margin-bottom: 0;
    }

    .feature-card {
        padding: 1.2rem;
        border-radius: 18px;
        border: 1px solid rgba(128,128,128,.20);
        min-height: 145px;
        margin-bottom: 1rem;
    }

    .feature-card h3 {
        margin-top: 0;
    }

    .section-title {
        margin-top: 1rem;
        margin-bottom: .5rem;
    }

    .stat-card {
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid rgba(128,128,128,.20);
        text-align: center;
    }

    .stat-number {
        font-size: 1.7rem;
        font-weight: 700;
    }

    .flashcard {
        padding: 1.5rem;
        border-radius: 20px;
        border: 1px solid rgba(128,128,128,.25);
        min-height: 190px;
    }

    .small-muted {
        opacity: .7;
        font-size: .9rem;
    }

    footer {
        visibility: hidden;
    }

    .brand-pill {
        display: inline-block;
        padding: .35rem .75rem;
        border-radius: 999px;
        border: 1px solid rgba(128,128,128,.22);
        font-size: .82rem;
        margin-bottom: .8rem;
    }

    .hero-badge {
        font-size: .9rem;
        font-weight: 600;
        opacity: .78;
        margin-bottom: .6rem;
    }

    .feature-card p {
        line-height: 1.55;
    }

    @media (max-width: 700px) {
        .hero {
            padding: 1.4rem 1.1rem;
            border-radius: 18px;
        }

        .hero h1 {
            font-size: 2.15rem;
        }

        .hero p {
            font-size: 1rem;
        }

        .feature-card {
            min-height: auto;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------
# Session state
# -------------------------
defaults = {
    "quiz_questions": [],
    "quiz_answers": {},
    "quiz_submitted": False,
    "quiz_version": 0,
    "study_text": "",
    "flashcards": [],
    "flashcard_index": 0,
    "flashcard_revealed": False,
    "show_home": True,
    "analysis_done": False,
    "selected_subject": "General",
    "subject_materials": {},
    "revision_topic": "",
    "quiz_history": [],
    "difficult_topics": [],
    "plan": "Free",
    "usage": {
        "study_notes": 0,
        "practice": 0,
        "flashcards": 0,
        "quizzes": 0,
        "revision": 0,
    },
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# Helpers
# =========================================================

def clean_text(text):
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_pdf_text(uploaded_file):
    try:
        data = uploaded_file.read()
        doc = fitz.open(stream=data, filetype="pdf")
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return clean_text("\n".join(pages))
    except Exception as e:
        st.error(f"Could not read PDF: {e}")
        return ""


def detect_subject(text):
    lower = text.lower()

    biology = [
        "photosynthesis", "chlorophyll", "cell", "plant", "biology",
        "respiration", "ecosystem", "mitosis", "dna", "organism"
    ]
    physics = [
        "gravity", "force", "motion", "velocity", "acceleration",
        "energy", "friction", "newton", "physics", "mass"
    ]
    chemistry = [
        "atom", "molecule", "chemical", "element", "reaction",
        "acid", "base", "electron", "proton", "chemistry"
    ]
    history = [
        "king", "empire", "war", "independence", "history",
        "dynasty", "revolution", "chola", "pandya", "mughal"
    ]
    civics = [
        "democracy", "government", "constitution", "citizen",
        "election", "parliament", "rights", "politics"
    ]
    mathematics = [
        "equation", "algebra", "geometry", "triangle", "fraction",
        "percentage", "integer", "mathematics", "math"
    ]
    geography = [
        "climate", "river", "mountain", "soil", "continent",
        "latitude", "longitude", "geography", "rainfall"
    ]

    groups = [
        ("Biology", biology),
        ("Physics", physics),
        ("Chemistry", chemistry),
        ("History", history),
        ("Civics", civics),
        ("Mathematics", mathematics),
        ("Geography", geography),
    ]

    scores = [(name, sum(1 for word in words if word in lower)) for name, words in groups]
    best = max(scores, key=lambda x: x[1])

    return best[0] if best[1] > 0 else "General Studies"


def tamil_explanation(text):
    lower = text.lower()

    if "photosynthesis" in lower:
        return (
            "ஒளிச்சேர்க்கை என்பது பச்சைத் தாவரங்கள் சூரிய ஒளியின் உதவியுடன் "
            "தங்களுக்கு தேவையான உணவை உருவாக்கும் செயல்முறையாகும். "
            "இதில் கார்பன் டைஆக்சைடு மற்றும் நீர் பயன்படுத்தப்படுகின்றன. "
            "குளோரோபில் சூரிய ஒளியை உறிஞ்ச உதவுகிறது. "
            "இதன் மூலம் குளுக்கோஸ் உருவாகிறது; ஆக்சிஜன் துணைப் பொருளாக வெளியிடப்படுகிறது."
        )

    if "atom" in lower:
        return (
            "அணு என்பது ஒரு தனிமத்தின் வேதியியல் பண்புகளைத் தக்க வைத்திருக்கும் "
            "மிகச் சிறிய அலகாகும். அணுவில் புரோட்டான், நியூட்ரான் மற்றும் "
            "எலக்ட்ரான் போன்ற துணை அணுத் துகள்கள் உள்ளன."
        )

    if "gravity" in lower:
        return (
            "ஈர்ப்பு விசை என்பது நிறை கொண்ட பொருட்கள் ஒன்றை ஒன்று ஈர்க்கும் "
            "விசையாகும். பூமியின் ஈர்ப்பு விசை பொருட்களை பூமியின் மையத்தை நோக்கி "
            "இழுக்கிறது. இதனால் பொருட்கள் கீழே விழுகின்றன."
        )

    if "democracy" in lower:
        return (
            "ஜனநாயகம் என்பது மக்கள் தங்கள் பிரதிநிதிகளைத் தேர்ந்தெடுத்து "
            "ஆட்சியில் பங்கேற்கும் ஒரு ஆட்சி முறையாகும். இதில் மக்கள் வாக்குரிமை, "
            "சமத்துவம் மற்றும் பிரதிநிதித்துவம் போன்ற கொள்கைகள் முக்கியமானவை."
        )

    sentences = re.split(r"(?<=[.!?])\s+", text)
    useful = " ".join(sentences[:3])

    if useful:
        return (
            "இந்தப் பகுதியின் எளிய தமிழ் விளக்கம்:\n\n"
            f"இந்தப் பாடப்பகுதி முக்கியமாக **{useful[:500]}** "
            "என்ற கருத்தை விளக்குகிறது. முக்கியமான சொற்கள் மற்றும் கருத்துகளை "
            "தனித்தனியாகப் படித்து, அவற்றை உங்கள் சொந்த வார்த்தைகளில் "
            "சொல்லிப் பார்ப்பது நினைவில் வைத்துக்கொள்ள உதவும்."
        )

    return "பாடக்குறிப்பை உள்ளிடுங்கள். அதைப் பார்த்து எளிய தமிழ் விளக்கத்தை உருவாக்கலாம்."


def extract_key_points(text):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    points = []
    for sentence in sentences:
        if sentence not in points:
            points.append(sentence)

    return points[:7]


def get_vocabulary(text):
    words = re.findall(r"\b[A-Za-z]{4,}\b", text.lower())
    stopwords = {
        "this", "that", "with", "from", "they", "their", "there",
        "which", "about", "using", "have", "been", "into", "also",
        "than", "then", "when", "where", "what", "will", "food",
        "make", "makes", "process", "used"
    }

    result = []
    for word in words:
        if word not in stopwords and word not in result:
            result.append(word)

    meanings = {
        "photosynthesis": "ஒளிச்சேர்க்கை",
        "chlorophyll": "பச்சையம்",
        "sunlight": "சூரிய ஒளி",
        "glucose": "குளுக்கோஸ்",
        "oxygen": "ஆக்சிஜன்",
        "carbon": "கார்பன்",
        "dioxide": "டைஆக்சைடு",
        "water": "நீர்",
        "gravity": "ஈர்ப்பு விசை",
        "atom": "அணு",
        "democracy": "ஜனநாயகம்",
        "government": "அரசாங்கம்",
        "energy": "ஆற்றல்",
        "force": "விசை",
    }

    output = []
    for word in result[:8]:
        output.append((word.title(), meanings.get(word, "பாடத்துடன் தொடர்புடைய முக்கிய சொல்")))

    return output


def make_flashcards(text):
    lower = text.lower()

    if "photosynthesis" in lower:
        return [
            ("What is photosynthesis?", "It is the process by which green plants make food using sunlight."),
            ("What absorbs sunlight?", "Chlorophyll absorbs sunlight."),
            ("What is produced during photosynthesis?", "Glucose is produced and oxygen is released as a by-product."),
            ("What raw materials are used?", "Carbon dioxide and water are used."),
        ]

    if "gravity" in lower:
        return [
            ("What is gravity?", "Gravity is the force of attraction between objects with mass."),
            ("Why do objects fall toward Earth?", "Earth's gravity pulls them toward its center."),
            ("What does gravity depend on?", "It is related to the masses of objects and the distance between them."),
        ]

    if "atom" in lower:
        return [
            ("What is an atom?", "The smallest unit of an element that retains its chemical properties."),
            ("Name three subatomic particles.", "Protons, neutrons, and electrons."),
            ("Where are electrons found?", "They occupy regions around the nucleus."),
        ]

    points = extract_key_points(text)
    cards = []

    for point in points[:5]:
        words = point.split()
        topic = " ".join(words[:6])
        cards.append(
            (
                f"What is the main idea of: {topic}...?",
                point
            )
        )

    return cards


def make_practice_questions(text):
    lower = text.lower()

    if "photosynthesis" in lower:
        return [
            "What is photosynthesis?",
            "What role does chlorophyll play in photosynthesis?",
            "Which substances are used by plants during photosynthesis?",
            "What is produced during photosynthesis?",
            "Why is photosynthesis important for plants?"
        ]

    if "gravity" in lower:
        return [
            "What is gravity?",
            "Why do objects fall toward Earth?",
            "How does gravity affect everyday life?",
            "What happens to an object when gravity acts on it?",
            "Why is gravity important?"
        ]

    if "atom" in lower:
        return [
            "What is an atom?",
            "What are the main subatomic particles?",
            "What is the role of the nucleus?",
            "Where are electrons found?",
            "Why are atoms important in chemistry?"
        ]

    if "democracy" in lower:
        return [
            "What is democracy?",
            "Why is voting important in a democracy?",
            "What is the role of citizens?",
            "What is representative government?",
            "Why are rights important in a democracy?"
        ]

    points = extract_key_points(text)

    questions = []
    for point in points[:5]:
        questions.append(f"Explain this idea in your own words: {point}")

    if not questions:
        questions = [
            "What is the main idea of this lesson?",
            "List two important facts from the lesson.",
            "Which term in the lesson is most important?",
            "Explain one concept from the lesson in your own words.",
            "What would you revise before an exam?"
        ]

    return questions


def build_quiz_questions(text, count):
    lower = text.lower()

    if "photosynthesis" in lower:
        bank = [
            {
                "q": "What is photosynthesis?",
                "options": [
                    "The process by which green plants make food",
                    "The movement of animals",
                    "The breakdown of rocks",
                    "The formation of clouds",
                ],
                "answer": "The process by which green plants make food",
                "explanation": "Green plants use sunlight, carbon dioxide, and water to make food."
            },
            {
                "q": "What absorbs sunlight during photosynthesis?",
                "options": ["Chlorophyll", "Glucose", "Oxygen", "Water"],
                "answer": "Chlorophyll",
                "explanation": "Chlorophyll is the green pigment that absorbs sunlight."
            },
            {
                "q": "Which gas is released as a by-product?",
                "options": ["Oxygen", "Nitrogen", "Hydrogen", "Helium"],
                "answer": "Oxygen",
                "explanation": "Oxygen is released as a by-product of photosynthesis."
            },
            {
                "q": "Which substance is produced as food?",
                "options": ["Glucose", "Nitrogen", "Salt", "Oxygen"],
                "answer": "Glucose",
                "explanation": "Plants produce glucose during photosynthesis."
            },
            {
                "q": "Which combination is needed for photosynthesis?",
                "options": [
                    "Sunlight, carbon dioxide, and water",
                    "Oxygen, salt, and soil",
                    "Nitrogen, oxygen, and glucose",
                    "Only sunlight",
                ],
                "answer": "Sunlight, carbon dioxide, and water",
                "explanation": "These are the main inputs described in the lesson."
            },
            {
                "q": "Why is chlorophyll important?",
                "options": [
                    "It helps absorb sunlight",
                    "It produces soil",
                    "It creates gravity",
                    "It stores oxygen in clouds",
                ],
                "answer": "It helps absorb sunlight",
                "explanation": "Chlorophyll captures sunlight needed for the process."
            },
            {
                "q": "Photosynthesis mainly helps plants to:",
                "options": [
                    "Make their own food",
                    "Move from one place to another",
                    "Produce rocks",
                    "Absorb sound",
                ],
                "answer": "Make their own food",
                "explanation": "Photosynthesis allows green plants to make food."
            },
        ]
    elif "gravity" in lower:
        bank = [
            {
                "q": "What is gravity?",
                "options": [
                    "A force of attraction between masses",
                    "A type of light",
                    "A chemical reaction",
                    "A form of sound",
                ],
                "answer": "A force of attraction between masses",
                "explanation": "Gravity attracts objects that have mass."
            },
            {
                "q": "Why does an object fall toward Earth?",
                "options": [
                    "Earth's gravity pulls it",
                    "The object creates wind",
                    "Sunlight pushes it",
                    "Sound attracts it",
                ],
                "answer": "Earth's gravity pulls it",
                "explanation": "Earth's gravitational attraction pulls objects toward its center."
            },
            {
                "q": "Gravity acts on objects that have:",
                "options": ["Mass", "Only color", "Only sound", "Only temperature"],
                "answer": "Mass",
                "explanation": "Gravity is associated with objects that have mass."
            },
        ]
    elif "atom" in lower:
        bank = [
            {
                "q": "What is an atom?",
                "options": [
                    "A basic unit of an element",
                    "A type of planet",
                    "A kind of plant",
                    "A unit of temperature",
                ],
                "answer": "A basic unit of an element",
                "explanation": "Atoms are the basic units that make up elements."
            },
            {
                "q": "Which particle has a negative charge?",
                "options": ["Electron", "Proton", "Neutron", "Nucleus"],
                "answer": "Electron",
                "explanation": "Electrons have a negative electric charge."
            },
            {
                "q": "Which particles are found in the nucleus?",
                "options": [
                    "Protons and neutrons",
                    "Only electrons",
                    "Only photons",
                    "Only molecules",
                ],
                "answer": "Protons and neutrons",
                "explanation": "The nucleus contains protons and neutrons."
            },
        ]
    else:
        points = extract_key_points(text)
        bank = []

        for i, point in enumerate(points[:7]):
            short = point[:90]
            bank.append(
                {
                    "q": f"Which statement best matches this lesson point: {short}?",
                    "options": [
                        point,
                        "This statement is unrelated to the lesson.",
                        "This is a completely different topic.",
                        "None of the lesson ideas apply.",
                    ],
                    "answer": point,
                    "explanation": "This option matches the information in the provided study text."
                }
            )

    random.shuffle(bank)
    return bank[:min(count, len(bank))]


def reset_quiz():
    st.session_state.quiz_questions = []
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_version += 1


def start_quiz(text, count):
    questions = build_quiz_questions(text, count)
    st.session_state.quiz_questions = questions
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_version += 1


def load_flashcards(text):
    st.session_state.flashcards = make_flashcards(text)
    st.session_state.flashcard_index = 0
    st.session_state.flashcard_revealed = False



# =========================================================
# V5 helpers
# =========================================================

SUBJECTS = [
    "General",
    "Tamil",
    "English",
    "Mathematics",
    "Science",
    "Social Science",
]

SUBJECT_ICONS = {
    "General": "📚",
    "Tamil": "🪷",
    "English": "🔤",
    "Mathematics": "➗",
    "Science": "🔬",
    "Social Science": "🌍",
}


def subject_dashboard_stats():
    materials = st.session_state.subject_materials
    return [
        {
            "subject": subject,
            "words": len(materials.get(subject, "").split()),
            "has_notes": bool(materials.get(subject, "")),
        }
        for subject in SUBJECTS
    ]


def save_to_subject(subject, text):
    if text:
        st.session_state.subject_materials[subject] = text
        st.session_state.selected_subject = subject


def get_current_subject_text():
    return st.session_state.subject_materials.get(
        st.session_state.selected_subject, ""
    )


def make_revision_pack(text):
    return {
        "summary": tamil_explanation(text),
        "points": extract_key_points(text)[:5],
        "practice": make_practice_questions(text)[:5],
        "cards": make_flashcards(text)[:5],
        "checklist": [
            "Read the key points once without looking at the full lesson.",
            "Explain the main idea in your own words.",
            "Review the important vocabulary.",
            "Try the practice questions without checking your notes.",
            "Finish with a short Test Yourself quiz.",
        ],
    }


def record_quiz_result(score, total, subject):
    percentage = int((score / total) * 100) if total else 0
    st.session_state.quiz_history.append({
        "subject": subject,
        "score": score,
        "total": total,
        "percentage": percentage,
    })
    # Keep the most recent 20 attempts so the session stays lightweight.
    st.session_state.quiz_history = st.session_state.quiz_history[-20:]


def progress_stats():
    history = st.session_state.quiz_history
    if not history:
        return {"attempts": 0, "average": 0, "best": 0, "questions": 0}

    percentages = [item["percentage"] for item in history]
    return {
        "attempts": len(history),
        "average": int(sum(percentages) / len(percentages)),
        "best": max(percentages),
        "questions": sum(item["total"] for item in history),
    }


def subject_progress(subject):
    attempts = [
        item for item in st.session_state.quiz_history
        if item["subject"] == subject
    ]
    if not attempts:
        return {"attempts": 0, "average": 0, "best": 0}

    percentages = [item["percentage"] for item in attempts]
    return {
        "attempts": len(attempts),
        "average": int(sum(percentages) / len(percentages)),
        "best": max(percentages),
    }


def add_difficult_topic(topic):
    topic = topic.strip()
    if topic and topic not in st.session_state.difficult_topics:
        st.session_state.difficult_topics.append(topic)


def remove_difficult_topic(topic):
    if topic in st.session_state.difficult_topics:
        st.session_state.difficult_topics.remove(topic)


# =========================================================
# Monetization
# =========================================================

PLAN_LIMITS = {
    "study_notes": 5,
    "practice": 5,
    "flashcards": 5,
    "quizzes": 3,
    "revision": 2,
}

PLAN_LABELS = {
    "study_notes": "Study Notes / analyses",
    "practice": "Practice sets",
    "flashcards": "Flashcard sets",
    "quizzes": "Quizzes",
    "revision": "Exam Revision packs",
}

def is_premium():
    return st.session_state.plan == "Premium"

def can_use(feature):
    if is_premium():
        return True
    return st.session_state.usage.get(feature, 0) < PLAN_LIMITS[feature]

def use_feature(feature):
    if not is_premium():
        st.session_state.usage[feature] = st.session_state.usage.get(feature, 0) + 1

def remaining(feature):
    if is_premium():
        return "Unlimited"
    return max(0, PLAN_LIMITS[feature] - st.session_state.usage.get(feature, 0))

def show_upgrade(feature):
    used = st.session_state.usage.get(feature, 0)
    limit = PLAN_LIMITS[feature]
    st.warning(
        f"⭐ You have reached the Free limit for {PLAN_LABELS[feature]} ({used}/{limit})."
    )
    st.markdown(
        "### ⭐ Upgrade to Premium — ₹49/month\n"
        "Get unlimited study tools, unlimited quizzes, unlimited revision packs, "
        "and unlimited saved study material."
    )
    st.button("🚀 Upgrade to Premium", key=f"upgrade_{feature}", use_container_width=True)
    st.caption("Payment is not connected yet — this button is a preview of the upgrade flow.")

def pricing_ui():
    st.markdown("### 💎 Choose your plan")
    free, premium = st.columns(2)
    with free:
        st.markdown("#### 🆓 Free")
        st.markdown("# ₹0")
        st.caption("Try Tamil Study AI before paying.")
        for feature, limit in PLAN_LIMITS.items():
            st.markdown(f"✓ {limit} {PLAN_LABELS[feature]} / month")
        st.markdown("✓ All subjects")
        st.markdown("✓ Progress tracking")
    with premium:
        st.markdown("#### ⭐ Premium")
        st.markdown("# ₹49 / month")
        st.caption("Unlimited study and revision.")
        st.markdown("✓ Unlimited Study Notes")
        st.markdown("✓ Unlimited Practice Questions")
        st.markdown("✓ Unlimited Flashcards")
        st.markdown("✓ Unlimited Quizzes")
        st.markdown("✓ Unlimited Exam Revision")
        st.markdown("✓ Unlimited saved study material")
        st.markdown("✓ Full progress tracking")
        st.button("🚀 Upgrade to Premium", key="upgrade_pricing", type="primary", use_container_width=True)
        st.caption("Payment coming in the next release.")



# =========================================================
# Sidebar
# =========================================================

with st.sidebar:
    st.markdown("## 📚 Tamil Study AI")
    st.caption("Simple study tools • Tamil-friendly learning")
    st.markdown('<div class="brand-pill">V5.1 • No API required</div>', unsafe_allow_html=True)

    st.divider()

    mode = st.radio(
        "Choose a study mode",
        [
            "🏠 Home",
            "📈 My Progress",
            "💎 Premium",
            "📊 My Subjects",
            "📄 Study Notes",
            "📝 Exam Revision",
            "🃏 Flashcards",
            "✍️ Practice",
            "🎯 Test Yourself",
        ],
        index=0,
    )

    st.divider()
    if is_premium():
        st.success("⭐ Premium plan")
    else:
        st.markdown("**🆓 Free plan**")
        st.caption(f"Notes {remaining("study_notes")} • Quizzes {remaining("quizzes")} left")

    st.divider()
    st.markdown("### 📚 Current subject")

    selected_subject = st.selectbox(
        "Subject",
        SUBJECTS,
        index=SUBJECTS.index(st.session_state.selected_subject),
        label_visibility="collapsed",
    )
    st.session_state.selected_subject = selected_subject

    st.divider()

    if st.session_state.study_text:
        st.success("Study material loaded")
        st.caption(f"{len(st.session_state.study_text.split())} words")

    sidebar_stats = progress_stats()
    st.markdown("### 📈 Progress")
    st.caption(
        f"Quizzes: {sidebar_stats['attempts']} • "
        f"Best: {sidebar_stats['best']}%"
    )

    st.markdown("### Quick guide")
    st.caption("1. Add your notes")
    st.caption("2. Analyze them")
    st.caption("3. Revise with tools")
    st.caption("4. Test yourself")


# =========================================================
# HOME
# =========================================================

if mode == "🏠 Home":
    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">🇮🇳 YOUR SIMPLE STUDY WORKSPACE</div>
            <h1>📚 Tamil Study AI</h1>
            <p>Understand lessons in simple Tamil, revise important ideas, and test yourself — all in one place.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Everything you need for a quick revision session")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            """
            <div class="feature-card">
                <h3>📄 Study Notes</h3>
                <p>Paste a lesson or upload a PDF and turn it into clear revision material with Tamil support.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🃏 Flashcards</h3>
                <p>Review important concepts one card at a time and reveal the answer when you are ready.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🎯 Test Yourself</h3>
                <p>Take a quick multiple-choice quiz, see your score, and review your mistakes.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Why use Tamil Study AI?")

    q1, q2, q3 = st.columns(3)
    with q1:
        st.markdown("**🇮🇳 Tamil-friendly**")
        st.caption("Understand difficult study ideas with simple Tamil explanations.")
    with q2:
        st.markdown("**🔑 Revision focused**")
        st.caption("Key points, vocabulary, flashcards and practice in one workflow.")
    with q3:
        st.markdown("**⚡ Simple & fast**")
        st.caption("No API key or complicated setup is required.")

    st.markdown("---")
    pricing_ui()

    st.markdown("### How it works")

    s1, s2, s3, s4 = st.columns(4)

    steps = [
        ("1", "Add notes", "Paste text or upload a PDF."),
        ("2", "Analyze", "Get Tamil explanations and key points."),
        ("3", "Revise", "Use vocabulary, flashcards and practice."),
        ("4", "Test", "Take a quiz and review your answers."),
    ]

    for col, (num, title, desc) in zip([s1, s2, s3, s4], steps):
        with col:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-number">{num}</div>
                    <b>{title}</b>
                    <p class="small-muted">{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.info("💡 Start with **Study Notes** from the sidebar.")



# =========================================================
# MY PROGRESS
# =========================================================

if mode == "📈 My Progress":
    st.title("📈 My Progress")
    st.write("See how your quiz performance is improving across your subjects.")

    stats = progress_stats()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("📝 Quizzes", stats["attempts"])
    with m2:
        st.metric("📊 Average", f"{stats['average']}%")
    with m3:
        st.metric("🏆 Best Score", f"{stats['best']}%")
    with m4:
        st.metric("❓ Questions", stats["questions"])

    st.markdown("---")
    st.subheader("📚 Subject Progress")

    subject_cols = st.columns(3)
    for i, subject in enumerate(SUBJECTS):
        progress = subject_progress(subject)
        with subject_cols[i % 3]:
            st.markdown(
                f"### {SUBJECT_ICONS[subject]} {subject}"
            )
            if progress["attempts"]:
                st.progress(
                    progress["average"] / 100,
                    text=f"Average: {progress['average']}%"
                )
                st.caption(
                    f"Attempts: {progress['attempts']} • "
                    f"Best: {progress['best']}%"
                )
            else:
                st.caption("No quiz attempts yet.")

    st.markdown("---")
    st.subheader("🧠 Difficult Topics")
    st.caption("Keep topics here that you want to revise again.")

    if st.session_state.difficult_topics:
        for i, topic in enumerate(st.session_state.difficult_topics):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.info(f"📌 {topic}")
            with c2:
                if st.button("Remove", key=f"remove_topic_{i}", use_container_width=True):
                    remove_difficult_topic(topic)
                    st.rerun()
    else:
        st.caption("No difficult topics saved yet.")

    topic_input = st.text_input(
        "Add a difficult topic",
        placeholder="Example: Algebraic equations",
        key="progress_topic_input",
    )
    if st.button("➕ Save Difficult Topic", use_container_width=True):
        if topic_input.strip():
            add_difficult_topic(topic_input)
            st.rerun()
        else:
            st.warning("Enter a topic first.")

    st.markdown("---")
    st.subheader("🕘 Quiz History")

    if not st.session_state.quiz_history:
        st.info("Complete a Test Yourself quiz and your result will appear here.")
    else:
        for number, attempt in enumerate(reversed(st.session_state.quiz_history), 1):
            pct = attempt["percentage"]
            if pct >= 80:
                icon = "🟢"
            elif pct >= 50:
                icon = "🟡"
            else:
                icon = "🔴"

            h1, h2, h3 = st.columns([3, 2, 1])
            with h1:
                st.markdown(
                    f"{icon} **Attempt {number} — "
                    f"{SUBJECT_ICONS.get(attempt['subject'], '📚')} {attempt['subject']}**"
                )
            with h2:
                st.caption(f"Score: {attempt['score']}/{attempt['total']}")
            with h3:
                st.metric("Score", f"{pct}%")


# =========================================================
# PREMIUM
# =========================================================

if mode == "💎 Premium":
    st.title("💎 Tamil Study AI Premium")
    st.write("Study without running into the Free plan limits.")
    pricing_ui()

    st.markdown("---")
    st.subheader("📊 Your Free usage")
    for feature, limit in PLAN_LIMITS.items():
        used = st.session_state.usage.get(feature, 0)
        st.progress(min(used / limit, 1.0), text=f"{PLAN_LABELS[feature]}: {used}/{limit}")

# =========================================================
# MY SUBJECTS
# =========================================================

if mode == "📊 My Subjects":
    st.title("📊 My Subjects")
    st.write("Organize your study material by subject and quickly return to revision.")

    stats = subject_dashboard_stats()
    cols = st.columns(3)

    for i, item in enumerate(stats):
        with cols[i % 3]:
            subject = item["subject"]
            icon = SUBJECT_ICONS[subject]
            status = "Notes saved" if item["has_notes"] else "No notes yet"
            st.markdown(
                f"""
                <div class="feature-card">
                    <h3>{icon} {subject}</h3>
                    <p><b>{item["words"]}</b> words</p>
                    <p class="small-muted">{status}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.subheader("📌 Current subject")

    subject = st.selectbox(
        "Choose a subject to view",
        SUBJECTS,
        index=SUBJECTS.index(st.session_state.selected_subject),
    )
    st.session_state.selected_subject = subject

    subject_text = st.session_state.subject_materials.get(subject, "")

    if subject_text:
        st.success(f"{SUBJECT_ICONS[subject]} {subject} notes are ready.")

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Words", len(subject_text.split()))
        with c2:
            st.metric("Key points", len(extract_key_points(subject_text)))
        with c3:
            st.metric("Practice questions", len(make_practice_questions(subject_text)))

        with st.expander("👀 Preview saved notes"):
            st.write(
                subject_text[:1200]
                + ("..." if len(subject_text) > 1200 else "")
            )

        if st.button(
            "📝 Open Exam Revision",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.study_text = subject_text
            st.session_state.revision_topic = subject
            st.rerun()
    else:
        st.info(
            f"No notes saved for {subject} yet. "
            "Go to Study Notes, choose this subject, and analyze some material."
        )

    st.markdown("### 💡 Suggested workflow")
    st.caption(
        "Choose a subject → add notes → save them → use Exam Revision → finish with a quiz."
    )


# =========================================================
# EXAM REVISION
# =========================================================

elif mode == "📝 Exam Revision":
    st.title("📝 Exam Revision")
    st.write("A focused revision session built from your saved study material.")

    revision_text = get_current_subject_text() or st.session_state.study_text

    if not revision_text:
        st.info("Add and analyze study material first from Study Notes.")
    else:
        if not can_use("revision"):
            show_upgrade("revision")
            st.stop()
        use_feature("revision")
        st.caption(f"Free revision packs remaining: {remaining('revision')}")
        topic_name = st.session_state.selected_subject

        st.markdown(
            f"### 🎯 Revision pack: {SUBJECT_ICONS.get(topic_name, '📚')} {topic_name}"
        )

        pack = make_revision_pack(revision_text)

        st.markdown("#### 🇮🇳 Quick Tamil explanation")
        st.info(pack["summary"])

        st.markdown("#### 🔑 Must-remember points")
        for point in pack["points"]:
            st.markdown(f"- {point}")

        st.markdown("#### 📖 Quick vocabulary")
        vocab = get_vocabulary(revision_text)

        if vocab:
            vc1, vc2 = st.columns(2)
            for i, (word, meaning) in enumerate(vocab):
                with (vc1 if i % 2 == 0 else vc2):
                    st.markdown(f"**{word}** — {meaning}")
        else:
            st.caption("No special vocabulary was detected.")

        st.markdown("#### 🃏 Flashcard review")
        for question, answer in pack["cards"]:
            with st.expander(question):
                st.write(answer)

        st.markdown("#### ✍️ Practice before the exam")
        for i, question in enumerate(pack["practice"], 1):
            st.markdown(f"**{i}. {question}**")

        st.markdown("#### ☑️ Final revision checklist")
        for i, item in enumerate(pack["checklist"]):
            st.checkbox(
                item,
                key=f"revision_{st.session_state.quiz_version}_{i}",
            )

        st.markdown("---")
        st.markdown("### 🎯 Ready for the final check?")
        st.caption(
            "Use Test Yourself from the sidebar to take a quiz on this material."
        )


# =========================================================
# STUDY NOTES
# =========================================================

elif mode == "📄 Study Notes":
    st.title("📄 Study Notes")
    st.write("Turn your lesson into a simple revision dashboard.")

    selected_subject = st.selectbox(
        "Save these notes under",
        SUBJECTS,
        index=SUBJECTS.index(st.session_state.selected_subject),
        key="study_notes_subject",
    )
    st.session_state.selected_subject = selected_subject

    input_method = st.radio(
        "How do you want to add your study material?",
        ["Paste Text", "Upload PDF"],
        horizontal=True,
    )

    text = ""

    if input_method == "Paste Text":
        text = st.text_area(
            "Paste your lesson here",
            height=220,
            placeholder="Example: Photosynthesis is the process by which green plants make their food...",
        )
    else:
        uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
        if uploaded_file:
            text = extract_pdf_text(uploaded_file)
            if text:
                st.success("PDF text extracted successfully.")

    if st.button("✨ Analyze My Notes", type="primary", use_container_width=True):
        text = clean_text(text)

        if not text:
            st.warning("Please add some study material first.")
        elif not can_use("study_notes"):
            show_upgrade("study_notes")
        else:
            use_feature("study_notes")
            st.session_state.study_text = text
            st.session_state.analysis_done = True
            save_to_subject(selected_subject, text)
            load_flashcards(text)
            reset_quiz()
            st.success(
                f"Your study material is ready and saved under "
                f"{SUBJECT_ICONS[selected_subject]} {selected_subject}!"
            )
            st.caption(f"Free analyses remaining: {remaining('study_notes')}")

    if st.session_state.study_text:
        study_text = st.session_state.study_text
        subject = detect_subject(study_text)
        points = extract_key_points(study_text)
        vocab = get_vocabulary(study_text)

        st.markdown("---")
        st.subheader("📊 Study Overview")

        a, b, c = st.columns(3)

        with a:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-number">{subject}</div>
                    <span class="small-muted">Detected subject</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with b:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-number">{len(study_text.split())}</div>
                    <span class="small-muted">Words</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-number">{len(points)}</div>
                    <span class="small-muted">Key points</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### 🇮🇳 தமிழ் விளக்கம்")
        st.info(tamil_explanation(study_text))

        st.markdown("### 🔑 Key Points")
        if points:
            for point in points:
                st.markdown(f"- {point}")
        else:
            st.write("No clear key points found.")

        st.markdown("### 📖 Important Vocabulary")

        if vocab:
            vcols = st.columns(2)
            for i, (word, meaning) in enumerate(vocab):
                with vcols[i % 2]:
                    st.markdown(f"**{word}** — {meaning}")
        else:
            st.write("No vocabulary items found.")

        st.markdown("### 🃏 Quick Flashcards")
        cards = make_flashcards(study_text)

        for question, answer in cards[:4]:
            with st.expander(question):
                st.write(answer)

        st.markdown("### ✍️ Practice Questions")

        for i, question in enumerate(make_practice_questions(study_text), 1):
            st.markdown(f"**{i}. {question}**")
            st.text_input(
                "Your answer",
                key=f"practice_{st.session_state.quiz_version}_{i}",
                label_visibility="collapsed",
                placeholder="Type your answer here...",
            )


# =========================================================
# FLASHCARDS
# =========================================================

elif mode == "🃏 Flashcards":
    st.title("🃏 Flashcards")

    if not st.session_state.study_text:
        st.info("Add and analyze study material first from **Study Notes**.")
    else:
        if not st.session_state.flashcards:
            if not can_use("flashcards"):
                show_upgrade("flashcards")
                st.stop()
            use_feature("flashcards")
            load_flashcards(st.session_state.study_text)
            st.caption(f"Free flashcard sets remaining: {remaining('flashcards')}")

        cards = st.session_state.flashcards

        if not cards:
            st.warning("No flashcards could be created from this material.")
        else:
            index = st.session_state.flashcard_index
            card = cards[index]

            st.caption(f"Card {index + 1} of {len(cards)}")

            st.markdown(
                f"""
                <div class="flashcard">
                    <h2>{card[0]}</h2>
                    <p class="small-muted">Think about your answer before revealing it.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")

            if st.button(
                "👁️ Reveal Answer" if not st.session_state.flashcard_revealed else "🙈 Hide Answer",
                use_container_width=True,
            ):
                st.session_state.flashcard_revealed = not st.session_state.flashcard_revealed

            if st.session_state.flashcard_revealed:
                st.success(card[1])

            p1, p2, p3 = st.columns(3)

            with p1:
                if st.button("⬅️ Previous", use_container_width=True):
                    st.session_state.flashcard_index = (index - 1) % len(cards)
                    st.session_state.flashcard_revealed = False
                    st.rerun()

            with p2:
                if st.button("🔄 Restart", use_container_width=True):
                    st.session_state.flashcard_index = 0
                    st.session_state.flashcard_revealed = False
                    st.rerun()

            with p3:
                if st.button("Next ➡️", use_container_width=True):
                    st.session_state.flashcard_index = (index + 1) % len(cards)
                    st.session_state.flashcard_revealed = False
                    st.rerun()


# =========================================================
# PRACTICE
# =========================================================

elif mode == "✍️ Practice":
    st.title("✍️ Practice Questions")
    st.write("Write answers in your own words to strengthen your understanding.")

    if not st.session_state.study_text:
        st.info("Add and analyze study material first from **Study Notes**.")
    elif not can_use("practice"):
        show_upgrade("practice")
    else:
        questions = make_practice_questions(st.session_state.study_text)
        use_feature("practice")
        st.caption(f"Free practice sets remaining: {remaining('practice')}")

        for i, question in enumerate(questions, 1):
            st.markdown(f"### {i}. {question}")
            st.text_area(
                f"Answer {i}",
                key=f"practice_page_{st.session_state.quiz_version}_{i}",
                height=100,
                placeholder="Write your answer...",
            )

        st.success("Tip: Try answering without looking back at your notes first.")


# =========================================================
# TEST YOURSELF
# =========================================================

elif mode == "🎯 Test Yourself":
    st.title("🎯 Test Yourself")
    st.write("Check what you remember with a quick multiple-choice quiz.")

    if not st.session_state.study_text:
        st.info("Add and analyze study material first from **Study Notes**.")
    else:
        count = st.selectbox(
            "Number of questions",
            [3, 5, 7, 10],
            index=1,
        )

        if not st.session_state.quiz_questions:
            st.markdown(
                """
                **Quiz tips**
                - Read every option carefully.
                - You need to answer every question before submitting.
                - Your score appears after submission.
                """
            )

            if st.button("🚀 Generate Quiz", type="primary", use_container_width=True):
                if not can_use("quizzes"):
                    show_upgrade("quizzes")
                else:
                    use_feature("quizzes")
                    start_quiz(st.session_state.study_text, count)
                    st.rerun()

            st.caption(f"Free quizzes remaining: {remaining('quizzes')}")

        else:
            questions = st.session_state.quiz_questions

            st.progress(
                len(st.session_state.quiz_answers) / max(len(questions), 1),
                text=f"{len(st.session_state.quiz_answers)} / {len(questions)} answered",
            )

            for i, question in enumerate(questions):
                key = f"quiz_{st.session_state.quiz_version}_{i}"

                choice = st.radio(
                    f"**{i + 1}. {question['q']}**",
                    question["options"],
                    index=None,
                    key=key,
                )

                if choice is not None:
                    st.session_state.quiz_answers[i] = choice

            answered = len(st.session_state.quiz_answers)
            all_answered = answered == len(questions)

            st.write("")

            if not st.session_state.quiz_submitted:
                if not all_answered:
                    st.warning(
                        f"Please answer all questions before submitting. "
                        f"{len(questions) - answered} remaining."
                    )

                if st.button(
                    "✅ Submit Quiz",
                    type="primary",
                    disabled=not all_answered,
                    use_container_width=True,
                ):
                    st.session_state.quiz_submitted = True
                    st.rerun()

            if st.session_state.quiz_submitted:
                score = 0

                for i, question in enumerate(questions):
                    if st.session_state.quiz_answers.get(i) == question["answer"]:
                        score += 1

                percentage = int((score / len(questions)) * 100)

                quiz_record_key = f"quiz_recorded_{st.session_state.quiz_version}"
                if not st.session_state.get(quiz_record_key, False):
                    record_quiz_result(
                        score,
                        len(questions),
                        st.session_state.selected_subject,
                    )
                    st.session_state[quiz_record_key] = True

                st.markdown("---")
                st.subheader("🏆 Your Result")

                r1, r2 = st.columns(2)

                with r1:
                    st.metric("Score", f"{score}/{len(questions)}")

                with r2:
                    st.metric("Percentage", f"{percentage}%")

                if percentage >= 80:
                    st.success("Excellent work! 🎉")
                elif percentage >= 50:
                    st.info("Good job! Review the missed questions once more.")
                else:
                    st.warning("Keep practicing. You can improve with another attempt!")

                st.markdown("### 🧠 Mark a topic for extra revision")
                difficult_topic = st.text_input(
                    "Topic to revise",
                    placeholder="Example: Photosynthesis",
                    key=f"difficult_topic_{st.session_state.quiz_version}",
                )
                if st.button(
                    "📌 Save to Difficult Topics",
                    key=f"save_difficult_{st.session_state.quiz_version}",
                    use_container_width=True,
                ):
                    if difficult_topic.strip():
                        add_difficult_topic(difficult_topic)
                        st.success("Saved to My Progress.")
                    else:
                        st.warning("Enter a topic first.")

                st.markdown("### 📋 Answer Review")

                for i, question in enumerate(questions):
                    user_answer = st.session_state.quiz_answers.get(i)
                    correct = user_answer == question["answer"]

                    if correct:
                        st.success(f"**{i + 1}. Correct**")
                    else:
                        st.error(f"**{i + 1}. Incorrect**")

                    st.write(f"**Question:** {question['q']}")
                    st.write(f"Your answer: {user_answer}")
                    st.write(f"Correct answer: {question['answer']}")
                    st.caption(question["explanation"])

                st.write("")

                if st.button("🔄 Try Another Quiz", use_container_width=True):
                    reset_quiz()
                    st.rerun()


# =========================================================
# Footer
# =========================================================

st.markdown("---")
st.caption("📚 Tamil Study AI • Version 5.1 • Free + Premium • No API key required")
