import random
import re
import streamlit as st
import fitz

st.set_page_config(page_title="Tamil Study AI", page_icon="📚", layout="wide")

if "study_text" not in st.session_state:
    st.session_state.study_text = ""
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "quiz" not in st.session_state:
    st.session_state.quiz = []
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0
if "quiz_count" not in st.session_state:
    st.session_state.quiz_count = 5
if "quiz_version" not in st.session_state:
    st.session_state.quiz_version = 0

st.markdown("""
<style>
.hero{padding:1.5rem;border-radius:18px;background:#f3f6fb;border:1px solid #dce4ef;margin-bottom:1.5rem}
.card{padding:1rem;border:1px solid #e5e7eb;border-radius:14px;background:white}
</style>
<div class="hero">
<h1>📚 Tamil Study AI</h1>
<p>Your simple no-API study assistant for notes, revision, practice questions, flashcards and quizzes.</p>
</div>
""", unsafe_allow_html=True)

def clean_text(text):
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def sentences(text):
    return [x.strip() for x in re.split(r"(?<=[.!?।])\s+|\n+", text) if len(x.strip()) > 12]

def subject(text):
    t = text.lower()
    groups = {
        "Biology": ["photosynthesis","cell","plant","biology","தாவரம்","உயிரியல்","ஒளிச்சேர்க்கை"],
        "Physics": ["force","motion","energy","gravity","physics","விசை","இயக்கம்","ஆற்றல்","இயற்பியல்"],
        "Chemistry": ["atom","molecule","element","reaction","chemistry","அணு","மூலக்கூறு","வேதியியல்"],
        "Mathematics": ["equation","algebra","geometry","math","கணிதம்","சமன்பாடு"],
        "Social Science": ["democracy","government","history","constitution","ஜனநாயகம்","வரலாறு","அரசு"],
        "English": ["grammar","noun","verb","adjective","sentence","english","இலக்கணம்"]
    }
    scores = {k: sum(w in t for w in v) for k,v in groups.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "General"

def reset_quiz():
    st.session_state.quiz = []
    st.session_state.quiz_started = False
    st.session_state.quiz_submitted = False
    st.session_state.quiz_answers = {}
    st.session_state.quiz_score = 0
    st.session_state.quiz_version += 1

def build_quiz(text, count):
    t = text.lower()
    q = []
    if "photosynthesis" in t or "ஒளிச்சேர்க்கை" in t:
        q += [
            {"q":"What is the main purpose of photosynthesis?","o":["To make food using light energy","To absorb oxygen from soil","To produce sound","To break down rocks"],"a":"To make food using light energy","e":"Green plants use light energy to make food."},
            {"q":"Which gas is used by plants during photosynthesis?","o":["Carbon dioxide","Nitrogen","Helium","Hydrogen"],"a":"Carbon dioxide","e":"Carbon dioxide is used along with water during photosynthesis."},
            {"q":"Which pigment captures light in photosynthesis?","o":["Chlorophyll","Hemoglobin","Keratin","Insulin"],"a":"Chlorophyll","e":"Chlorophyll is the green pigment that captures light energy."},
            {"q":"Which substance is produced as food during photosynthesis?","o":["Glucose","Salt","Iron","Calcium"],"a":"Glucose","e":"Photosynthesis produces glucose."},
            {"q":"Which gas is released during photosynthesis?","o":["Oxygen","Carbon dioxide","Nitrogen","Helium"],"a":"Oxygen","e":"Oxygen is released as a product of photosynthesis."},
            {"q":"Which two raw materials are needed for photosynthesis?","o":["Carbon dioxide and water","Oxygen and salt","Nitrogen and iron","Glucose and oxygen"],"a":"Carbon dioxide and water","e":"Carbon dioxide and water are the main raw materials."}
        ]
    if "atom" in t or "அணு" in t:
        q += [
            {"q":"What is an atom?","o":["The basic unit of an element","A type of plant","A form of energy","A type of force"],"a":"The basic unit of an element","e":"An atom is the basic unit of an element."},
            {"q":"Which particle has a negative electric charge?","o":["Electron","Proton","Neutron","Nucleus"],"a":"Electron","e":"Electrons have a negative electric charge."}
        ]
    if "gravity" in t or "ஈர்ப்பு" in t:
        q += [{"q":"What does gravity do on Earth?","o":["Attracts objects toward Earth","Stops all motion","Creates light","Removes mass"],"a":"Attracts objects toward Earth","e":"Earth's gravity attracts objects toward its center."}]
    if "democracy" in t or "ஜனநாயகம்" in t:
        q += [{"q":"What is a key feature of democracy?","o":["People participate in choosing representatives","Only one person makes every decision","Citizens cannot influence government","Elections are never used"],"a":"People participate in choosing representatives","e":"Democracy includes participation by people in government."}]
    if not q:
        ss = sentences(text)
        for s in ss[:10]:
            words = re.findall(r"[A-Za-z]{4,}", s)
            if len(words) >= 4:
                answer = words[-1].strip(".,!?;:")
                q.append({"q":f"Which term appears in this study statement?\n\n{s}","o":[answer,words[0],words[1],words[2]],"a":answer,"e":"This answer is taken from the supplied study material."})
    if not q:
        q = [
            {"q":"Which habit is useful for effective studying?","o":["Reviewing material regularly","Never revisiting notes","Studying only at the last minute","Avoiding practice questions"],"a":"Reviewing material regularly","e":"Regular review helps reinforce learning."},
            {"q":"Why are practice questions useful?","o":["To check your understanding","To avoid learning","To remove revision","To replace every lesson"],"a":"To check your understanding","e":"Practice questions help you check what you understand."}
        ]
    unique=[]
    seen=set()
    for item in q:
        if item["q"] not in seen:
            seen.add(item["q"])
            item["o"] = list(item["o"])
            random.shuffle(item["o"])
            unique.append(item)
    random.shuffle(unique)
    return unique[:count]

with st.sidebar:
    st.header("📖 Study Assistant")
    mode = st.radio("Mode", ["📄 Study Notes","🎯 Test Yourself"])
    st.divider()
    st.write("• Explain in Tamil")
    st.write("• Key points")
    st.write("• Practice questions")
    st.write("• Flashcards")
    st.write("• Vocabulary")
    st.write("• Quiz mode")
    st.divider()
    st.caption("No API key required.")

st.subheader("📥 Add your study material")
method = st.radio("Input method", ["Paste text","Upload PDF"], horizontal=True)

text = ""
if method == "Paste text":
    text = st.text_area("Paste your notes or textbook content here", height=220,
                        placeholder="Example: Photosynthesis is the process by which green plants make food...")
else:
    file = st.file_uploader("Upload a PDF", type=["pdf"])
    if file:
        try:
            doc = fitz.open(stream=file.getvalue(), filetype="pdf")
            text = "\n".join(page.get_text("text") for page in doc).strip()
            doc.close()
            st.success("PDF text extracted successfully.")
        except Exception as e:
            st.error(f"Could not read PDF: {e}")

if text:
    st.session_state.study_text = clean_text(text)

if st.session_state.study_text:
    st.success("Study material is ready.")
    if st.button("✨ Analyze Study Material", type="primary"):
        ss = sentences(st.session_state.study_text)
        points = ss[:7]
        vocab = re.findall(r"[A-Za-z]{4,}", st.session_state.study_text.lower())
        st.session_state.analysis = {
            "subject": subject(st.session_state.study_text),
            "points": points,
            "vocab": list(dict.fromkeys(vocab))[:10],
            "explanation": "இந்தப் பாடத்தின் முக்கிய கருத்துகளை எளிமையாகப் புரிந்துகொள்ள கீழே உள்ள குறிப்புகளைப் பயன்படுத்தலாம்."
        }
        reset_quiz()
        st.rerun()

if st.session_state.analysis and mode == "📄 Study Notes":
    a = st.session_state.analysis
    st.divider()
    st.subheader("📚 Study Analysis")
    c1,c2=st.columns(2)
    with c1:
        st.markdown("### 🏷️ Subject")
        st.info(a["subject"])
    with c2:
        st.markdown("### 📝 Quick explanation")
        st.write(a["explanation"])
    st.markdown("### 🔑 Key Points")
    for p in a["points"]:
        st.markdown("- " + p)
    st.markdown("### 🧠 Vocabulary")
    st.write(", ".join(a["vocab"]) if a["vocab"] else "No vocabulary detected.")
    st.markdown("### 🃏 Flashcards")
    for i,p in enumerate(a["points"][:5],1):
        with st.expander(f"Flashcard {i}"):
            st.markdown("**Question:** What is the key idea?")
            st.write(p)

if mode == "🎯 Test Yourself":
    st.divider()
    st.subheader("🎯 Test Yourself")
    if not st.session_state.study_text:
        st.info("Add study material above first.")
    else:
        count = st.selectbox("Number of questions",[3,5,7,10],index=1,key="quiz_count_selector")
        st.session_state.quiz_count = count

        if not st.session_state.quiz_started:
            st.markdown('<div class="card"><b>Ready?</b><br>Answers will start completely unselected.</div>',unsafe_allow_html=True)
            if st.button("🚀 Start Quiz", type="primary"):
                st.session_state.quiz = build_quiz(st.session_state.study_text,count)
                st.session_state.quiz_started = True
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {i:None for i in range(len(st.session_state.quiz))}
                st.session_state.quiz_version += 1
                st.rerun()
        elif not st.session_state.quiz_submitted:
            st.markdown(f"### Quiz — {len(st.session_state.quiz)} Questions")
            unanswered=[]
            for i,item in enumerate(st.session_state.quiz):
                st.markdown(f"#### Question {i+1} of {len(st.session_state.quiz)}")
                st.write(item["q"])

                # VERSION 3.1 FIX:
                # index=None prevents the first answer from being selected.
                selected = st.radio(
                    "Choose one answer:",
                    item["o"],
                    index=None,
                    key=f"quiz_answer_{st.session_state.quiz_version}_{i}",
                    label_visibility="collapsed"
                )
                st.session_state.quiz_answers[i]=selected
                if selected is None:
                    unanswered.append(i+1)
                st.divider()

            if unanswered:
                st.warning("Please answer all questions before submitting. Unanswered: " + ", ".join(map(str,unanswered)))

            if st.button("✅ Submit Quiz", type="primary", disabled=bool(unanswered)):
                st.session_state.quiz_score = sum(
                    st.session_state.quiz_answers[i] == item["a"]
                    for i,item in enumerate(st.session_state.quiz)
                )
                st.session_state.quiz_submitted=True
                st.rerun()
        else:
            total=len(st.session_state.quiz)
            score=st.session_state.quiz_score
            pct=round(score/total*100) if total else 0
            st.success(f"🎉 You scored {score}/{total} ({pct}%)")
            if pct >= 80:
                st.balloons()
            elif pct >= 50:
                st.info("Good effort! Review the questions you missed.")
            else:
                st.info("Keep practicing and revise the topic again.")

            st.markdown("### 📋 Answer Review")
            for i,item in enumerate(st.session_state.quiz):
                chosen=st.session_state.quiz_answers.get(i)
                if chosen == item["a"]:
                    st.markdown(f"#### {i+1}. ✅ Correct")
                    st.write(f"Your answer: **{chosen}**")
                else:
                    st.markdown(f"#### {i+1}. ❌ Incorrect")
                    st.write(f"Your answer: **{chosen}**")
                    st.write(f"Correct answer: **{item['a']}**")
                st.caption(item["e"])
                st.divider()

            if st.button("🔄 Try Another Quiz", type="primary"):
                reset_quiz()
                st.rerun()

st.divider()
st.caption("Tamil Study AI • Version 3.1 • No API key required")
