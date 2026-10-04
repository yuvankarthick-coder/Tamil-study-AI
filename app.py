import streamlit as st
import fitz
import random
import re

st.set_page_config(page_title="Tamil Study AI", page_icon="📚", layout="wide")

st.markdown("""
<style>
.main-title{font-size:42px;font-weight:800;margin-bottom:5px}
.subtitle{font-size:18px;opacity:.8;margin-bottom:25px}
.card{padding:18px;border-radius:14px;border:1px solid rgba(128,128,128,.25);margin-bottom:15px}
.section-title{font-size:25px;font-weight:700;margin-top:15px;margin-bottom:10px}
</style>
""", unsafe_allow_html=True)

for key, default in {
    "quiz_questions": [], "quiz_answers": {}, "quiz_submitted": False,
    "quiz_version": 0, "study_text": ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def clean_text(text):
    return re.sub(r"\s+", " ", (text or "").replace("\x00", " ")).strip()

def extract_pdf_text(uploaded_file):
    try:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = clean_text("\n".join(page.get_text() for page in doc))
        doc.close()
        return text
    except Exception as e:
        st.error(f"Could not read the PDF: {e}")
        return ""

def detect_subject(text):
    lower = text.lower()
    groups = {
        "Biology":["photosynthesis","cell","plant","animal","chlorophyll","respiration","biology"],
        "Physics":["gravity","force","motion","speed","velocity","energy","newton","mass","physics"],
        "Chemistry":["atom","molecule","element","chemical","reaction","acid","base","oxygen","hydrogen","chemistry"],
        "Mathematics":["equation","number","fraction","algebra","geometry","triangle","angle","mathematics","math"],
        "History":["war","king","empire","independence","history","revolution","ancient","dynasty"],
        "Civics":["democracy","government","constitution","citizen","election","parliament","rights"]
    }
    scores = {s: sum(w in lower for w in words) for s, words in groups.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "General Studies"

def tamil_explanation(text, subject):
    lower = text.lower()
    if "photosynthesis" in lower:
        return "ஒளிச்சேர்க்கை என்பது பச்சைத் தாவரங்கள் சூரிய ஒளியைப் பயன்படுத்தி உணவை உருவாக்கும் செயல்முறையாகும். இதற்கு கார்பன் டை ஆக்சைடு, நீர் மற்றும் குளோரோஃபில் உதவுகின்றன. இந்த செயல்முறையில் ஆக்சிஜன் துணைப் பொருளாக வெளியிடப்படுகிறது."
    if "atom" in lower:
        return "அணு என்பது ஒரு தனிமத்தின் வேதியியல் பண்புகளைத் தக்க வைத்திருக்கும் மிகச் சிறிய அலகாகும். அணுவில் புரோட்டான், நியூட்ரான் மற்றும் எலக்ட்ரான் போன்ற துகள்கள் உள்ளன."
    if "gravity" in lower:
        return "ஈர்ப்பு விசை என்பது நிறை கொண்ட பொருட்களை ஒன்றை ஒன்று நோக்கி இழுக்கும் விசையாகும். பூமியின் ஈர்ப்பு விசை காரணமாக பொருட்கள் பூமியை நோக்கி விழுகின்றன."
    if "democracy" in lower:
        return "ஜனநாயகம் என்பது மக்கள் தங்கள் பிரதிநிதிகளைத் தேர்ந்தெடுத்து ஆட்சியில் பங்கேற்கும் ஒரு ஆட்சி முறையாகும். தேர்தல், மக்களின் பங்கேற்பு மற்றும் உரிமைகள் முக்கிய அம்சங்களாகும்."
    return f"இந்தப் பகுதி {subject} தொடர்பான படிப்புப் பொருளாகும். கொடுக்கப்பட்ட குறிப்புகளில் உள்ள முக்கிய கருத்துகளைப் புரிந்து கொண்டு, அவற்றுக்கிடையிலான தொடர்புகளை நினைவில் வைத்துக் கொள்வது முக்கியம்."

def extract_key_points(text):
    points = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) >= 20]
    if not points and text:
        points = [" ".join(text.split()[:35])]
    return points[:6]

