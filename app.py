import streamlit as st
from transformers import pipeline
from fpdf import FPDF
import time

# --- Setup & Theme ---
# --- Theme Toggle ---
theme = st.radio("🌗 Choose Theme", ["Light", "Dark"])

# Inject CSS file
with open("styles/themes.css") as f:
    st.markdown(f"<body class='{theme}'>", unsafe_allow_html=True)

# Inject theme-specific override
if theme == "Dark":
    st.markdown("""
        <style>
            html, body, [data-testid="stAppViewContainer"], .stApp {
                background-color: #121212 !important;
                color: #f4f4f4 !important;
            }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
            html, body, [data-testid="stAppViewContainer"], .stApp {
                background-color: #f4f4f4 !important;
                color: #222 !important;
            }
        </style>
    """, unsafe_allow_html=True)
st.title("🧠 AI Resume & Cover Letter Generator")

phrases = ["AI Resume Generator", "Powered by GPT-2", "Made with ❤️ by Tamanna"]
placeholder = st.empty()

for phrase in phrases:
    placeholder.markdown(f"<h3 style='text-align:center; color:#ff4b4b;'>{phrase}</h3>", unsafe_allow_html=True)
    time.sleep(1.5)

# --- GPT-2 Model Loader ---
generator = pipeline("text-generation", model="sshleifer/tiny-gpt2")


def truncate_after(text, stop_word):
    stop_phrases = [stop_word, "Warm regards", "Thank you", "Sincerely", "Best regards"]
    for phrase in stop_phrases:
        if phrase in text:
            return text.split(phrase)[0].strip() + "\n" + phrase
    # If none found, fallback to first 12 lines max
    return "\n".join(text.split("\n")[:12])

def generate_text(prompt, temperature=0.7):
    result = generator(prompt, max_new_tokens=300, do_sample=True, temperature=temperature)[0]['generated_text']
    lines = result.strip().split("\n")

    clean_lines = []
    for line in lines:
        words = line.strip().split()
        unique_words = set(words)

        # Keep only meaningful lines
        if (
            len(words) >= 6 and
            len(unique_words) > 4 and
            line.isascii() and
            all(char.isalpha() or char.isspace() or char in ",.:;!?" for char in line)
        ):
            clean_lines.append(line.strip())

    return "\n".join(clean_lines)
# --- Resume / Letter Prompts ---
def generate_resume(name, role, position,company, skills, experience, temperature=0.7):
    prompt = f"""
Create a professional resume for {name}, a {role}, applying for {position} at {company}.
Include clearly labeled sections: Objective, Skills, Experience, and Highlights.
Generate detailed experience bullet points based on this input: {experience}
Skills: {skills}
"""
    raw_resume = generate_text(prompt, temperature)
    resume = truncate_after(raw_resume, "Experience:")
    return resume

def generate_letter(name, role, position, company, skills, temperature=0.7):
    role_clean = (
        role.strip()
        .replace("A background in", "")
        .replace("Software Software Engineer", "Software Engineer")
        .title()
    )
    skills_list = [s.strip().capitalize() for s in skills.split(",")]
    skills_formatted = ', '.join(skills_list)
    company = company.strip().title()

    prompt = f"""Write a professional and structured cover letter for {name}, applying for the position of {position} at {company}.
Highlight strengths in {skills_formatted}.
Explain how their background in {role_clean} makes them a strong fit.
Format the response with clear section headings and enthusiastic tone tailored to {company}'s mission."""

    try:
        response = generator(prompt, max_new_tokens=300, do_sample=True, temperature=temperature)
        response_raw = response[0]['generated_text'].strip().replace("\n\n", "\n")

# Filter noisy lines before truncation
        lines = response_raw.split("\n")
        filtered = []
        for line in lines:
            words = line.strip().split()
            unique = set(words)

            if (
                len(words) >= 6 and                  # Minimum words per line
                len(unique) > 4 and                  # Avoid repeated tokens
                line.isascii() and                  # English only
                all(c.isalpha() or c.isspace() or c in ",.:;!?'" for c in line)
             ):
                filtered.append(line.strip())

        response_filtered = "\n".join(filtered)
        response_clean = truncate_after(response_filtered, "Warm regards")
        return f"""
### 💼 Application for {position} at {company}

**👤 Candidate:** {name}  
**🎯 Target Role:** {role_clean}  
**🔧 Core Skills:** {skills_formatted}

---

**📨 Introduction**  
I am excited to apply for the position of **{position}** at **{company}**, a company renowned for innovation and excellence. With a solid background in {role_clean} and strong proficiency in {skills_formatted}, I bring creativity and precision to every project I work on.

**🧠 Why I'm a Fit**  
{response_clean}

**🚀 Alignment with {company}**  
Your mission inspires me — blending technology with purpose. I’m excited about contributing to your forward-thinking goals, bringing both technical capability and design intuition to your team.

**🙏 Closing**  
Thank you for considering my application.  
Warm regards,  
**{name}**
"""
    except Exception as e:
        st.error(f"❌ Cover letter generation failed: {str(e)}")
        return "Something went wrong while generating the cover letter."


