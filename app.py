import base64
import io
import os
import re

import streamlit as st
from openai import OpenAI

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from PIL import Image
except ImportError:
    Image = None

st.set_page_config(page_title="Tamil Study AI", page_icon="🇮🇳", layout="wide")

APP_NAME = "Tamil Study AI"
DEFAULT_MODEL = "gpt-4.1-mini"
MAX_UPLOAD_MB = 20
MAX_PDF_PAGES = 30
MAX_TEXT_CHARS = 45000

SYSTEM_PROMPT = """
You are Tamil Study AI, a careful study assistant for Tamil-speaking students.
Explain supplied study material in natural, simple Tamil.
Base answers primarily on the supplied material. Never invent unsupported facts.
If something is missing, unclear, or unreadable, say so.
Keep important English technical terms in parentheses when useful.
Preserve formulas, equations, units, dates, names, scientific terms, and steps.
Do not claim an answer is guaranteed for an exam.
"""


def secret(name, default=None):
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return value or os.getenv(name, default)


def client():
    key = secret("OPENAI_API_KEY")
    return OpenAI(api_key=key) if key else None


def model_name():
    return secret("OPENAI_MODEL", DEFAULT_MODEL)


def clean(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def limit_text(text):
    text = clean(text)
    if len(text) <= MAX_TEXT_CHARS:
        return text
    return text[:MAX_TEXT_CHARS].rstrip() + "\n\n[Material truncated for processing.]"


def pdf_text(file):
    if fitz is None:
        raise RuntimeError("PDF support requires PyMuPDF in requirements.txt.")
    data = file.getvalue()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"Please upload a file smaller than {MAX_UPLOAD_MB} MB.")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        count = len(doc)
        if count == 0:
            raise ValueError("The PDF does not contain any pages.")
        pages = min(count, MAX_PDF_PAGES)
        text = clean("\n\n".join(doc.load_page(i).get_text("text") for i in range(pages)))
        doc.close()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("The uploaded PDF could not be opened.") from exc
    if not text:
        raise ValueError("No readable text was found. For scanned PDFs, upload a page as an image.")
    if count > MAX_PDF_PAGES:
        text += f"\n\n[Only the first {MAX_PDF_PAGES} pages were processed from this {count}-page PDF.]"
    return limit_text(text), count


def image_url(file):
    if Image is None:
        raise RuntimeError("Image support requires Pillow in requirements.txt.")
    data = file.getvalue()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"Please upload a file smaller than {MAX_UPLOAD_MB} MB.")
    try:
        image = Image.open(io.BytesIO(data))
        image.verify()
    except Exception as exc:
        raise ValueError("The uploaded image could not be opened.") from exc
    mime = file.type if file.type in {"image/png", "image/jpeg", "image/webp"} else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def ai_text(material, task):
    ai = client()
    if ai is None:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured in Streamlit secrets. "
            "Use Manage app → Settings → Secrets and add your key."
        )
    prompt = f"""
Study material supplied by the student:
--- BEGIN MATERIAL ---
{limit_text(material)}
--- END MATERIAL ---

Task:
{task}

Respond in clear, natural Tamil. Keep important English subject terms in parentheses when useful.
"""
    response = ai.responses.create(model=model_name(), instructions=SYSTEM_PROMPT, input=prompt)
    if not response.output_text:
        raise RuntimeError("The AI returned an empty response.")
    return response.output_text.strip()


def ai_image(data_url, task):
    ai = client()
    if ai is None:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured in Streamlit secrets. "
            "Use Manage app → Settings → Secrets and add your key."
        )
    response = ai.responses.create(
        model=model_name(),
        instructions=SYSTEM_PROMPT,
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Read this study material carefully. " + task},
                {"type": "input_image", "image_url": data_url},
            ],
        }],
    )
    if not response.output_text:
        raise RuntimeError("The AI returned an empty response.")
    return response.output_text.strip()


def ask(material, image, task):
    if image:
        return ai_image(image, task)
    if not material.strip():
        raise ValueError("Please provide study material first.")
    return ai_text(material, task)


def clear_results():
    for key in ("explanation", "key_points", "practice"):
        st.session_state[key] = ""


# Session state
for key, default in {
    "material_text": "", "material_name": "", "material_source": "",
    "image_data_url": None, "explanation": "", "key_points": "",
    "practice": "", "last_file_key": "",
}.items():
    st.session_state.setdefault(key, default)

