import requests
from bs4 import BeautifulSoup
import os
import numpy as np
import faiss
from mistralai import Mistral, UserMessage
import time
import streamlit as st

api_key = st.secrets["MISTRAL_API_KEY"]


urls = [
    "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/student-conduct-policy",
    "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/udst-policies-and-procedures/academic-schedule-policy",
    "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/student-attendance-policy",
    "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/admissions-policy",
    "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/registration-policy",
    "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/sport-and-wellness-facilities-and",
    "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/udst-policies-and-procedures/international-student-policy",
    "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/udst-policies-and-procedures/student-counselling-services-policy",
    "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/scholarship-and-financial-assistance",
    "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/use-library-space-policy"
]

def fetch_policy_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Remove extra spaces, newlines, and non-ASCII characters
    text = soup.get_text(separator=" ").replace("\n", " ").strip()
    text = " ".join(text.split())  # Normalize extra spaces
    
    return text


policies = {url: fetch_policy_text(url) for url in urls}
#updated

chunk_size = 512
policy_chunks = []
policy_sources = []

for url, text in policies.items():
    chunks = [text[i: i + chunk_size] for i in range(0, len(text), chunk_size)]
    policy_chunks.extend(chunks)
    policy_sources.extend([url] * len(chunks))



def get_text_embedding(list_txt_chunks, batch_size=50):  
    client = Mistral(api_key=api_key)
    embeddings = []

    for i in range(0, len(list_txt_chunks), batch_size):
        batch = list_txt_chunks[i:i + batch_size]

        retries = 3  # Allow 3 retries in case of failure
        while retries > 0:
            try:
                embeddings_batch_response = client.embeddings.create(
                    model="mistral-embed",
                    inputs=batch
                )
                batch_embeddings = [e.embedding for e in embeddings_batch_response.data]
                embeddings.extend(batch_embeddings)
                time.sleep(2)  # Add delay to prevent hitting rate limit
                break  # Exit retry loop if successful

            except Exception as e:
                print(f"Error in batch {i}-{i+batch_size}: {e}")
                retries -= 1
                if "429" in str(e):
                    print("Rate limit hit! Waiting for 10 seconds before retrying...")
                    time.sleep(10)  # Wait longer before retrying

    return embeddings



text_embeddings = get_text_embedding(policy_chunks)

if not text_embeddings:
    print("No embeddings were retrieved. Exiting program.")
    exit()  # Stop execution if embeddings are missing

#Directly convert list of embeddings into a NumPy array
embeddings = np.array(text_embeddings)

d = len(embeddings[0])
index = faiss.IndexFlatL2(d)
index.add(embeddings)


def retrieve_relevant_chunks(query):
    query_embedding = np.array([get_text_embedding([query])[0]])
    D, I = index.search(query_embedding, k=6)  # Start with max depth
    
    # Convert FAISS distances to confidence scores
    confidence_scores = 1 / (1 + D[0])  # Normalize scores (higher = better)
    
    # Determine top_k dynamically
    if confidence_scores[0] > 0.9:  # High confidence
        top_k = 2
    elif confidence_scores[0] > 0.7:  # Medium confidence
        top_k = 4
    else:  # Low confidence, expand retrieval
        top_k = 6

    retrieved_chunks = [policy_chunks[i] for i in I[0][:top_k] if i < len(policy_chunks)]
    retrieved_chunks = [chunk for chunk in retrieved_chunks if len(chunk) > 30]  # Ignore cut-off responses
    
    return retrieved_chunks

# Dictionary to map policies to their URLs
policy_links = {
    "Student attendance policy": "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/student-attendance-policy",
    "Registration policy": "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/registration-policy",
    "Library space policy": "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/use-library-space-policy",
    "Student conduct policy": "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/student-conduct-policy",
    "Admissions Policy": "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/admissions-policy",
    "Scholarship Policy": "https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/scholarship-and-financial-assistance",
    "Academic Schedule Policy":"https://www.udst.edu.qa/about-udst/institutional-excellence-ie/udst-policies-and-procedures/academic-schedule-policy",
    "Sports and Wellness Policy":"https://www.udst.edu.qa/about-udst/institutional-excellence-ie/policies-and-procedures/sport-and-wellness-facilities-and",
    "International Student Policy":"https://www.udst.edu.qa/about-udst/institutional-excellence-ie/udst-policies-and-procedures/international-student-policy",
    "Student Counselling Services Policy":"https://www.udst.edu.qa/about-udst/institutional-excellence-ie/udst-policies-and-procedures/student-counselling-services-policy",
}


urls = [


]


def generate_response(user_query):
    retrieved_chunks = retrieve_relevant_chunks(user_query)

    # Identify the MOST relevant policy using query context
    query_keywords = user_query.lower().split()
    relevant_policies = set()

    # Find policies that match query keywords
    for policy_name, policy_url in policy_links.items():
        policy_keywords = policy_name.lower().split()
        # Check if any policy keyword exists in user query
        if any(keyword in query_keywords for keyword in policy_keywords):
            relevant_policies.add(policy_name)

    # Construct prompt
    prompt = f"""
    You are an AI assistant providing official university policy information. 
    Provide **concise, to-the-point answers**. Only include the most relevant details.

    Context:
    ---------------------
    {' '.join(retrieved_chunks)}
    ---------------------

    - Answer the user query in **2-3 sentences max**.
    - If there are **specific steps**, summarize them in bullet points.
    - Do NOT include unnecessary background details.
    - If certain details are missing, mention where users can find them.

    User Query: {user_query}
    Answer:
    """

    client = Mistral(api_key=api_key)
    messages = [UserMessage(content=prompt)]
    
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=messages
    )
    answer = response.choices[0].message.content.strip()

    # Append policy link if any policy keywords are detected
    if relevant_policies:
        # Find policy with highest keyword match
        best_match = max(relevant_policies, 
                         key=lambda x: sum(word in user_query.lower() for word in x.lower().split()))
        policy_links_html = f"🔗 **More Information:** [Read the full {best_match} here]({policy_links[best_match]})"
        answer = f"{answer}\n\n{policy_links_html}"
    
    return answer





# if __name__ == "__main__":
#     print("Testing RAG system...")

#     test_queries = [
#         "What is the student attendance policy?",
#         "How do I register for courses?",
#         "What are the rules for using the library space?"
#     ]

#     for query in test_queries:
#         print("\n🔍 User Query:", query)
#         response = generate_response(query)
#         print("🤖 AI Response:\n", response)
