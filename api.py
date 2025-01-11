import openai
import streamlit as st
from dotenv import load_dotenv
import os
import shelve
import unicodedata
from fpdf import FPDF
import base64

def generate_pdf(content, filename):
    content = unicodedata.normalize('NFKD', content).encode('ascii', 'ignore').decode('ascii')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', size=12)
    pdf.multi_cell(0, 10, content)
    pdf.output(filename)
    return filename

st.set_page_config(
    page_title="Automated Course Content Generator",
    page_icon=":robot:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_dotenv()

with st.sidebar:
    language = st.selectbox("Select Language / Sélectionnez la langue", ["English", "Français"])

translations = {
    "title": {"English": "Automated Course Content Generator 🤖", "Français": "Générateur de Contenu de Cours Automatisé 🤖"},
    "course_details": {"English": "Course Details 📋", "Français": "Détails du Cours 📋"},
    "course_name": {"English": "Course Name", "Français": "Nom du Cours"},
    "target_audience": {"English": "Target Audience Edu Level", "Français": "Niveau Éducatif de l'Audience Cible"},
    "difficulty_level": {"English": "Course Difficulty Level", "Français": "Niveau de Difficulté du Cours"},
    "modules": {"English": "No. of Modules", "Français": "Nombre de Modules"},
    "duration": {"English": "Course Duration", "Français": "Durée du Cours"},
    "credit": {"English": "Course Credit", "Français": "Crédit du Cours"},
    "generate_outline": {"English": "Generate Course Outline", "Français": "Générer un Plan de Cours"},
    "start_new_course": {"English": "Start a New Course", "Français": "Commencer un Nouveau Cours"},
    "content_header": {"English": "Generated Course Content 📝", "Français": "Contenu du Cours Généré 📝"},
    "outline": {"English": "Course Outline", "Français": "Plan du Cours"},
    "generate_complete": {"English": "Generate Complete Course", "Français": "Générer le Cours Complet"},
    "modifications": {"English": "Make Modifications", "Français": "Faire des Modifications"},
    "delete_history": {"English": "Delete Chat History", "Français": "Supprimer l'Historique des Conversations"},
}

st.title(translations["title"][language])

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API Key not found.")
    openai.api_key = api_key
except Exception as e:
    st.error(f"Error: {e}")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])

def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages

if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

if "course_modules" not in st.session_state:
    st.session_state.course_modules = []

with st.sidebar:
    if st.button(translations["delete_history"][language]):
        st.session_state.messages = []
        save_chat_history([])

col1, col_divider, col2 = st.columns([3.0, 0.1, 7.0])

with col1:
    st.header(translations["course_details"][language])
    course_name = st.text_input(translations["course_name"][language])
    target_audience_edu_level = st.selectbox(
        translations["target_audience"][language],
        ["Primary", "High School", "Diploma", "Bachelors", "Masters"]
    )
    difficulty_level = st.radio(
        translations["difficulty_level"][language],
        ["Beginner", "Intermediate", "Advanced"]
    )
    num_modules = st.slider(
        translations["modules"][language],
        min_value=1, max_value=15
    )
    course_duration = st.text_input(translations["duration"][language])
    course_credit = st.text_input(translations["credit"][language])

    st.session_state.course_name = course_name
    st.session_state.target_audience_edu_level = target_audience_edu_level
    st.session_state.difficulty_level = difficulty_level
    st.session_state.num_modules = num_modules
    st.session_state.course_duration = course_duration
    st.session_state.course_credit = course_credit

    button1, button2 = st.columns([1, 0.8])
    with button1:
        generate_button = st.button(translations["generate_outline"][language])
    with button2:
        if "pdf" in st.session_state:
            new_course_button = st.button(translations["start_new_course"][language])
            if new_course_button:
                st.session_state.course_name = ""
                st.session_state.target_audience_edu_level = ""
                st.session_state.difficulty_level = ""
                st.session_state.num_modules = 1
                st.session_state.course_duration = ""
                st.session_state.course_credit = ""
                st.session_state.pdf = False
                st.experimental_rerun()

with col2:
    st.header(translations["content_header"][language])
    if generate_button and "pdf" not in st.session_state:
        user_selections = f"{translations['course_name'][language]}: {course_name}\n{translations['target_audience'][language]}: {target_audience_edu_level}\n{translations['difficulty_level'][language]}: {difficulty_level}\n{translations['modules'][language]}: {num_modules}\n{translations['duration'][language]}: {course_duration}\n{translations['credit'][language]}: {course_credit}"
        st.session_state.messages.append({"role": "user", "content": user_selections})

        PROMPT = f"You are Prompter. Generate a detailed prompt for Tabler using these inputs: 1) Course Name: {course_name} 2) Target Audience Edu Level: {target_audience_edu_level} 3) Course Difficulty Level: {difficulty_level} 4) No. of Modules: {num_modules} 5) Course Duration: {course_duration} 6) Course Credit: {course_credit}."

        response = openai.ChatCompletion.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": "system", "content": PROMPT},
            ]
        )
        generated_prompt = response.choices[0].message["content"]

        with st.spinner("Generating course outline..."):
            response = openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=[
                    {"role": "system", "content": generated_prompt},
                ]
            )
            course_outline = response.choices[0].message["content"]
            st.success("Course outline generated successfully!")
            st.session_state['course_outline'] = course_outline
            st.session_state['buttons_visible'] = True

    if 'course_outline' in st.session_state and "pdf" not in st.session_state:
        with st.expander(translations["outline"][language]):
            st.write(st.session_state['course_outline'])

        if 'buttons_visible' in st.session_state and st.session_state['buttons_visible']:
            button1, button2 = st.columns([1, 2])
            with button1:
                complete_course_button = st.button(translations["generate_complete"][language])
            with button2:
                modifications_button = st.button(translations["modifications"][language])

            if complete_course_button:
                with st.spinner("Generating complete course by module..."):
                    modules = []
                    for i in range(1, st.session_state.num_modules + 1):
                        module_prompt = f"Generate detailed content for Module {i} of the course: {course_name}. The module should include an introduction, main content, examples, and a summary."
                        response = openai.ChatCompletion.create(
                            model=st.session_state["openai_model"],
                            messages=[
                                {"role": "system", "content": module_prompt},
                            ]
                        )
                        module_content = response.choices[0].message["content"]
                        modules.append(f"Module {i}: {module_content}")
                    
                    st.session_state.course_modules = modules
                    st.success("Complete course content generated successfully!")

if st.session_state.course_modules:
    for module in st.session_state.course_modules:
        with st.expander(module.split(':')[0]):
            st.write(module)
            pdf_file = generate_pdf(module, f"{module.split(':')[0].strip()}.pdf")
            if pdf_file:
                with open(pdf_file, "rb") as pdf:
                    b64 = base64.b64encode(pdf.read()).decode('latin1')
                st.download_button(
                    label=f"{translations['outline'][language]} {module.split(':')[0]} PDF",
                    data=b64,
                    file_name=f"{module.split(':')[0].strip()}.pdf",
                    mime="application/pdf"
                )

save_chat_history(st.session_state.messages)
