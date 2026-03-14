# ai_engine.py
import PyPDF2
import re
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

# Load the model only once
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

def clean_text(text):
    """Cleans text by removing special characters and extra spaces."""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text

def extract_text_from_pdf(uploaded_file):
    """Extracts raw text from a PDF file."""
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def calculate_similarity(resume_text, job_descriptions):
    """Calculates cosine similarity between resume and a list of jobs."""
    model = load_model()
    resume_embedding = model.encode(resume_text)
    job_embeddings = model.encode(job_descriptions)
    
    # Calculate scores
    scores = cosine_similarity([resume_embedding], job_embeddings)[0]
    return scores

skills_list = [
    "python","java","c++","machine learning","deep learning",
    "data science","sql","tensorflow","pytorch","nlp",
    "pandas","numpy","scikit-learn","docker","kubernetes",
    "aws","git","flask","django","react","javascript"
]

def extract_skills(text):
    text = text.lower()
    found_skills = []

    for skill in skills_list:
        if skill in text:
            found_skills.append(skill)

    return found_skills