def get_vocabulary(text):
    lower = text.lower()
    known = {
        "photosynthesis":"ஒளிச்சேர்க்கை","chlorophyll":"குளோரோஃபில் / பச்சையம்",
        "glucose":"குளுக்கோஸ்","oxygen":"ஆக்சிஜன்","carbon dioxide":"கார்பன் டை ஆக்சைடு",
        "atom":"அணு","molecule":"மூலக்கூறு","gravity":"ஈர்ப்பு விசை","force":"விசை",
        "energy":"ஆற்றல்","democracy":"ஜனநாயகம்","government":"அரசாங்கம்",
        "constitution":"அரசியலமைப்பு","election":"தேர்தல்"
    }
    found = [(w.title(), t) for w,t in known.items() if w in lower]
    if found: return found[:8]
    words = re.findall(r"[A-Za-z]{5,}", text)
    seen, result = set(), []
    for word in words:
        if word.lower() not in seen:
            seen.add(word.lower()); result.append((word, "பாடத்தில் வரும் முக்கிய சொல்"))
    return result[:8]

def make_flashcards(text):
    lower = text.lower()
    if "photosynthesis" in lower:
        return [
            ("What is photosynthesis?","The process by which green plants make food using sunlight."),
            ("What pigment helps absorb sunlight?","Chlorophyll."),
            ("What gas is released during photosynthesis?","Oxygen.")
        ]
    if "atom" in lower:
        return [
            ("What is an atom?","The smallest unit of an element that retains its chemical properties."),
            ("Name two particles found in an atom.","Protons and electrons."),
            ("Which particle has a negative charge?","The electron.")
        ]
    if "gravity" in lower:
        return [
            ("What is gravity?","A force that attracts masses toward one another."),
            ("Why do objects fall toward Earth?","Because Earth's gravity attracts them."),
            ("What does gravity do?","It attracts masses toward one another.")
        ]
    if "democracy" in lower:
        return [
            ("What is democracy?","A system of government in which people participate in choosing representatives."),
            ("What is an important feature of democracy?","Free and fair elections."),
            ("Why are citizens important?","They participate in the political process and exercise their rights.")
        ]
    return [(f"Key idea {i}", p) for i,p in enumerate(extract_key_points(text)[:5],1)]

def make_practice_questions(text):
    lower = text.lower()
    if "photosynthesis" in lower:
        return [
            {"q":"Which process allows green plants to make their food?","a":"Photosynthesis","options":["Respiration","Photosynthesis","Digestion","Transpiration"]},
            {"q":"Which pigment absorbs sunlight during photosynthesis?","a":"Chlorophyll","options":["Hemoglobin","Chlorophyll","Insulin","Keratin"]},
            {"q":"Which gas is released as a by-product of photosynthesis?","a":"Oxygen","options":["Nitrogen","Oxygen","Hydrogen","Helium"]}
        ]
    if "atom" in lower:
        return [
            {"q":"What is the smallest unit of an element that retains its chemical properties?","a":"Atom","options":["Cell","Atom","Tissue","Organ"]},
            {"q":"Which particle has a negative charge?","a":"Electron","options":["Proton","Neutron","Electron","Nucleus"]},
            {"q":"Which particles are found in the nucleus of an atom?","a":"Protons and neutrons","options":["Electrons only","Protons and neutrons","Electrons and protons","Photons and electrons"]}
        ]
    if "gravity" in lower:
        return [
            {"q":"What force attracts objects toward Earth?","a":"Gravity","options":["Friction","Gravity","Magnetism","Pressure"]},
            {"q":"Why does an object fall toward Earth?","a":"Earth's gravity attracts it","options":["Earth's gravity attracts it","The object becomes weightless","Air pushes it downward","The Sun pulls it downward"]}
        ]
    if "democracy" in lower:
        return [
            {"q":"Which is an important feature of democracy?","a":"Elections","options":["Elections","Monarchy","Censorship","Dictatorship"]},
            {"q":"In a democracy, citizens can participate mainly by:","a":"Voting and choosing representatives","options":["Voting and choosing representatives","Avoiding elections","Removing all laws","Ending public participation"]}
        ]
    points = extract_key_points(text)
    result = []
    for i, point in enumerate(points[:4],1):
        words = re.findall(r"[A-Za-z]{4,}", point)
        if len(words) >= 2:
            answer = words[-1]
            question = point.replace(answer, "_____")
            distractors = [w for w in words[:-1] if w.lower() != answer.lower()]
            while len(distractors) < 3:
                distractors.append(f"Option {len(distractors)+1}")
            options = [answer] + distractors[:3]
            random.shuffle(options)
            result.append({"q":f"Complete the idea from the notes: {question}","a":answer,"options":options})
    return result

