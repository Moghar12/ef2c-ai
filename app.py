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

def clean_outline(outline):
    phrases_to_remove = [
        "N'hésitez pas à adapter ce plan de cours en fonction des besoins spécifiques de vos apprenants",
        "et à ajouter des ressources complémentaires telles que des livres, des tutoriels en ligne, des projets supplémentaires, etc.",
        "Bonne chance pour votre cours !"
    ]
    for phrase in phrases_to_remove:
        outline = outline.replace(phrase, "")
    return outline.strip()

def generate_quiz(module_content, num_questions=5):
    prompt = f"Générez {num_questions} questions à choix multiples avec 4 options chacune basées sur le contenu suivant :\n\n{module_content}\n\nFormat :\nQuestion : ...\nA. Option 1\nB. Option 2\nC. Option 3\nD. Option 4\nRéponse : ..."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for generating quizzes."},
            {"role": "user", "content": prompt},
        ]
    )
    quiz_text = response.choices[0].message["content"]
    return quiz_text

def display_quiz(quiz_content):
    st.markdown("<h3 style='color: #4CAF50;'>Quiz du Module</h3>", unsafe_allow_html=True)
    questions = quiz_content.split("\n\n")
    for question in questions:
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>"
                    f"<p style='font-weight: bold;'>{question.split(':')[1].strip()}</p>"
                    f"<ul>"
                    f"<li>{question.split('A.')[1].split('B.')[0].strip()}</li>"
                    f"<li>{question.split('B.')[1].split('C.')[0].strip()}</li>"
                    f"<li>{question.split('C.')[1].split('D.')[0].strip()}</li>"
                    f"<li>{question.split('D.')[1].split('Réponse:')[0].strip()}</li>"
                    f"</ul>"
                    f"<p style='color: #FF5733;'>Réponse: {question.split('Réponse:')[1].strip()}</p>"
                    f"</div>", 
                    unsafe_allow_html=True)

def display_course_outline(outline_content):
    st.markdown("<h3 style='color: #4CAF50;'>Plan de Cours Généré</h3>", unsafe_allow_html=True)
    sections = outline_content.split("\n\n")
    for section in sections:
        st.markdown(f"<div style='background-color: #f0f8ff; padding: 15px; border-radius: 10px; margin-bottom: 15px;'>"
                    f"<p style='font-weight: bold; font-size: 16px;'>{section}</p>"
                    f"</div>", 
                    unsafe_allow_html=True)

st.set_page_config(
    page_title="EF2C - AI Generator",
    page_icon=":robot:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_dotenv()

with st.sidebar:
    language = st.selectbox("Select Language / Sélectionnez la langue", ["English", "Français"])

translations = {
    "title": {"English": "EF2C - AI Generator 🤖", "Français": "Générateur de Contenu de Cours Automatisé 🤖"},
    "course_details": {"English": "Détails du Cours 📋", "Français": "Détails du Cours 📋"},
    "course_name": {"English": "Nom du Cours", "Français": "Nom du Cours"},
    "target_audience": {"English": "Niveau Éducatif de l'Audience Cible", "Français": "Niveau Éducatif de l'Audience Cible"},
    "difficulty_level": {"English": "Niveau de Difficulté du Cours", "Français": "Niveau de Difficulté du Cours"},
    "modules": {"English": "Nombre de Chapitres", "Français": "Nombre de Modules"},
    "duration": {"English": "Durée du Cours", "Français": "Durée du Cours"},
    "generate_outline": {"English": "Générer un Plan de Cours", "Français": "Générer un Plan de Cours"},
    "start_new_course": {"English": "Start a New Course", "Français": "Commencer un Nouveau Cours"},
    "content_header": {"English": "Contenu du Cours Généré 📝", "Français": "Contenu du Cours Généré 📝"},
    "outline": {"English": "Plan du Cours", "Français": "Plan du Cours"},
    "generate_complete": {"English": "Générer le Cours Complet", "Français": "Générer le Cours Complet"},
    "modifications": {"English": "Faire des Modifications", "Français": "Faire des Modifications"},
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

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = {}

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
        ["Primaire", "Lycée", "Diplôme", "Licence", "Master"]
    )
    difficulty_level = st.radio(
        translations["difficulty_level"][language],
        ["Débutant", "Intermédiaire", "Avancé"]
    )
    num_modules = st.slider(
        translations["modules"][language],
        min_value=1, max_value=15
    )
    course_duration = st.text_input(translations["duration"][language])

    st.session_state.course_name = course_name
    st.session_state.target_audience_edu_level = target_audience_edu_level
    st.session_state.difficulty_level = difficulty_level
    st.session_state.num_modules = num_modules
    st.session_state.course_duration = course_duration

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
                st.session_state.pdf = False
                st.experimental_rerun()

with col2:
    st.header(translations["content_header"][language])
    if generate_button and "pdf" not in st.session_state:
        user_selections = f"{translations['course_name'][language]}: {course_name}\n{translations['target_audience'][language]}: {target_audience_edu_level}\n{translations['difficulty_level'][language]}: {difficulty_level}\n{translations['modules'][language]}: {num_modules}\n{translations['duration'][language]}: {course_duration}\n"
        st.session_state.messages.append({"role": "user", "content": user_selections})
        PROMPT = f"You are french Prompter. Generate in french a detailed prompt for Tabler using these inputs: 1) Course Name: {course_name} 2) Target Audience Edu Level: {target_audience_edu_level} 3) Course Difficulty Level: {difficulty_level} 4) No. of Modules: {num_modules} 5) Course Duration: {course_duration}"
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
            course_outline = clean_outline(course_outline)
            st.success("Plan du cours généré avec succès!")
            st.session_state['course_outline'] = course_outline
            st.session_state['buttons_visible'] = True

    if 'course_outline' in st.session_state and "pdf" not in st.session_state:
        with st.expander(translations["outline"][language]):
            display_course_outline(st.session_state['course_outline'])
        if 'buttons_visible' in st.session_state and st.session_state['buttons_visible']:
            button1, button2 = st.columns([1, 2])
            with button1:
                complete_course_button = st.button(translations["generate_complete"][language])
            with button2:
                modifications_button = st.button(translations["modifications"][language])
            if complete_course_button:
                with st.spinner("Génération des chapitres du cours..."):
                    modules = []
                    for i in range(1, st.session_state.num_modules + 1):
                        module_prompt = f"Generate in french detailed content for Module {i} of the course: {course_name}. The module should include an introduction, main content, examples, and a summary."
                        response = openai.ChatCompletion.create(
                            model=st.session_state["openai_model"],
                            messages=[
                                {"role": "system", "content": module_prompt},
                            ]
                        )
                        module_content = response.choices[0].message["content"]
                        modules.append(f"Module {i}: {module_content}")
                        quiz_content = generate_quiz(module_content)
                        st.session_state.quiz_questions[f"Module {i}"] = quiz_content
                    st.session_state.course_modules = modules
                    st.success("Contenu complet du cours et quiz générés avec succès!")

if st.session_state.course_modules:
    for i, module in enumerate(st.session_state.course_modules, 1):
        with st.expander(f"{module.split(':')[0]}"):
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
            if f"Module {i}" in st.session_state.quiz_questions:
                st.write("### Quiz")
                st.text(st.session_state.quiz_questions[f"Module {i}"])

save_chat_history(st.session_state.messages)
