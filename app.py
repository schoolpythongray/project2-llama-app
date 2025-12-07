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

Below is the document text (it may be empty):

{context}

If the document is empty, you may answer the question from your general knowledge.
If the document has content, use it to answer the question.

Question:
{question}

Answer:
"""

    chat_completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return chat_completion.choices[0].message.content.strip()


def read_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

def read_docx(file):
    d = docx.Document(file)
    paragraphs = [p.text for p in d.paragraphs]
    return "\n".join(paragraphs)

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

question = st.text_input("Enter your question:")

uploaded_file = st.file_uploader("Upload attachment:")

if st.button("Ask"):
    if not question.strip():
        st.error("Please enter a question before clicking Ask.")
    else:
        try:
            client = get_client()
        except Exception as e:
            st.error(f"Error initializing LLM client: {e}")
        else:
            if uploaded_file is not None:
                context = extract_text(uploaded_file)
            else:
                context = ""

            with st.spinner("Thinking..."):
                answer = generate_answer(client, question, context)

            st.header("AI Response:")
            st.write(answer)