def build_quiz_questions(text, count):
    practice = make_practice_questions(text)
    pool = [{
        "q":x["q"], "a":x["a"], "options":x["options"],
        "explanation":"Review the study notes and identify the statement supported by them."
    } for x in practice]
    if not pool:
        pool = [{
            "q":"What is the main purpose of the study material you provided?",
            "a":"To learn the topic explained in the notes",
            "options":["To learn the topic explained in the notes","To delete the notes","To stop studying","To change the subject"],
            "explanation":"The quiz is based on the study material supplied by the learner."
        }]
    selected = random.sample(pool, min(count, len(pool)))
    while len(selected) < count:
        selected.append(random.choice(pool).copy())
    for item in selected:
        item["options"] = item["options"].copy()
        random.shuffle(item["options"])
    return selected

def reset_quiz():
    st.session_state.quiz_questions=[]
    st.session_state.quiz_answers={}
    st.session_state.quiz_submitted=False
    st.session_state.quiz_version += 1

st.markdown('<div class="main-title">📚 Tamil Study AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your simple AI-free study assistant for notes, revision and quizzes.</div>', unsafe_allow_html=True)

mode = st.sidebar.radio("Choose a mode:", ["📄 Study Notes","🎯 Test Yourself"])

if mode == "📄 Study Notes":
    st.markdown("### 📄 Add your study material")
    input_method = st.radio("Choose input method:", ["Paste Text","Upload PDF"], horizontal=True)
    text = ""
    if input_method == "Paste Text":
        text = st.text_area("Paste your notes here:", height=220, placeholder="Paste your study notes here...")
    else:
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        if uploaded_file:
            text = extract_pdf_text(uploaded_file)
            if text: st.success("PDF text extracted successfully.")

    if st.button("✨ Analyze My Notes", type="primary", use_container_width=True):
        text = clean_text(text)
        if not text:
            st.warning("Please paste some notes or upload a PDF first.")
        else:
            st.session_state.study_text = text

    if st.session_state.study_text:
        study_text = st.session_state.study_text
        subject = detect_subject(study_text)

        st.markdown("---")
        st.markdown("## 📊 Study Analysis")
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("### 📚 Subject"); st.info(subject)
        with c2:
            st.markdown("### 📝 Words"); st.info(str(len(study_text.split())))

        st.markdown('<div class="section-title">🇮🇳 தமிழ் விளக்கம்</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card">{tamil_explanation(study_text, subject)}</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">🔑 Key Points</div>', unsafe_allow_html=True)
        for point in extract_key_points(study_text):
            st.markdown(f"- {point}")

        st.markdown('<div class="section-title">🧠 Vocabulary</div>', unsafe_allow_html=True)
        for english,tamil in get_vocabulary(study_text):
            st.markdown(f"**{english}** → {tamil}")

        st.markdown('<div class="section-title">🃏 Flashcards</div>', unsafe_allow_html=True)
        for question,answer in make_flashcards(study_text):
            with st.expander(question): st.write(answer)

        st.markdown('<div class="section-title">✍️ Practice Questions</div>', unsafe_allow_html=True)
        practice = make_practice_questions(study_text)
        if practice:
            for i,item in enumerate(practice,1):
                st.markdown(f"**{i}. {item['q']}**")
                st.write(f"Answer: **{item['a']}**")
                st.write("---")
        else:
            st.info("No practice questions could be generated from these notes.")