def format_basic_resume(raw_text):
    lines = raw_text.strip().split("\n")
    formatted_lines = []

    for line in lines:
        if line.lower().startswith("objective:"):
            formatted_lines.append("\n=== Objective ===")
        elif line.lower().startswith("skills:"):
            formatted_lines.append("\n=== Skills ===")
        elif line.lower().startswith("experience:"):
            formatted_lines.append("\n=== Experience ===")
        elif line.lower().startswith("highlights:"):
            formatted_lines.append("\n=== Highlights ===")
        else:
            formatted_lines.append(line.strip())

    return "\n".join(formatted_lines)


# --- PDF + TXT Downloader ---
def download_file(content, filename_txt, filename_pdf):
    # TXT download
    st.download_button("📄 Download as TXT", data=content, file_name=filename_txt, mime="text/plain")

    # Emoji-safe sanitization function
    def sanitize_for_pdf(text):
        safe_lines = []
        for line in text.split("\n"):
            safe_line = ''.join(char for char in line if ord(char) < 128)  # Removes emojis
            safe_lines.append(safe_line)
        return "\n".join(safe_lines)

    # Sanitize content before PDF creation
    safe_content = sanitize_for_pdf(content)

    # PDF setup
    pdf = FPDF()
    pdf.add_page()
    try:
        pdf.add_font("DejaVu", "", "assets/DejaVuSans.ttf", uni=True)
        pdf.add_font("DejaVu", "B", "assets/DejaVuSans-Bold.ttf", uni=True)
        pdf.set_font("DejaVu", "", size=12)
    except:
        pdf.set_font("Arial", size=12)

    for line in safe_content.split("\n"):
        line = line.strip()
        if line.startswith("###"):
            pdf.set_font("DejaVu", "B", 14)  # Simulate a bold section header
            pdf.ln(5)
            pdf.multi_cell(0, 10, txt=line.replace("###", "").strip())
            pdf.ln(2)
            pdf.set_font("DejaVu", "", 12)  # Reset font to normal
        elif line.startswith("**"):
            pdf.set_font("DejaVu", "B", 12)
            pdf.multi_cell(0, 10, txt=line.replace("**", "").strip())
            pdf.set_font("DejaVu", "", 12)
        else:
            pdf.multi_cell(0, 10, txt=line)

    pdf_bytes = pdf.output(dest="S").encode("latin1")
    st.download_button("📄 Download as PDF", data=pdf_bytes, file_name=filename_pdf, mime="application/pdf")





