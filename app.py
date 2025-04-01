import openai
import streamlit as st
from fpdf import FPDF
import os

# Interface de saisie de la clé API
st.sidebar.subheader("Authentification OpenAI")
user_api_key = st.sidebar.text_input("Entrez votre clé API OpenAI", type="password")

if user_api_key:
    openai.api_key = user_api_key
else:
    st.sidebar.warning("Veuillez entrer votre clé API OpenAI pour continuer.")

# Fonction pour générer un PDF
def generate_pdf(content, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', size=12)
    pdf.multi_cell(0, 10, content)
    pdf.output(filename)
    return filename

# Fonction pour générer le plan du cours
def generate_course_plan(title, duration, audience, objectives, num_chapters):
    prompt = f"""
    Crée un plan complet et très détaillé pour une formation intitulée "{title}".

    Détails :
    - Durée : {duration}
    - Public concerné : {audience}
    - Contenu de la formation : {objectives}
    - Nombre de chapitres : {num_chapters}

    Le plan doit inclure :
    1. Les prérequis nécessaires pour suivre cette formation.
    2. L'objectif final de la formation (reprenant les objectifs indiqués).
    3. Une liste des chapitres avec :
       - Un titre pour chaque chapitre.
       - Une description très détaillée pour chaque chapitre (6 à 8 lignes).
       - Une énumération des sous-chapitres avec leurs titres et une brève explication.
    4. Une conclusion résumant les points clés de la formation et comment les objectifs seront atteints.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

# Fonction pour générer le contenu détaillé d’un chapitre
def generate_chapter_content(chapter_title):
    prompt = f"""
    Crée un contenu extrêmement détaillé et structuré pour le chapitre : "{chapter_title}".
    
    Le contenu doit inclure environ 15 à 25 pages, détaillé et structuré avec exemples, cas pratiques, exercices, et bonnes pratiques.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

# Fonction pour générer un quiz
def generate_quiz(chapter_content, num_questions=5):
    prompt = f"""
    Générez un quiz de {num_questions} questions à choix multiples basé sur : {chapter_content}
    Chaque question doit avoir 4 options avec une seule réponse correcte clairement indiquée.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

# Interface principale
st.title("EF2C AI - Générateur de Contenu de Cours")
st.sidebar.header("Détails de la formation")

title = st.sidebar.text_input("Titre de la formation")
duration = st.sidebar.text_input("Durée de la formation")
audience = st.sidebar.text_area("Public concerné")
objectives = st.sidebar.text_area("Contenu de la formation")
num_chapters = st.sidebar.slider("Nombre de chapitres", 1, 15, 5)

if st.sidebar.button("Générer le plan du cours"):
    if not user_api_key:
        st.sidebar.error("Veuillez entrer votre clé API.")
    elif all([title, duration, audience, objectives]):
        with st.spinner("Génération du plan du cours..."):
            course_plan = generate_course_plan(title, duration, audience, objectives, num_chapters)
            st.session_state["course_plan"] = course_plan
            st.session_state["title"] = title
            st.session_state["duration"] = duration
            st.session_state["audience"] = audience
            st.session_state["objectives"] = objectives

            os.makedirs("cours/plan", exist_ok=True)
            plan_pdf_path = f"cours/plan/plan_{title.replace(' ', '_')}.pdf"
            generate_pdf(course_plan, plan_pdf_path)

            with open(plan_pdf_path, "rb") as pdf:
                st.download_button(
                    label="Télécharger le Plan du cours",
                    data=pdf,
                    file_name=f"plan_{title.replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )
    else:
        st.sidebar.error("Veuillez remplir tous les champs.")

if "course_plan" in st.session_state:
    st.header("Plan du cours")
    st.text(st.session_state["course_plan"])

if "chapters" not in st.session_state and "course_plan" in st.session_state:
    if st.button("Générer les chapitres"):
        if not user_api_key:
            st.error("Veuillez entrer votre clé API.")
        else:
            with st.spinner("Génération des chapitres, contenus et quiz..."):
                lines = st.session_state["course_plan"].splitlines()
                chapters = [line for line in lines if line.strip().startswith("Chapitre")]
                st.session_state["chapters"] = []

                full_course_content = f"Titre : {st.session_state['title']}\nDurée : {st.session_state['duration']}\nObjectifs : {st.session_state['objectives']}\n\nListe des chapitres :\n"

                for chapter in chapters:
                    chapter_title = chapter.strip()
                    chapter_content = generate_chapter_content(chapter_title)
                    quiz_content = generate_quiz(chapter_content)

                    st.session_state["chapters"].append((chapter_title, chapter_content, quiz_content))

                    full_course_content += f"\n\n{chapter_title}\n\n{chapter_content}\n\nQuiz:\n{quiz_content}\n\n"

                os.makedirs("cours/chapitres", exist_ok=True)
                chapters_pdf_path = f"cours/chapitres/{title.replace(' ', '_')}.pdf"
                generate_pdf(full_course_content, chapters_pdf_path)

                with open(chapters_pdf_path, "rb") as pdf:
                    st.session_state["download_link"] = pdf.read()

if "chapters" in st.session_state:
    for chapter_title, chapter_content, quiz_content in st.session_state["chapters"]:
        with st.expander(chapter_title):
            st.subheader("Contenu")
            st.write(chapter_content)
            st.subheader("Quiz")
            st.text(quiz_content)

    if "download_link" in st.session_state:
        st.download_button(
            label="Télécharger le PDF complet",
            data=st.session_state["download_link"],
            file_name=f"{title.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
