import streamlit as st
from datetime import date, timedelta
import re


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Tamil Study AI — Exam Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 2.7rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        font-size: 1.1rem;
        opacity: 0.75;
        margin-bottom: 1.2rem;
    }

    .hero {
        padding: 1.6rem;
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 20px;
        background: linear-gradient(
            135deg,
            rgba(90,120,255,0.10),
            rgba(0,180,150,0.08)
        );
        margin-bottom: 1.2rem;
    }

    .card {
        padding: 1rem;
        border: 1px solid rgba(128,128,128,0.22);
        border-radius: 16px;
        margin-bottom: 0.8rem;
    }

    .small {
        font-size: 0.88rem;
        opacity: 0.72;
    }

    .weak {
        border-left: 5px solid #d9534f;
        padding-left: 0.8rem;
    }

    .okay {
        border-left: 5px solid #f0ad4e;
        padding-left: 0.8rem;
    }

    .strong {
        border-left: 5px solid #5cb85c;
        padding-left: 0.8rem;
    }

    .mission-card {
        padding: 1.1rem;
        border: 1px solid rgba(128,128,128,0.22);
        border-radius: 16px;
        margin-bottom: 0.8rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# APP CONSTANTS
# ============================================================

SUBJECTS = [
    "Tamil",
    "English",
    "Mathematics",
    "Science",
    "Social Science",
    "Computer Science",
]

CHAPTERS = [
    "Chapter 1",
    "Chapter 2",
    "Chapter 3",
    "Chapter 4",
    "Chapter 5",
    "Chapter 6",
    "Chapter 7",
    "Chapter 8",
]


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "Dashboard",

    "profile": {
        "class": "10",
        "board": "Tamil Nadu State Board",
        "medium": "Tamil Medium",
        "subject": "Science",
        "exam_date": date.today() + timedelta(days=7),
        "daily_minutes": 90,
        "exam_type": "General Revision",
    },

    "chapters": {},
    "scores": [],
    "study_log": [],

    "current_mission": [],
    "mission_date": None,

    "chapter_text": {},
}


for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# SUBJECT DATA
# ============================================================

def ensure_subject(subject):
    if subject not in st.session_state.chapters:

        st.session_state.chapters[subject] = {
            chapter: {
                "status": "Not started",
                "score": None,
                "minutes": 0,
            }
            for chapter in CHAPTERS
        }


for subject_name in SUBJECTS:
    ensure_subject(subject_name)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def days_left():
    exam_date = st.session_state.profile["exam_date"]

    return max(
        0,
        (exam_date - date.today()).days
    )


def get_score(subject, chapter):

    return st.session_state.chapters[subject][chapter]["score"]


def get_status(subject, chapter):

    return st.session_state.chapters[subject][chapter]["status"]


def status_label(score):

    if score is None:
        return "⚪ Not assessed"

    if score < 50:
        return "🔴 Weak"

    if score < 70:
        return "🟡 Needs work"

    if score < 85:
        return "🟢 Good"

    return "⭐ Strong"


def chapter_priority(subject, chapter):

    item = st.session_state.chapters[subject][chapter]

    score = item["score"]
    status = item["status"]

    # No score yet
    if score is None:

        if status == "In progress":
            return 70

        return 55

    # Weakest chapters receive highest priority
    if score < 50:
        return 100

    if score < 70:
        return 80

    if score < 85:
        return 55

    return 25


def overall_score(subject):

    scores = []

    for chapter in CHAPTERS:

        score = get_score(subject, chapter)

        if score is not None:
            scores.append(score)

    if not scores:
        return 0

    return round(
        sum(scores) / len(scores)
    )


def completed_count(subject):

    count = 0

    for chapter in CHAPTERS:

        if get_status(subject, chapter) == "Completed":
            count += 1

    return count


def weak_chapters(subject):

    result = []

    for chapter in CHAPTERS:

        score = get_score(subject, chapter)

        if score is not None and score < 70:
            result.append(chapter)

    return result