def format_resume(name, job_role,resume_type, position, skills, experience, company="", style_mode="Rich"):
    role=resume_type
    name = name.strip().title()
    position = position.strip().title()
    role = role.strip().title()
    company = company.strip().title()
    skills_list = [s.strip().capitalize() for s in skills.split(",")]
    skills_str = "• " + "\n• ".join(skills_list)
    experience = experience.strip().capitalize()
    # Basic layout using GPT raw output only
    if style_mode == "Basic":
        raw_resume = generate_resume(name, job_role, position, company, skills, experience)
        return "\n".join([
            "=== Objective ===",
            f"A highly motivated {job_role} applying for {position} at {company}.",
            "",
            "=== Skills ===",
            f"{', '.join(skills_list)}",
            "",
            "=== Experience ===",
            f"{experience or 'Experience section coming soon.'}",
            "",
            "=== Highlights ===",
             f"{experience or 'Experience section coming soon.'}",
            "",
            "=== Highlights ===",
            "- Passionate about user-friendly design",
            "- Experienced in GPT-2 and responsive layouts",
            "- Built intelligent resume app with PDF support"
        ])

    # Rich layout using GPT output + markdown formatting
    gpt_resume = generate_resume(name, job_role, position, company, skills, experience)
    try:
        objective = gpt_resume.split("Objective:")[1].split("Skills:")[0].strip()
    except Exception:
        objective = "A motivated applicant eager to contribute meaningfully to this position."

    try:
        if "Experience:" in gpt_resume:
            experience_block = gpt_resume.split("Experience:")[1].strip()
        else:
            experience_block = f"- {experience}" if experience else "Experience section not found. Ready to grow and learn."
    except Exception:
        experience_block = f"- {experience}" if experience else "Experience section not found. Ready to grow and learn."

    # Rich styles based on resume_type
    if role == "Chronological":
        return f"""
### 👤 Name  
{name}

### 🎯 Position Applied  
{position} at {company}


### 🧠 Objective  
{objective}

### 🔧 Skills  
**Core Technologies:** {', '.join(skills_list)}  
**Tools:** Streamlit, FPDF, GPT-2, CSS  
**Practices:** Agile dev, Clean code, UI/UX design

### 📆 Experience Timeline  
{experience_block}

### 🌟 Highlights  
- Built AI resume generator with GPT-2  
- Designed light/dark themes with CSS  
- Debugged Unicode errors in PDF generation  
- Crafted responsive layouts using HTML & Spring Boot
"""

    elif role == "Functional":
        return f"""
### 👤 Name  
**{name}**

### 🔧 Functional Expertise  
**{position}**

### 🧠 Objective  
{objective}

### 🔍 Core Competencies  
{skills_str}

### 📌 Experience Summary  
{experience_block}

### 🧩 Tools Used  
GPT-2, FPDF, Spring Boot, Streamlit
"""

    elif role == "Combinational":
        return f"""
### 👤 Name  
**{name}**

### 💼 Combined Role  
**{position}**

### 🧠 Objective  
{objective}

### 🧪 Skill Snapshot  
{skills_str}

### 📜 Career Highlights  
{experience_block}

### 📂 Hybrid Strengths  
- Combines creative UI with robust backend logic  
- Excels in team collaboration and agile prototyping
"""

    elif role == "Mini":
        return f"""
### 👤 {name} — **{position}**

**🔹 Objective**  
{objective}

**🔹 Skills**  
{', '.join(skills_list)}

**🔹 Experience**  
{experience_block}
"""

    elif role == "Nontraditional":
        return f"""
🌈 **Creative Resume – {name}**

🎯 Role Desired: **{position}**

✨ Purpose  
I bring creativity, versatility, and a bold mindset — applying my strengths in {skills} to design experiences that resonate.

🛠️ What I Bring  
{skills_str}

📸 Notable Work  
{experience_block}

🌐 Technical Expression  
• Styled interfaces using custom CSS themes  
• Integrated GPT-2 for auto text generation  
• Built PDF export logic via FPDF  
• Explored Streamlit UI for interactive flow

📬 Let’s Collaborate!
"""

    else:
        return "**Error**: Unsupported resume type. Please select a valid format."


# --- Form Input & Output Tabs ---
with st.form("resume_form"):
    st.subheader("🧑‍💻 Enter Your Info")
    col1, col2 = st.columns(2)
    with col1:
        resume_type = st.selectbox("Resume Type", ["Chronological", "Functional", "Combinational", "Mini", "Nontraditional"], key="resume_type")
        job_role = st.text_input("Your Role (e.g. Software Engineer)", key="job_role")  # NEW FIELD
        name = st.text_input("Your Name", key="name")
        position = st.text_input("Job Position", key="position")
        skills = st.text_area("Your Skills", key="skills")
    with col2:
        experience = st.text_area("Experience Summary", key="experience")
        company = st.text_input("Company Name", key="company")
    style_mode = st.radio("🎨 Resume Style Format", ["Rich", "Basic"], key="style_mode")
    temperature = st.slider("🧠 GPT Creativity Level", 0.3, 1.0, 0.7, 0.1)
    submitted = st.form_submit_button("🚀 Create Resume & Letter")


if submitted:
    resume = format_resume(name, job_role,resume_type, position, skills, experience, company, style_mode)
    letter = generate_letter(name, job_role, position, company, skills,temperature)
    tab1, tab2 = st.tabs(["📄 Resume", "💼 Cover Letter"])
    with tab1:
        st.markdown(f"<div class='resume-box'>{resume}</div>", unsafe_allow_html=True)
        download_file(resume, f"{name}_resume.txt", f"{name}_resume.pdf")

    with tab2:
        st.markdown(f"<div class='letter-box'>{letter}</div>", unsafe_allow_html=True)
        download_file(letter, f"{name}_cover_letter.txt", f"{name}_cover_letter.pdf")