# Styling
st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;}
.hero {padding:38px 24px;border-radius:24px;background:linear-gradient(135deg,#0ea5e9,#7c3aed);color:white;text-align:center;margin-bottom:22px;}
.hero h1 {font-size:44px;margin:0 0 8px 0;}
.hero p {font-size:18px;margin:4px auto;max-width:760px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<h1>🇮🇳 Tamil Study AI</h1>
<p><b>Understand your lessons in simple Tamil.</b></p>
<p>Upload study material or paste text to get explanations, key points and practice questions.</p>
</div>
""", unsafe_allow_html=True)

if client():
    st.success(f"🤖 AI connected • Model: `{model_name()}`")
else:
    st.warning("⚠️ AI is not connected. Add OPENAI_API_KEY in Streamlit Secrets to enable AI.")

st.subheader("📚 Add your study material")
upload_tab, text_tab = st.tabs(["📄 Upload file", "✍️ Paste text"])

with upload_tab:
    st.caption(f"Maximum upload: {MAX_UPLOAD_MB} MB • PDF, PNG, JPG/JPEG, WEBP")
    uploaded = st.file_uploader(
        "Upload a PDF or image of your lesson/question",
        type=["pdf", "png", "jpg", "jpeg", "webp"],
        help=f"Maximum file size is {MAX_UPLOAD_MB} MB.",
    )
    if uploaded is not None:
        key = f"{uploaded.name}:{uploaded.size}"
        if key != st.session_state.last_file_key:
            st.session_state.last_file_key = key
            st.session_state.material_name = uploaded.name
            clear_results()
            try:
                if uploaded.name.lower().endswith(".pdf"):
                    text, pages = pdf_text(uploaded)
                    st.session_state.material_text = text
                    st.session_state.image_data_url = None
                    st.session_state.material_source = f"PDF • {pages} page(s)"
                else:
                    st.session_state.material_text = ""
                    st.session_state.image_data_url = image_url(uploaded)
                    st.session_state.material_source = "Image"
                st.success(f"Loaded: {uploaded.name}")
            except Exception as exc:
                st.session_state.material_text = ""
                st.session_state.image_data_url = None
                st.error(str(exc))

with text_tab:
    pasted = st.text_area(
        "Paste your lesson, notes, or question",
        height=220,
        placeholder="Example: Photosynthesis is the process by which green plants make food...",
    )
    if pasted.strip():
        value = limit_text(pasted)
        if value != st.session_state.material_text or st.session_state.material_source != "Pasted text":
            st.session_state.material_text = value
            st.session_state.image_data_url = None
            st.session_state.material_name = "Pasted text"
            st.session_state.material_source = "Pasted text"
            clear_results()

has_material = bool(st.session_state.material_text.strip() or st.session_state.image_data_url)

if has_material:
    st.divider()
    left, right = st.columns([2, 1])
    with left:
        st.subheader("📖 Material ready")
        if st.session_state.material_source == "Image":
            st.info(f"🖼️ {st.session_state.material_name} is ready for AI vision analysis.")
            try:
                raw = base64.b64decode(st.session_state.image_data_url.split(",", 1)[1])
                st.image(raw, caption=st.session_state.material_name)
            except Exception:
                pass
        else:
            preview = st.session_state.material_text[:1800]
            if len(st.session_state.material_text) > 1800:
                preview += "\n..."
            st.text_area("Extracted text preview", value=preview, height=230, disabled=True)
    with right:
        st.metric("Input", st.session_state.material_source or "Material")
        if st.session_state.material_text:
            st.metric("Characters", f"{len(st.session_state.material_text):,}")
        st.caption("AI output can contain mistakes. Verify important academic information with your textbook or teacher.")
        if st.button("🗑️ Clear material", use_container_width=True):
            for key, default in {
                "material_text": "", "material_name": "", "material_source": "",
                "image_data_url": None, "explanation": "", "key_points": "",
                "practice": "", "last_file_key": "",
            }.items():
                st.session_state[key] = default
            st.rerun()

if has_material:
    st.divider()
    st.subheader("✨ Learn from your material")
    a, b, c = st.columns(3)
    with a:
        explain = st.button("📖 Explain in Tamil", use_container_width=True, type="primary")
    with b:
        points = st.button("🧠 Key Points", use_container_width=True)
    with c:
        practice = st.button("❓ Practice Questions", use_container_width=True)

    if explain:
        with st.spinner("தமிழில் எளிய விளக்கம் உருவாக்கப்படுகிறது..."):
            try:
                st.session_state.explanation = ask(
                    st.session_state.material_text, st.session_state.image_data_url,
                    """
Explain the lesson in simple Tamil.
Use: a short heading, main idea, small concept sections, simple examples supported by the material,
and a short 'நினைவில் வைத்துக்கொள்ளுங்கள்' section. Preserve formulas, equations, steps and terminology.
Do not add unsupported facts.
""",
                )
            except Exception as exc:
                st.error(f"Could not generate the explanation: {exc}")

    if points:
        with st.spinner("முக்கிய குறிப்புகள் உருவாக்கப்படுகின்றன..."):
            try:
                st.session_state.key_points = ask(
                    st.session_state.material_text, st.session_state.image_data_url,
                    """
Create a concise study sheet based only on the material.
Return:
### 🧠 முக்கிய குறிப்புகள் — 5 to 10 useful bullet points
### 📌 முக்கிய சொற்கள் — important English terms with short Tamil meanings
### ⚡ Quick Revision — a very short summary
Do not invent facts or terms absent from the material.
""",
                )
            except Exception as exc:
                st.error(f"Could not generate key points: {exc}")

    if practice:
        with st.spinner("பயிற்சி கேள்விகள் உருவாக்கப்படுகின்றன..."):
            try:
                st.session_state.practice = ask(
                    st.session_state.material_text, st.session_state.image_data_url,
                    """
Create a practice set based only on the material.
Include 5 multiple-choice questions with A-D options and the correct answer,
5 short-answer questions with concise model answers, and 2 harder revision questions with answers.
Keep it appropriate for a school student and do not test facts absent from the material.
""",
                )
            except Exception as exc:
                st.error(f"Could not generate practice questions: {exc}")

if st.session_state.explanation:
    st.divider()
    st.subheader("📖 Explanation in Tamil")
    st.markdown(st.session_state.explanation)

if st.session_state.key_points:
    st.divider()
    st.subheader("🧠 Key Points")
    st.markdown(st.session_state.key_points)

if st.session_state.practice:
    st.divider()
    st.subheader("❓ Practice Questions")
    st.markdown(st.session_state.practice)

st.divider()
st.caption("Tamil Study AI • Educational tool. Verify important academic information with your textbook or teacher.")
