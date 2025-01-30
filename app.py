import openai
import streamlit as st
from dotenv import load_dotenv
import os
from fpdf import FPDF

st.sidebar.header("Configuration de l'API")
api_key = st.sidebar.text_input("Entrez votre clé API OpenAI", type="password")

if api_key:
    openai.api_key = api_key
else:
    st.sidebar.warning("Veuillez entrer votre clé API pour continuer.")

def generate_pdf(content, filename):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', size=12)
    pdf.multi_cell(0, 10, content)
    pdf.output(filename)
    return filename

def generate_course_plan(title, duration, audience, num_chapters):
    prompt = f"""
    Crée un plan complet et très détaillé pour une formation intitulée "{title}".
    
    Détails :
    - Durée : {duration}
    - Public concerné : {audience}
    - Nombre de chapitres : {num_chapters}
    
    Le plan doit inclure :
    1. Les prérequis nécessaires pour suivre cette formation.
    2. L'objectif final de la formation.
    3. Une liste des chapitres avec :
       - Un titre pour chaque chapitre.
       - Une description très détaillée pour chaque chapitre (6 à 8 lignes).
       - Une énumération des sous-chapitres avec leurs titres et une brève explication.
    4. Une conclusion résumant les points clés de la formation.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

def generate_chapter_content(chapter_title):
    prompt = f"""
    Crée un contenu extrêmement détaillé et structuré pour le chapitre : "{chapter_title}".
    
    Le contenu doit inclure environ **15 à 25 pages** en respectant les points suivants :
    1. Une introduction détaillée expliquant les concepts clés abordés.
    2. Des sous-chapitres organisés de la manière suivante :
       - Chaque sous-chapitre doit avoir un titre clair.
       - Une explication détaillée du concept abordé (1 à 2 pages).
       - Des sous-sections dans chaque sous-chapitre, avec des explications approfondies et des exemples concrets.
       - Des cas d’usage réels et des scénarios pratiques illustrant les concepts (1 à 2 pages par cas).
       - Des illustrations ou des analogies pour clarifier les concepts complexes.
    3. Des blocs de code formatés comme exemples pratiques (code SQL, Python, ou autre selon le contexte) avec explications détaillées.
    4. Chapitre sur la programmtion des sites adapte aux handicapes
    5. Des exercices pratiques pour chaque sous-chapitre, avec des instructions claires.
    6. Une étude de cas complète couvrant les concepts du chapitre, avec une solution détaillée (environ 4 à 5 pages).
    7. Une section "Bonnes pratiques" expliquant comment appliquer les concepts efficacement dans des situations réelles.
    8. Une conclusion développée récapitulant les points essentiels du chapitre et suggérant des lectures complémentaires.
    
    Attention : assurez-vous que le contenu soit suffisamment détaillé pour atteindre environ 15 à 25 pages.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

def generate_quiz(chapter_content, num_questions=5):
    prompt = f"""
    Générez un quiz de {num_questions} questions à choix multiples (QCM) basé sur le contenu suivant :
    
    {chapter_content}
    
    Chaque question doit être claire, bien formulée et contextuelle. Fournissez 4 options de réponse, avec une seule bonne réponse.
    Format attendu :
    Question : ...
    A. Option 1
    B. Option 2
    C. Option 3
    D. Option 4
    Réponse : ...
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

st.title("EF2C AI - Générateur de Contenu de Cours")
st.sidebar.header("Détails de la formation")

title = st.sidebar.text_input("Titre de la formation")
duration = st.sidebar.text_input("Durée de la formation")
audience = st.sidebar.text_area("Public concerné")
num_chapters = st.sidebar.slider("Nombre de chapitres", min_value=1, max_value=15, value=5)

if st.sidebar.button("Générer le plan du cours"):
    if all([title, duration, audience]):
        with st.spinner("Génération du plan du cours..."):
            course_plan = generate_course_plan(title, duration, audience, num_chapters)
            st.session_state["course_plan"] = course_plan
            st.session_state["title"] = title
            st.session_state["duration"] = duration
            st.session_state["audience"] = audience
            
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

if "course_plan" in st.session_state:
    st.header("Plan du cours")
    st.text(st.session_state["course_plan"])

if "chapters" not in st.session_state and "course_plan" in st.session_state:
    if st.button("Générer les chapitres"):
        with st.spinner("Génération des chapitres, contenus et quiz..."):
            lines = st.session_state["course_plan"].splitlines()
            chapters = [line for line in lines if line.strip().startswith("Chapitre")]
            st.session_state["chapters"] = []

            full_course_content = f"Titre : {st.session_state['title']}\nDurée : {st.session_state['duration']}\n\nListe des chapitres :\n"

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
