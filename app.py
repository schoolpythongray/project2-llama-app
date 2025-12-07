import os
import re
import streamlit as st
from groq import Groq
from PyPDF2 import PdfReader
import docx
from bs4 import BeautifulSoup

def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")
    return Groq(api_key=api_key)

def generate_answer(client, question, context):
    short_context = context[:8000]
    prompt = f"""
You are an AI assistant.

Below is the document text (which may be empty):

{short_context}

If the document is empty, you may answer the question from your general knowledge.
If the document has content, use it to answer the question.

Question:
{question}

Answer:
"""
    chat_completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return chat_completion.choices[0].message.content.strip()

def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def read_docx(file):
    d = docx.Document(file)
    return "\n".join([p.text for p in d.paragraphs])

def read_html(file):
    raw = file.read()
    html = raw.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(" ")

def read_txt(file):
    raw = file.read()
    return raw.decode("utf-8", errors="ignore")

def extract_text(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return read_pdf(uploaded_file)
    elif name.endswith(".docx"):
        return read_docx(uploaded_file)
    elif name.endswith(".html") or name.endswith(".htm"):
        return read_html(uploaded_file)
    else:
        return read_txt(uploaded_file)

def generate_abbrev_index(text):
    pattern = r'([A-Za-z][A-Za-z\s\-]{2,})\s*\(([A-Z]{2,})\)'
    matches = re.findall(pattern, text)
    abbrev_map = {}
    for full, abbr in matches:
        full_clean = " ".join(full.split())
        words = [w.strip(",.;:") for w in full_clean.split()]
        leading_stop = {
            "and","or","the","a","an","we","therefore","then","shows","use","using","used",
            "pending","which","that","are","is","was","were","applied","measured","replaced",
            "similar","from","of","for","in","on","with","to","by"
        }
        while words and words[0].lower() in leading_stop:
            words.pop(0)
        if not words:
            continue
        abbr_clean = abbr.strip()
        first_letter = abbr_clean[0].lower()
        start_idx = 0
        for i, w in enumerate(words):
            if w and w[0].lower() == first_letter:
                start_idx = i
                break
        words = words[start_idx:]
        if len(words) > 8:
            words = words[-8:]
        phrase = " ".join(words).lower()
        if 2 <= len(abbr_clean) <= 10 and 1 <= len(phrase.split()) <= 12:
            abbrev_map[abbr_clean] = phrase
    lines = []
    for ab in sorted(abbrev_map.keys()):
        lines.append(f"{ab}: {abbrev_map[ab]}")
    return "\n".join(lines)

st.title("Input into AI")

mode = st.radio("Choose mode:", ["Answer a question (Q1)", "Make abbreviation list (Q2)"])

if mode == "Answer a question (Q1)":
    question = st.text_input("Enter your question:")
    uploaded_file = st.file_uploader("Upload a file (optional):")
    if st.button("Ask"):
        if not question.strip():
            st.error("Please enter a question before clicking Ask.")
        else:
            try:
                client = get_client()
            except ValueError as e:
                st.error(str(e))
            else:
                if uploaded_file is not None:
                    context = extract_text(uploaded_file)
                else:
                    context = "No document uploaded."
                try:
                    with st.spinner("Thinking..."):
                        answer = generate_answer(client, question, context)
                    st.header("AI Response:")
                    st.write(answer)
                except Exception:
                    st.error("Error calling Groq API. Please try again.")

elif mode == "Make abbreviation list (Q2)":
    uploaded_files = st.file_uploader(
        "Upload one or more files:",
        accept_multiple_files=True
    )
    if st.button("Generate abbreviation list"):
        if not uploaded_files:
            st.error("Please upload at least one file.")
        else:
            for f in uploaded_files:
                text = extract_text(f)
                index = generate_abbrev_index(text)
                st.subheader(f"Abbreviations for {f.name}")
                if index.strip():
                    st.code(index)
                else:
                    st.write("No abbreviations found.")
