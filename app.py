import io
import re
from collections import Counter

import streamlit as st

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image
except ImportError:
    Image = None


# ============================================================
# Tamil Study AI — Version 2
# API-free study assistant
# ============================================================

st.set_page_config(
    page_title="Tamil Study AI",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_NAME = "Tamil Study AI"
MAX_UPLOAD_MB = 20
MAX_PDF_PAGES = 30
MAX_TEXT_CHARS = 50000


# ------------------------------------------------------------
# Built-in vocabulary
# ------------------------------------------------------------
TERMS = {
    "photosynthesis": ("ஒளிச்சேர்க்கை", "தாவரங்கள் சூரிய ஒளியைப் பயன்படுத்தி உணவைத் தயாரிக்கும் செயல்முறை"),
    "chlorophyll": ("பச்சையம்", "சூரிய ஒளியை உறிஞ்ச உதவும் பச்சை நிறமி"),
    "carbon dioxide": ("கார்பன் டை ஆக்சைடு", "தாவரங்கள் ஒளிச்சேர்க்கையில் பயன்படுத்தும் வாயு"),
    "oxygen": ("ஆக்சிஜன் / பிராணவாயு", "உயிரினங்கள் சுவாசத்திற்கு பயன்படுத்தும் வாயு"),
    "glucose": ("குளுக்கோஸ்", "தாவரங்கள் உருவாக்கும் ஒரு சர்க்கரை / உணவுப் பொருள்"),
    "respiration": ("சுவாசம்", "உணவில் இருந்து ஆற்றலைப் பெறும் செயல்முறை"),
    "cell": ("உயிரணு", "உயிரினங்களின் அடிப்படை அமைப்பு மற்றும் செயல்பாட்டு அலகு"),
    "nucleus": ("உட்கரு", "உயிரணுவின் முக்கிய கட்டுப்பாட்டு பகுதி"),
    "force": ("விசை", "ஒரு பொருளின் இயக்கத்தை மாற்றக்கூடிய தள்ளுதல் அல்லது இழுத்தல்"),
    "motion": ("இயக்கம்", "ஒரு பொருள் தனது நிலையை மாற்றுவது"),
    "velocity": ("திசைவேகம்", "திசையுடன் கூடிய வேகம்"),
    "acceleration": ("முடுக்கம்", "திசைவேகத்தில் ஏற்படும் மாற்றம்"),
    "gravity": ("ஈர்ப்பு விசை", "பொருட்களை ஒன்றை ஒன்று நோக்கி இழுக்கும் விசை"),
    "mass": ("நிறை", "ஒரு பொருளில் உள்ள பொருளின் அளவு"),
    "atom": ("அணு", "ஒரு தனிமத்தின் மிகச் சிறிய அடிப்படை அலகு"),
    "molecule": ("மூலக்கூறு", "இரண்டு அல்லது அதற்கு மேற்பட்ட அணுக்கள் இணைந்த அமைப்பு"),
    "acid": ("அமிலம்", "அமிலத் தன்மை கொண்ட பொருள்"),
    "base": ("காரம்", "காரத் தன்மை கொண்ட பொருள்"),
    "reaction": ("வினை", "பொருட்களில் மாற்றம் ஏற்படும் செயல்முறை"),
    "temperature": ("வெப்பநிலை", "ஒரு பொருள் எவ்வளவு சூடாக அல்லது குளிராக உள்ளது என்பதைக் காட்டும் அளவு"),
    "electricity": ("மின்சாரம்", "மின்னூட்டங்களின் இயக்கத்துடன் தொடர்புடைய ஆற்றல்"),
    "current": ("மின்னோட்டம்", "மின்னூட்டத்தின் ஓட்டம்"),
    "voltage": ("மின்னழுத்தம்", "மின்னோட்டத்தை இயக்கும் மின்னழுத்த வேறுபாடு"),
    "resistance": ("மின்தடை", "மின்னோட்ட ஓட்டத்தை எதிர்க்கும் தன்மை"),
    "ecosystem": ("சூழலமைப்பு", "உயிரினங்களும் அவற்றின் சூழலும் இணைந்து செயல்படும் அமைப்பு"),
    "environment": ("சுற்றுச்சூழல்", "உயிரினங்களைச் சுற்றியுள்ள இயற்கை மற்றும் பிற காரணிகள்"),
    "organism": ("உயிரினம்", "உயிருடன் செயல்படும் ஒரு தனி உயிர் அலகு"),
    "plant": ("தாவரம்", "பொதுவாக ஒளிச்சேர்க்கை மூலம் உணவைத் தயாரிக்கும் உயிரினம்"),
    "animal": ("விலங்கு", "தனக்குத் தேவையான உணவை வெளிப்புற மூலங்களிலிருந்து பெறும் உயிரினம்"),
    "democracy": ("மக்களாட்சி", "மக்கள் பங்கேற்புடன் நடைபெறும் ஆட்சி முறை"),
    "government": ("அரசாங்கம்", "ஒரு நாட்டை அல்லது பகுதியை நிர்வகிக்கும் அமைப்பு"),
    "constitution": ("அரசியலமைப்பு", "ஒரு நாட்டின் ஆட்சி அமைப்பு மற்றும் அடிப்படை விதிகளை வகுக்கும் ஆவணம்"),
    "history": ("வரலாறு", "கடந்த கால நிகழ்வுகளைப் பற்றிய படிப்பு"),
    "geography": ("புவியியல்", "பூமி, இடங்கள், நிலப்பரப்பு மற்றும் மனிதச் செயல்பாடுகளைப் பற்றிய படிப்பு"),
    "economics": ("பொருளாதாரம்", "வளங்கள், உற்பத்தி, பகிர்வு மற்றும் பயன்பாட்டைப் பற்றிய படிப்பு"),
    "biology": ("உயிரியல்", "உயிரினங்களைப் பற்றிய அறிவியல்"),
    "physics": ("இயற்பியல்", "பொருள், ஆற்றல், இயக்கம் மற்றும் இயற்கை விதிகளைப் பற்றிய அறிவியல்"),
    "chemistry": ("வேதியியல்", "பொருட்களின் பண்புகள் மற்றும் அவற்றின் மாற்றங்களைப் பற்றிய அறிவியல்"),
    "mathematics": ("கணிதம்", "எண்கள், அளவுகள், வடிவங்கள் மற்றும் தொடர்புகளைப் பற்றிய படிப்பு"),
}


# ------------------------------------------------------------
# Input helpers
# ------------------------------------------------------------
def clean_text(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate_text(text, limit=MAX_TEXT_CHARS):
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n\n[மேலும் உள்ளடக்கம் நீளமாக இருப்பதால் இங்கே நிறுத்தப்பட்டுள்ளது.]"


def split_sentences(text):
    text = clean_text(text)
    # Handle English and Tamil punctuation plus line breaks.
    parts = re.split(r"(?<=[.!?।])\s+|\n+", text)
    return [p.strip(" •-\t") for p in parts if p.strip(" •-\t")]


def extract_pdf_text(uploaded):
    if fitz is None:
        raise RuntimeError("PDF support requires PyMuPDF in requirements.txt.")

    data = uploaded.getvalue()

    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"Please upload a file smaller than {MAX_UPLOAD_MB} MB.")

    doc = fitz.open(stream=data, filetype="pdf")
    try:
        page_count = len(doc)
        if page_count == 0:
            raise ValueError("இந்த PDF-ல் பக்கங்கள் இல்லை.")

        pages = min(page_count, MAX_PDF_PAGES)
        text = "\n\n".join(
            doc.load_page(i).get_text("text") for i in range(pages)
        )
        text = clean_text(text)

        if not text:
            raise ValueError(
                "இந்த PDF-ல் படிக்கக்கூடிய text கிடைக்கவில்லை. "
                "Scanned PDF என்றால் text-ஐ paste செய்யவும்."
            )

        if page_count > MAX_PDF_PAGES:
            text += f"\n\n[முதல் {MAX_PDF_PAGES} பக்கங்கள் மட்டும் பயன்படுத்தப்பட்டுள்ளன.]"

        return truncate_text(text), page_count
    finally:
        doc.close()


def read_image(uploaded):
    if Image is None:
        raise RuntimeError("Image support requires Pillow in requirements.txt.")

    data = uploaded.getvalue()

    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"Please upload an image smaller than {MAX_UPLOAD_MB} MB.")

    try:
        image = Image.open(io.BytesIO(data))
        image.load()
        return image.copy()
    except Exception as exc:
        raise ValueError("இந்த image-ஐ திறக்க முடியவில்லை.") from exc


