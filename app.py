import os
import streamlit as st
from groq import Groq
from PyPDF2 import PdfReader
import docx
from bs4 import BeautifulSoup

def get_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")
    client = Groq(api_key=api_key)
    return client

def generate_answer(client, question, context):
    prompt = f"""
You are an AI assistant.

Below is the document text (which may be empty):

{context}

If the document is empty, you may answer the question from your general knowledge.
If the document has content, use it to answer the question.

Question:
{question}

Answer:
"""
    response = llm.invoke(prompt)
    return response.content.strip()

def generate_abbrev_index(llm, context):
    prompt = f"""
Read the article and look for abbreviations written like this:

full phrase (ABBR)

Use only the abbreviations that are actually defined in the article.

For each one, write a line like:
ABBR: full phrase

Put the list in A–Z order.
Do not add anything else.

Article:
{context}

Abbreviation list:
"""
    response = llm.invoke(prompt)
    return response.content.strip()

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
            llm = get_llm()

            if uploaded_file is not None:
                context = extract_text(uploaded_file)
            else:
                context = "No document uploaded."

            with st.spinner("Thinking..."):
                answer = generate_answer(llm, question, context)

            st.header("AI Response:")
            st.write(answer)

else:
    uploaded_files = st.file_uploader(
        "Upload article(s):",
        accept_multiple_files=True
    )

    if st.button("Generate abbreviation list"):
        if not uploaded_files:
            st.error("Please upload at least one article.")
        else:
            llm = get_llm()

            for file in uploaded_files:
                st.subheader(f"Abbreviation list for: {file.name}")
                with st.spinner(f"Reading {file.name}..."):
                    text = extract_text(file)
                    index_text = generate_abbrev_index(llm, text)
                st.code(index_text, language="text")