def build_mission(subject, minutes):

    ranked_chapters = sorted(
        CHAPTERS,
        key=lambda chapter: chapter_priority(
            subject,
            chapter
        ),
        reverse=True,
    )

    task_blocks = [
        ("Learn / revise", 25),
        ("Focused practice", 25),
        ("Mini test", 20),
        ("Mistake review", 10),
        ("Quick recall", 10),
    ]

    mission = []

    remaining = max(
        30,
        minutes
    )

    for index, (task, block_minutes) in enumerate(task_blocks):

        if remaining <= 0:
            break

        actual_minutes = min(
            block_minutes,
            remaining
        )

        chapter = ranked_chapters[
            index % len(ranked_chapters)
        ]

        mission.append(
            {
                "chapter": chapter,
                "task": task,
                "minutes": actual_minutes,
                "done": False,
            }
        )

        remaining -= actual_minutes

    return mission


def log_study(
    subject,
    chapter,
    minutes,
    task
):

    st.session_state.study_log.append(
        {
            "date": str(date.today()),
            "subject": subject,
            "chapter": chapter,
            "minutes": int(minutes),
            "task": task,
        }
    )


def extract_pdf(uploaded_file):

    try:

        import fitz

        document = fitz.open(
            stream=uploaded_file.read(),
            filetype="pdf"
        )

        pages = []

        for page in document:
            pages.append(
                page.get_text()
            )

        return "\n".join(pages)

    except Exception as error:

        st.error(
            f"Could not read the PDF: {error}"
        )

        return ""


def make_questions(text, count=5):

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.split()) >= 5
    ]

    questions = []

    for sentence in sentences[:count]:

        focus = " ".join(
            sentence.split()[:8]
        ).rstrip(".,;:")

        questions.append(
            f"Explain the main idea of: {focus} ..."
        )

    fallback_questions = [
        "What is the main idea of this chapter?",
        "Write two important points from this chapter.",
        "Explain one important term from this chapter.",
        "Give one example from the chapter.",
        "Write a short answer based on the chapter.",
    ]

    return (
        questions + fallback_questions
    )[:count]


def simple_explanation(text):

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    return sentences[:5]


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🎯 Tamil Study AI")

    st.caption(
        "Exam Coach • No API • No payments"
    )

    page = st.radio(
        "Go to",

        [
            "Dashboard",
            "Exam Setup",
            "My Chapters",
            "Today's Mission",
            "Practice",
            "Mistake Review",
            "Progress",
            "Chapter Material",
            "About",
        ],
    )

    st.session_state.page = page

    st.divider()

    st.markdown("### Your exam")

    profile = st.session_state.profile

    class_options = [
        str(number)
        for number in range(6, 13)
    ]

    profile["class"] = st.selectbox(
        "Class",
        class_options,
        index=class_options.index(
            profile["class"]
        ),
    )

    profile["subject"] = st.selectbox(
        "Subject",
        SUBJECTS,
        index=SUBJECTS.index(
            profile["subject"]
        ),
    )

    profile["exam_date"] = st.date_input(
        "Exam date",
        value=profile["exam_date"],
        min_value=date.today(),
    )

    profile["daily_minutes"] = st.slider(
        "Study time today",
        30,
        240,
        int(profile["daily_minutes"]),
        step=15,
    )

    st.info(
        f"📅 **{days_left()} days** until your exam"
    )


# ============================================================
# CURRENT SUBJECT
# ============================================================

subject = st.session_state.profile["subject"]

ensure_subject(subject)