# ------------------------------------------------------------
# Study understanding helpers
# ------------------------------------------------------------
def find_terms(text):
    lower = text.lower()
    found = []

    # Long phrases first.
    for english, (tamil, meaning) in sorted(
        TERMS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if re.search(r"(?<![A-Za-z])" + re.escape(english) + r"(?![A-Za-z])", lower):
            found.append((english.title(), tamil, meaning))

    return found


def detect_subject(text):
    lower = text.lower()

    scores = {
        "🔬 அறிவியல்": sum(
            lower.count(x)
            for x in (
                "photosynthesis", "chlorophyll", "cell", "oxygen",
                "carbon dioxide", "atom", "molecule", "reaction",
                "force", "motion", "gravity", "biology", "physics", "chemistry"
            )
        ),
        "➗ கணிதம்": sum(
            lower.count(x)
            for x in ("mathematics", "equation", "algebra", "geometry", "calculate")
        ),
        "🌍 புவியியல்": sum(
            lower.count(x)
            for x in ("geography", "climate", "river", "mountain", "earth", "soil")
        ),
        "🏛️ சமூக அறிவியல்": sum(
            lower.count(x)
            for x in ("democracy", "government", "constitution", "history", "economics")
        ),
    }

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "📚 பொதுப் பாடம்"


def translate_sentence(sentence):
    """
    API-free translation layer.

    It intentionally does not pretend to translate arbitrary English.
    It handles common educational sentence patterns and known terms.
    For unsupported sentences it preserves the original sentence and
    explains that the sentence could not be automatically translated.
    """
    s = sentence.strip()
    lower = s.lower().rstrip(".")

    # High-quality built-in explanations for the example/topic that the app
    # is designed to demonstrate.
    if "photosynthesis" in lower:
        if "process" in lower and "green plants" in lower:
            return (
                "பச்சைத் தாவரங்கள் சூரிய ஒளி, கார்பன் டை ஆக்சைடு மற்றும் "
                "நீரைப் பயன்படுத்தி தங்களுக்குத் தேவையான உணவைத் தயாரிக்கும் "
                "செயல்முறையே ஒளிச்சேர்க்கை."
            )
        if "make their own food" in lower:
            return "ஒளிச்சேர்க்கையின் மூலம் பச்சைத் தாவரங்கள் தங்களுக்குத் தேவையான உணவைத் தயாரிக்கின்றன."

    if "chlorophyll" in lower and ("absorb" in lower or "sunlight" in lower):
        return "பச்சையம் தாவரங்களுக்கு சூரிய ஒளியை உறிஞ்ச உதவுகிறது."

    if "oxygen" in lower and "released" in lower:
        return "இந்த செயல்முறையின் போது ஆக்சிஜன் வெளியிடப்படுகிறது."

    # Common simple patterns.
    patterns = [
        (
            r"^(.+?) is the process by which (.+)$",
            lambda m: f"{m.group(1).strip().title()} என்பது {m.group(2).strip()} நடைபெறும் செயல்முறை."
        ),
        (
            r"^(.+?) helps (.+)$",
            lambda m: f"{lookup_term(m.group(1))} {m.group(2).strip()} உதவுகிறது."
        ),
        (
            r"^(.+?) is used for (.+)$",
            lambda m: f"{lookup_term(m.group(1))} என்பது {m.group(2).strip()} பயன்படுகிறது."
        ),
    ]

    for pattern, builder in patterns:
        match = re.match(pattern, lower)
        if match:
            try:
                return builder(match)
            except Exception:
                pass

    # If the sentence is already Tamil, keep it.
    tamil_chars = len(re.findall(r"[\u0B80-\u0BFF]", s))
    latin_chars = len(re.findall(r"[A-Za-z]", s))

    if tamil_chars > latin_chars:
        return s

    # Replace known technical terms while retaining the original meaning.
    converted = s
    replacements = sorted(
        TERMS.items(), key=lambda item: len(item[0]), reverse=True
    )

    changed = False
    for english, (tamil, _) in replacements:
        pattern = re.compile(r"(?<![A-Za-z])" + re.escape(english) + r"(?![A-Za-z])", re.I)
        new = pattern.sub(tamil, converted)
        if new != converted:
            changed = True
            converted = new

    if changed:
        return converted

    return (
        f"**மொழிபெயர்ப்பு தேவை:** {s}\n\n"
        "இந்த வாக்கியத்திற்கு API இல்லாமல் நம்பகமான தானியங்கி தமிழ் "
        "மொழிபெயர்ப்பை உருவாக்க முடியவில்லை."
    )


def lookup_term(word):
    key = word.strip().lower()
    for english, (tamil, _) in TERMS.items():
        if english == key:
            return tamil
    return word.strip()


def build_explanation(text):
    sentences = split_sentences(text)

    if not sentences:
        return "விளக்கம் உருவாக்க போதுமான study material இல்லை."

    subject = detect_subject(text)
    terms = find_terms(text)

    out = [
        "## 📖 எளிய தமிழ் விளக்கம்",
        "",
        f"**பாட வகை:** {subject}",
        "",
        "### 💡 முதலில் புரிந்துகொள்ள வேண்டியது",
        "",
    ]

    # First sentence as the core idea.
    core = translate_sentence(sentences[0])
    out.append(core)
    out.append("")

    if len(sentences) > 1:
        out.append("### 🔎 முக்கிய கருத்துகள்")
        out.append("")

        for sentence in sentences[1:9]:
            translated = translate_sentence(sentence)
            out.append(f"- {translated}")

        out.append("")

    if terms:
        out.extend(["### 📌 முக்கிய சொற்கள்", ""])
        for english, tamil, meaning in terms[:10]:
            out.append(f"- **{english}** → **{tamil}**")
            out.append(f"  - {meaning}")

        out.append("")

    out.extend(
        [
            "### 🧠 ஒரு வரியில் நினைவில் வைத்துக்கொள்ளுங்கள்",
            "",
            build_one_line_summary(text),
            "",
            "> ⚠️ இது API இல்லாத பதிப்பு. ஆதரிக்கப்படாத தகவலை நான் உருவாக்கவில்லை. "
            "முக்கியமான பாடத் தகவல்களை textbook அல்லது ஆசிரியரிடம் சரிபார்க்கவும்.",
        ]
    )

    return "\n".join(out)


def build_one_line_summary(text):
    lower = text.lower()

    if "photosynthesis" in lower:
        return (
            "**ஒளிச்சேர்க்கை = சூரிய ஒளி + கார்பன் டை ஆக்சைடு + நீர் "
            "→ தாவர உணவு + ஆக்சிஜன்.**"
        )

    sentences = split_sentences(text)
    if sentences:
        return translate_sentence(sentences[0])

    return "கொடுக்கப்பட்ட material-ன் முக்கிய கருத்தை மேலே உள்ள குறிப்புகளில் பார்க்கலாம்."


def build_key_points(text):
    sentences = split_sentences(text)
    terms = find_terms(text)

    if not sentences:
        return "முக்கிய குறிப்புகள் உருவாக்க text இல்லை."

    # Preserve source order instead of randomly ranking sentences.
    selected = sentences[:10]

    out = [
        "## 🧠 முக்கிய குறிப்புகள்",
        "",
    ]

    for sentence in selected:
        out.append(f"- {translate_sentence(sentence)}")

    if terms:
        out.extend(["", "## 📌 முக்கிய சொற்கள்", ""])
        for english, tamil, meaning in terms[:10]:
            out.append(f"- **{english}** — **{tamil}**")

    out.extend(
        [
            "",
            "## ⚡ 30-வினாடி Revision",
            "",
            build_one_line_summary(text),
        ]
    )

    return "\n".join(out)


def build_questions(text):
    sentences = split_sentences(text)
    if not sentences:
        return "கேள்விகள் உருவாக்க போதுமான material இல்லை."

    terms = find_terms(text)
    out = [
        "## ❓ Practice Questions",
        "",
        "### ✍️ Short Answer",
        "",
    ]

    for i, sentence in enumerate(sentences[:5], 1):
        out.append(f"**{i}.** இந்தக் கருத்தை உங்கள் சொந்த வார்த்தைகளில் விளக்குக.")
        out.append(f"**Model answer:** {translate_sentence(sentence)}")
        out.append("")

    if terms:
        out.extend(["### 📌 முக்கிய சொற்கள் — நினைவுப் பயிற்சி", ""])
        for i, (english, tamil, _) in enumerate(terms[:5], 1):
            out.append(f"**{i}.** `{english}` என்பதன் தமிழ் பொருள் என்ன?")
            out.append(f"**Answer:** {tamil}")
            out.append("")

    out.extend(
        [
            "### 🧠 Quick Revision Challenge",
            "",
            "1. இந்தப் பாடத்தின் முக்கிய கருத்தை ஒரு வாக்கியத்தில் எழுதுக.",
            "2. இரண்டு முக்கிய சொற்களைத் தேர்ந்தெடுத்து அவற்றின் பொருளை எழுதுக.",
            "3. Material-ல் கூறப்பட்டுள்ள ஒரு முக்கிய தகவலை நினைவிலிருந்து எழுதுக.",
            "",
            "_குறிப்பு: இவை revision questions. இவை தேர்வில் நிச்சயம் வரும் என்று பொருள் அல்ல._",
        ]
    )

    return "\n".join(out)


def make_flashcards(text):
    terms = find_terms(text)

    if not terms:
        return (
            "## 🃏 Flashcards\n\n"
            "இந்த material-ல் இந்த API-free பதிப்பு அறிந்த முக்கிய technical terms கிடைக்கவில்லை."
        )

    out = ["## 🃏 Flashcards", ""]

    for i, (english, tamil, meaning) in enumerate(terms[:10], 1):
        out.extend(
            [
                f"### Card {i}",
                f"**Front:** {english}",
                "",
                f"**Back:** {tamil}",
                "",
                f"**Meaning:** {meaning}",
                "",
            ]
        )

    return "\n".join(out)


def word_stats(text):
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower())
    return Counter(words).most_common(8)