else:
    st.markdown("## 🎯 Test Yourself")
    st.write("Create a multiple-choice quiz from your study material.")
    method = st.radio("Choose input method:", ["Use current study notes","Paste new text","Upload PDF"], horizontal=True)
    quiz_text = ""
    if method == "Use current study notes":
        quiz_text = st.session_state.study_text
        if quiz_text: st.success("Using your current study notes.")
        else: st.info("No study notes are currently loaded. Paste text or upload a PDF.")
    elif method == "Paste new text":
        quiz_text = st.text_area("Paste text for the quiz:", height=200)
    else:
        qfile = st.file_uploader("Upload a PDF for the quiz", type=["pdf"], key="quiz_pdf")
        if qfile: quiz_text = extract_pdf_text(qfile)

    count = st.selectbox("Number of questions:", [3,5,7,10])
    if st.button("🚀 Generate Quiz", type="primary", use_container_width=True):
        quiz_text = clean_text(quiz_text)
        if not quiz_text:
            st.warning("Please provide study material first.")
        else:
            st.session_state.quiz_questions = build_quiz_questions(quiz_text,count)
            st.session_state.quiz_answers = {}
            st.session_state.quiz_submitted = False
            st.session_state.quiz_version += 1

    if st.session_state.quiz_questions:
        st.markdown("---")
        st.markdown("### 📝 Your Quiz")
        for i,item in enumerate(st.session_state.quiz_questions):
            st.markdown(f"**Question {i+1}:** {item['q']}")
            selected = st.radio("Choose one answer:", item["options"], index=None,
                                key=f"quiz_answer_{st.session_state.quiz_version}_{i}",
                                label_visibility="collapsed")
            st.session_state.quiz_answers[i] = selected

        all_answered = all(st.session_state.quiz_answers.get(i) is not None for i in range(len(st.session_state.quiz_questions)))
        if not all_answered: st.info("Please answer every question before submitting.")
        if st.button("✅ Submit Quiz", disabled=not all_answered, use_container_width=True):
            st.session_state.quiz_submitted = True

        if st.session_state.quiz_submitted:
            score = sum(st.session_state.quiz_answers.get(i)==item["a"] for i,item in enumerate(st.session_state.quiz_questions))
            total = len(st.session_state.quiz_questions)
            st.markdown("---")
            st.markdown("## 🏆 Your Result")
            st.success(f"You scored **{score}/{total}**")
            pct = int(score/total*100)
            if pct == 100:
                st.balloons(); st.success("Excellent! Perfect score! 🎉")
            elif pct >= 70: st.success("Great job! Keep revising. 💪")
            elif pct >= 40: st.warning("Good attempt. A little more revision will help. 📖")
            else: st.info("Keep practicing. You can improve with another attempt. 🔁")
            st.markdown("## 🔍 Answer Review")
            for i,item in enumerate(st.session_state.quiz_questions):
                user_answer = st.session_state.quiz_answers.get(i)
                if user_answer == item["a"]: st.success(f"Question {i+1}: Correct")
                else: st.error(f"Question {i+1}: Incorrect")
                st.write(f"Your answer: **{user_answer}**")
                st.write(f"Correct answer: **{item['a']}**")
                st.caption(item["explanation"])
            if st.button("🔄 Try Another Quiz", use_container_width=True):
                reset_quiz(); st.rerun()

st.markdown("---")
st.caption("Tamil Study AI • Version 3.2 • No API key required")
