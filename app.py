import os
import streamlit as st
from groq import Groq
from PyPDF2 import PdfReader
import docx
from bs4 import BeautifulSoup
import re

def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")
    client = Groq(api_key=api_key)
    return client

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

def generate_abbrev_index(context):
    pattern = re.compile(
        r'([A-Za-z][A-Za-z\s&,\-’\'/]*?)\s*\(\s*([A-Z][A-Z0-9&/-]{1,15})\s*\)',
        flags=re.UNICODE
    )

    pairs = {}
    for match in pattern.finditer(context):
        phrase = match.group(1).strip(" ,;:.")
        abbr = match.group(2).strip()

        if not phrase or not abbr:
            continue

        if " " in abbr and len(abbr) > 5:
            continue

        if not (1 <= len(abbr) <= 15):
            continue

        if abbr in pairs:
            continue

        pairs[abbr] = phrase

    lines = [f"{abbr}: {pairs[abbr]}" for abbr in sorted(pairs.keys())]
    return "\n".join(lines)

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

st.title("Input to AI")

mode = st.radio(
    "Choose what you want to do:",
    ["Answer a question (Q1)", "Make abbreviation list (Q2)"]
)

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

else:
    uploaded_files = st.file_uploader(
        "Upload article(s):",
        accept_multiple_files=True
    )

    if st.button("Generate abbreviation list"):
        if not uploaded_files:
            st.error("Please upload at least one article.")
        else:
            for file in uploaded_files:
                st.subheader(f"Abbreviation list for: {file.name}")
                with st.spinner(f"Reading {file.name}..."):
                    text = extract_text(file)
                    index_text = generate_abbrev_index(text)
                st.code(index_text, language="text")