# ============================================================
# GLOBAL HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🎯 Tamil Study AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Your exam coach — decide what to study next, not just what to read.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "Dashboard":

    st.markdown(
        """
        <div class="hero">

        <h2>Stop wondering what to study next.</h2>

        <p>
        Tell Tamil Study AI your exam date, available study time
        and chapter performance.
        The app turns that information into a focused study mission.
        </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    column1, column2, column3, column4 = st.columns(4)

    column1.metric(
        "Days left",
        days_left(),
    )

    preparation = overall_score(subject)

    column2.metric(
        "Preparation",
        f"{preparation}%"
        if preparation
        else "Not assessed",
    )

    column3.metric(
        "Completed",
        f"{completed_count(subject)}/{len(CHAPTERS)}",
    )

    total_study_minutes = sum(
        item["minutes"]
        for item in st.session_state.study_log
    )

    column4.metric(
        "Study minutes",
        total_study_minutes,
    )

    st.subheader(
        "🔥 What needs attention?"
    )

    weak = weak_chapters(subject)

    if weak:

        for chapter in weak[:3]:

            score = get_score(
                subject,
                chapter
            )

            st.markdown(
                f"""
                <div class="card weak">

                <b>🔴 {chapter}</b>

                <br>

                Latest score: {score}%

                <br>

                <span class="small">
                Give this chapter priority in your next session.
                </span>

                </div>
                """,
                unsafe_allow_html=True,
            )

    else:

        st.info(
            "No assessed weak chapters yet. "
            "Enter chapter scores in My Chapters."
        )

    st.subheader(
        "🚀 Start here"
    )

    button1, button2, button3 = st.columns(3)

    if button1.button(
        "🧭 Build today's mission",
        use_container_width=True,
    ):

        st.session_state.current_mission = build_mission(
            subject,
            profile["daily_minutes"],
        )

        st.session_state.mission_date = str(
            date.today()
        )

        st.session_state.page = "Today's Mission"

        st.rerun()

    if button2.button(
        "📚 Set up chapters",
        use_container_width=True,
    ):

        st.session_state.page = "My Chapters"

        st.rerun()

    if button3.button(
        "📖 Add chapter material",
        use_container_width=True,
    ):

        st.session_state.page = "Chapter Material"

        st.rerun()

    st.caption(
        "No-API note: the planning engine uses your entered "
        "scores, completion status and study time. "
        "It does not predict exam questions."
    )


# ============================================================
# EXAM SETUP
# ============================================================

elif page == "Exam Setup":

    st.header(
        "⚙️ Exam Setup"
    )

    st.write(
        "Set the information the coach uses to build your study plan."
    )

    board_options = [
        "Tamil Nadu State Board",
        "CBSE",
        "Other",
    ]

    medium_options = [
        "Tamil Medium",
        "English Medium",
        "Bilingual",
    ]

    exam_options = [
        "Unit Test",
        "Quarterly",
        "Half-Yearly",
        "Annual",
        "General Revision",
    ]

    with st.form("exam_setup_form"):

        board = st.selectbox(
            "Board",
            board_options,
            index=board_options.index(
                profile.get(
                    "board",
                    "Tamil Nadu State Board"
                )
            ),
        )

        medium = st.selectbox(
            "Medium",
            medium_options,
            index=medium_options.index(
                profile.get(
                    "medium",
                    "Tamil Medium"
                )
            ),
        )

        exam_type = st.selectbox(
            "Exam goal",
            exam_options,
            index=exam_options.index(
                profile.get(
                    "exam_type",
                    "General Revision"
                )
            ),
        )

        exam_date = st.date_input(
            "Exam date",
            value=profile["exam_date"],
            min_value=date.today(),
        )

        minutes = st.slider(
            "Typical daily study time",
            30,
            240,
            int(profile["daily_minutes"]),
            step=15,
        )

        submitted = st.form_submit_button(
            "Save exam plan"
        )

    if submitted:

        profile.update(
            {
                "board": board,
                "medium": medium,
                "exam_type": exam_type,
                "exam_date": exam_date,
                "daily_minutes": minutes,
            }
        )

        st.success(
            "Exam plan saved."
        )


# ============================================================
# MY CHAPTERS
# ============================================================

elif page == "My Chapters":

    st.header(
        f"📚 {subject} — My Chapters"
    )

    st.write(
        "Set each chapter's status and latest test/practice score."
    )

    for chapter in CHAPTERS:

        item = st.session_state.chapters[
            subject
        ][chapter]

        with st.container(border=True):

            left, middle, right = st.columns(
                [2, 2, 1]
            )

            left.markdown(
                f"### {chapter}"
            )

            status_options = [
                "Not started",
                "In progress",
                "Completed",
            ]

            new_status = middle.selectbox(
                "Status",
                status_options,
                index=status_options.index(
                    item["status"]
                ),
                key=f"status_{subject}_{chapter}",
            )

            current_score = (
                0
                if item["score"] is None
                else int(item["score"])
            )

            new_score = right.number_input(
                "Score %",
                min_value=0,
                max_value=100,
                value=current_score,
                key=f"score_{subject}_{chapter}",
            )

            item["status"] = new_status

            if (
                new_score > 0
                or new_status == "Completed"
            ):
                item["score"] = new_score

            if item["score"] is not None:

                st.caption(
                    f"{status_label(item['score'])} "
                    f"• {item['score']}%"
                )

    if st.button(
        "🧭 Rebuild today's mission"
    ):

        st.session_state.current_mission = build_mission(
            subject,
            profile["daily_minutes"],
        )

        st.session_state.mission_date = str(
            date.today()
        )

        st.success(
            "Mission rebuilt from your current chapter data."
        )


# ============================================================
# TODAY'S MISSION
# ============================================================

elif page == "Today's Mission":

    st.header(
        "🎯 Today's Mission"
    )

    st.caption(
        f"{subject} • "
        f"{profile['daily_minutes']} minutes • "
        f"{days_left()} days until exam"
    )

    if (
        not st.session_state.current_mission
        or st.session_state.mission_date
        != str(date.today())
    ):

        st.session_state.current_mission = build_mission(
            subject,
            profile["daily_minutes"],
        )

        st.session_state.mission_date = str(
            date.today()
        )

    mission = st.session_state.current_mission

    completed = sum(
        item["done"]
        for item in mission
    )

    total = len(mission)

    st.progress(
        completed / total
        if total
        else 0
    )

    st.write(
        f"**{completed}/{total} tasks completed**"
    )

    for index, task in enumerate(mission):

        with st.container(border=True):

            left, middle, right = st.columns(
                [3, 1, 1]
            )

            icon = (
                "✅"
                if task["done"]
                else "⬜"
            )

            left.markdown(
                f"### {icon} {task['task']}"
            )

            left.write(
                f"**{task['chapter']}**"
            )

            middle.metric(
                "Time",
                f"{task['minutes']} min",
            )

            button_text = (
                "Undo"
                if task["done"]
                else "Complete"
            )

            if right.button(
                button_text,
                key=f"mission_task_{index}",
            ):

                task["done"] = not task["done"]

                if task["done"]:

                    log_study(
                        subject,
                        task["chapter"],
                        task["minutes"],
                        task["task"],
                    )

                st.rerun()

    if total and completed == total:

        st.success(
            "🎉 Today's mission is complete!"
        )

        st.write(
            "Your next session should focus on "
            "the chapter with the lowest score."
        )


# ============================================================
# PRACTICE
# ============================================================

elif page == "Practice":

    st.header(
        "📝 Practice"
    )

    st.write(
        "Use your chapter material to create simple practice prompts "
        "and record your result."
    )

    selected_chapter = st.selectbox(
        "Chapter",
        CHAPTERS,
    )

    text = st.session_state.chapter_text.get(
        (subject, selected_chapter),
        "",
    )

    if not text:

        st.info(
            "No material saved for this chapter yet. "
            "Add it in Chapter Material."
        )

    else:

        questions = make_questions(
            text,
            5,
        )

        st.subheader(
            "Practice set"
        )

        for index, question in enumerate(
            questions,
            start=1,
        ):

            st.markdown(
                f"**{index}. {question}**"
            )

            st.text_area(
                "Your answer",
                key=f"practice_{subject}_{selected_chapter}_{index}",
            )

        correct = st.slider(
            "How many did you answer correctly?",
            0,
            len(questions),
            0,
        )

        if st.button(
            "Save practice result"
        ):

            percentage = round(
                correct
                / len(questions)
                * 100
            )

            st.session_state.chapters[
                subject
            ][selected_chapter]["score"] = percentage

            st.session_state.chapters[
                subject
            ][selected_chapter]["status"] = (
                "Completed"
                if percentage >= 70
                else "In progress"
            )

            st.session_state.scores.append(
                {
                    "date": str(date.today()),
                    "subject": subject,
                    "chapter": selected_chapter,
                    "score": percentage,
                }
            )

            st.success(
                f"Saved {percentage}%. "
                f"{status_label(percentage)}"
            )


# ============================================================
# MISTAKE REVIEW
# ============================================================

elif page == "Mistake Review":

    st.header(
        "🔎 Mistake Review"
    )

    results = sorted(
        [
            (
                chapter,
                get_score(subject, chapter)
            )
            for chapter in CHAPTERS
            if get_score(subject, chapter) is not None
        ],
        key=lambda item: item[1],
    )

    if not results:

        st.info(
            "Complete a practice set or enter a test score first."
        )

    else:

        st.write(
            "Your chapters are ordered from lowest current score "
            "to highest."
        )

        for chapter, score in results:

            if score < 50:

                css_class = "weak"
                next_action = (
                    "relearn + practice"
                )

            elif score < 70:

                css_class = "okay"
                next_action = (
                    "practice + recall"
                )

            else:

                css_class = "strong"
                next_action = (
                    "quick revision"
                )

            st.markdown(
                f"""
                <div class="card {css_class}">

                <b>{chapter}</b> — {score}%

                <br>

                <span class="small">
                Recommended next step: {next_action}
                </span>

                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# PROGRESS
# ============================================================

elif page == "Progress":

    st.header(
        "📈 My Progress"
    )

    column1, column2, column3 = st.columns(3)

    preparation = overall_score(subject)

    column1.metric(
        "Preparation",
        f"{preparation}%"
        if preparation
        else "Not assessed",
    )

    column2.metric(
        "Weak chapters",
        len(weak_chapters(subject)),
    )

    column3.metric(
        "Study sessions",
        len(st.session_state.study_log),
    )

    st.subheader(
        "Chapter map"
    )

    for chapter in CHAPTERS:

        score = get_score(
            subject,
            chapter
        )

        text = (
            f"**{chapter}** — "
            f"{status_label(score)}"
        )

        if score is not None:
            text += f" — {score}%"

        st.write(text)

    if st.session_state.scores:

        st.subheader(
            "Recent results"
        )

        for result in reversed(
            st.session_state.scores[-10:]
        ):

            st.write(
                f"{result['date']} • "
                f"{result['chapter']} • "
                f"{result['score']}%"
            )


# ============================================================
# CHAPTER MATERIAL
# ============================================================

elif page == "Chapter Material":

    st.header(
        "📖 Chapter Material"
    )

    st.write(
        "Paste notes or upload a PDF. "
        "Material is kept for the current app session."
    )

    selected_chapter = st.selectbox(
        "Chapter",
        CHAPTERS,
    )

    uploaded_file = st.file_uploader(
        "Upload chapter PDF",
        type=["pdf"],
    )

    pasted_text = st.text_area(
        "Or paste chapter text",
        height=220,
        value=st.session_state.chapter_text.get(
            (subject, selected_chapter),
            "",
        ),
    )

    if st.button(
        "Save chapter material"
    ):

        text = pasted_text.strip()

        if uploaded_file is not None:

            extracted_text = extract_pdf(
                uploaded_file
            )

            if extracted_text.strip():

                text = extracted_text

        if text:

            st.session_state.chapter_text[
                (subject, selected_chapter)
            ] = text

            st.session_state.chapters[
                subject
            ][selected_chapter]["status"] = (
                "In progress"
            )

            st.success(
                f"Saved material for {selected_chapter}."
            )

        else:

            st.warning(
                "Add text or upload a readable PDF."
            )

    current_text = st.session_state.chapter_text.get(
        (subject, selected_chapter),
        "",
    )

    if current_text:

        st.subheader(
            "Quick understanding"
        )

        for sentence in simple_explanation(
            current_text
        ):

            st.write(
                "• " + sentence
            )

        st.subheader(
            "Practice prompts"
        )

        for question in make_questions(
            current_text,
            5,
        ):

            st.write(
                "• " + question
            )


# ============================================================
# ABOUT
# ============================================================

elif page == "About":

    st.header(
        "ℹ️ About Tamil Study AI"
    )

    st.markdown(
        """
        ### 🎯 Tamil Study AI — Exam Coach V6

        The core idea is simple:

        **Help a student decide what to study next.**

        The coach uses:

        - exam countdown
        - available study time
        - chapter completion
        - recent scores
        - weak-chapter priority
        - completed study sessions

        ### Why this version is different

        This isn't designed to be another giant collection of
        notes, flashcards and quizzes.

        The main workflow is:

        **Exam → Chapters → Performance → Priority → Today's Mission → Progress**

        ### Important

        This is a **no-API version**.

        The planning engine is rule-based, so it should not be
        presented as a full AI tutor or as a predictor of exam questions.

        This version also does not permanently store student data.
        Streamlit Session State is tied to the current browser session,
        so a refresh/reconnection can reset the session data.

        A future production version can add a database and accounts.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Tamil Study AI V6 • Exam Coach • No API • No payments"
)