def reset_results():
    st.session_state.explanation = ""
    st.session_state.key_points = ""
    st.session_state.practice = ""
    st.session_state.flashcards = ""


def clear_material():
    for key in (
        "material_text",
        "material_name",
        "material_source",
        "material_image",
        "last_file_key",
        "explanation",
        "key_points",
        "practice",
        "flashcards",
    ):
        st.session_state.pop(key, None)


# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
for key, default in {
    "material_text": "",
    "material_name": "",
    "material_source": "",
    "material_image": None,
    "explanation": "",
    "key_points": "",
    "practice": "",
    "flashcards": "",
    "last_file_key": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ------------------------------------------------------------
# Styling
# ------------------------------------------------------------
st.markdown(
    """
<style>
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
header {visibility:hidden;}

.hero {
    padding: 36px 22px;
    border-radius: 24px;
    background: linear-gradient(135deg,#0ea5e9,#7c3aed);
    color: white;
    text-align: center;
    margin-bottom: 20px;
}

.hero h1 {
    font-size: 42px;
    margin: 0 0 8px 0;
}

.hero p {
    font-size: 17px;
    margin: 5px auto;
    max-width: 760px;
}

.badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(255,255,255,.18);
    margin-top: 10px;
    font-size: 14px;
}

.study-card {
    padding: 14px;
    border-radius: 16px;
    border: 1px solid rgba(128,128,128,.22);
    margin-bottom: 10px;
}

.muted {
    color: #6b7280;
    font-size: 14px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------
st.markdown(
    """
<div class="hero">
    <h1>🇮🇳 Tamil Study AI</h1>
    <p><b>Understand. Revise. Practice.</b></p>
    <p>Turn your study material into simple Tamil explanations and revision tools.</p>
    <div class="badge">🆓 API-free • No API key required</div>
</div>
""",
    unsafe_allow_html=True,
)

st.info(
    "💡 **API-free Version 2:** இந்த app external AI service-ஐ பயன்படுத்தாது. "
    "அதனால் API key தேவையில்லை. Built-in study tools பயன்படுத்தப்படுகின்றன."
)


# ------------------------------------------------------------
# Material input
# ------------------------------------------------------------
st.subheader("📚 1. Add your study material")

upload_tab, text_tab = st.tabs(
    ["📄 Upload PDF / Image", "✍️ Paste Text"]
)

with upload_tab:
    st.caption(
        f"Maximum {MAX_UPLOAD_MB} MB • PDF, PNG, JPG/JPEG, WEBP"
    )

    uploaded = st.file_uploader(
        "Upload your lesson, notes, or question",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
    )

    if uploaded is not None:
        file_key = f"{uploaded.name}:{uploaded.size}"

        if st.session_state.last_file_key != file_key:
            st.session_state.last_file_key = file_key
            st.session_state.material_name = uploaded.name
            reset_results()

            try:
                if uploaded.name.lower().endswith(".pdf"):
                    text, pages = extract_pdf_text(uploaded)
                    st.session_state.material_text = text
                    st.session_state.material_image = None
                    st.session_state.material_source = f"PDF • {pages} page(s)"
                else:
                    st.session_state.material_text = ""
                    st.session_state.material_image = read_image(uploaded)
                    st.session_state.material_source = "Image"

                st.success(f"Loaded: {uploaded.name}")
            except Exception as exc:
                st.error(str(exc))


with text_tab:
    pasted = st.text_area(
        "Paste your lesson, notes, or question",
        height=220,
        placeholder=(
            "Example:\n"
            "Photosynthesis is the process by which green plants make their own "
            "food using sunlight, carbon dioxide and water."
        ),
    )

    if pasted.strip():
        cleaned = truncate_text(pasted)

        if cleaned != st.session_state.material_text:
            st.session_state.material_text = cleaned
            st.session_state.material_image = None
            st.session_state.material_name = "Pasted text"
            st.session_state.material_source = "Pasted text"
            reset_results()


has_material = bool(
    st.session_state.material_text.strip()
    or st.session_state.material_image is not None
)


# ------------------------------------------------------------
# Material overview
# ------------------------------------------------------------
if has_material:
    st.divider()
    st.subheader("🔎 2. Material overview")

    left, right = st.columns([2, 1])

    with left:
        if st.session_state.material_image is not None:
            st.image(
                st.session_state.material_image,
                caption=st.session_state.material_name,
                use_container_width=True,
            )
            st.warning(
                "🖼️ Image loaded. இந்த API-free version image-ஐ AI போல "
                "தானாகப் படிக்காது. Text கிடைத்தால் அதை Paste Text பகுதியில் paste செய்யவும்."
            )
        else:
            preview = st.session_state.material_text[:2000]
            if len(st.session_state.material_text) > 2000:
                preview += "\n..."
            st.text_area(
                "Material preview",
                value=preview,
                height=240,
                disabled=True,
            )

    with right:
        st.metric("Input", st.session_state.material_source or "Material")

        if st.session_state.material_text:
            st.metric(
                "Characters",
                f"{len(st.session_state.material_text):,}",
            )
            st.metric(
                "Sentences",
                f"{len(split_sentences(st.session_state.material_text)):,}",
            )

        st.markdown(
            f"**Subject**  \n{detect_subject(st.session_state.material_text)}"
        )

        if st.session_state.material_text:
            stats = word_stats(st.session_state.material_text)
            if stats:
                st.caption("Frequently used terms")
                st.write(", ".join(word for word, _ in stats))

        if st.button("🗑️ Clear material", use_container_width=True):
            clear_material()
            st.rerun()


# ------------------------------------------------------------
# Study tools
# ------------------------------------------------------------
if has_material:
    st.divider()
    st.subheader("✨ 3. Study tools")

    text_ready = bool(st.session_state.material_text.strip())

    if not text_ready:
        st.warning(
            "இந்த tools பயன்படுத்த text தேவை. Image-க்கு text-ஐ Paste Text பகுதியில் சேர்க்கவும்."
        )

    a, b = st.columns(2)

    with a:
        explain_clicked = st.button(
            "📖 Explain in Tamil",
            use_container_width=True,
            type="primary",
            disabled=not text_ready,
        )

    with b:
        points_clicked = st.button(
            "🧠 Key Points",
            use_container_width=True,
            disabled=not text_ready,
        )

    c, d = st.columns(2)

    with c:
        practice_clicked = st.button(
            "❓ Practice Questions",
            use_container_width=True,
            disabled=not text_ready,
        )

    with d:
        flashcard_clicked = st.button(
            "🃏 Flashcards",
            use_container_width=True,
            disabled=not text_ready,
        )

    if explain_clicked:
        with st.spinner("விளக்கம் தயாராகிறது..."):
            st.session_state.explanation = build_explanation(
                st.session_state.material_text
            )

    if points_clicked:
        with st.spinner("முக்கிய குறிப்புகள் தயாராகின்றன..."):
            st.session_state.key_points = build_key_points(
                st.session_state.material_text
            )

    if practice_clicked:
        with st.spinner("Practice questions தயாராகின்றன..."):
            st.session_state.practice = build_questions(
                st.session_state.material_text
            )

    if flashcard_clicked:
        with st.spinner("Flashcards தயாராகின்றன..."):
            st.session_state.flashcards = make_flashcards(
                st.session_state.material_text
            )


# ------------------------------------------------------------
# Results
# ------------------------------------------------------------
if st.session_state.explanation:
    st.divider()
    st.subheader("📖 4. Explanation")
    st.markdown(st.session_state.explanation)

if st.session_state.key_points:
    st.divider()
    st.subheader("🧠 5. Key Points")
    st.markdown(st.session_state.key_points)

if st.session_state.practice:
    st.divider()
    st.subheader("❓ 6. Practice")
    st.markdown(st.session_state.practice)

if st.session_state.flashcards:
    st.divider()
    st.subheader("🃏 7. Flashcards")
    st.markdown(st.session_state.flashcards)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------
st.divider()
st.markdown(
    '<p class="muted">Tamil Study AI Version 2 • API-free edition • '
    'No OpenAI API key required.</p>',
    unsafe_allow_html=True,
)
st.caption(
    "Educational tool only. Verify important academic information with "
    "your textbook or teacher."
)
