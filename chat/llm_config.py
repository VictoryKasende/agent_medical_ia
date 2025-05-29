import os
from dotenv import load_dotenv
from httpx import stream

from langchain_community.chat_models import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# Charger les variables d'environnement depuis .env
load_dotenv()

# Clés API
openai_key = os.getenv("OPENAI_API_KEY")
# anthropic_key = os.getenv("ANTHROPIC_API_KEY")
google_key = os.getenv("GOOGLE_API_KEY")

# Vérification de la présence des clés
if not all([openai_key, google_key]):
    raise ValueError("⚠️ Les clés API OpenAI et Google doivent être définies dans le fichier .env")

# Instanciation des modèles LLM
gpt4 = ChatOpenAI(
    model="gpt-4.1",  # ou "gpt-4.1" selon ta version
    temperature=0.3,
    openai_api_key=openai_key
)

claude = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3,
    google_api_key=google_key
)

gemini = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.3,
    google_api_key=google_key
)

# Modèle utilisé pour la synthèse finale
synthese_llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.2,
    openai_api_key=openai_key,
    model_kwargs={"stream": True}
)


# import os
# import requests
# from dotenv import load_dotenv
# from langchain.schema import BaseMessage, HumanMessage, AIMessage
#
# # Charger les variables d'environnement
# load_dotenv()
#
# RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "25bf45b4famsha577558dcd485e6p1e53f5jsne9f69d176218")  # valeur par défaut
#
# def call_rapidapi_llm(message: BaseMessage, nom_model: str) -> AIMessage:
#     """ Appelle l'API RapidAPI pour simuler un modèle LLM. """
#     url = "https://chatgpt-42.p.rapidapi.com/gpt4o"
#
#     headers = {
#         "x-rapidapi-key": RAPIDAPI_KEY,
#         "x-rapidapi-host": "chatgpt-42.p.rapidapi.com",
#         "Content-Type": "application/json"
#     }
#
#     payload = {
#         "messages": [{"role": "user", "content": message.content}],
#         "web_access": False
#     }
#
#     try:
#         response = requests.post(url, json=payload, headers=headers)
#         response.raise_for_status()
#         content = response.json().get("result", "[Erreur] Réponse manquante.")
#     except Exception as e:
#         content = f"[Erreur {nom_model}] Impossible de récupérer la réponse : {e}"
#
#     return AIMessage(content=content)
#
# # Les trois modèles (simulés via RapidAPI pour le moment)
# def gpt4(messages: list[BaseMessage]) -> AIMessage:
#     return call_rapidapi_llm(messages[-1], "GPT-4")
#
# def claude(messages: list[BaseMessage]) -> AIMessage:
#     return call_rapidapi_llm(messages[-1], "Claude 3")
#
# def gemini(messages: list[BaseMessage]) -> AIMessage:
#     return call_rapidapi_llm(messages[-1], "Gemini Pro")
#
# # Synthèse (on utilise la même API, en attendant la vraie clé OpenAI)
# def synthese_llm(messages: list[BaseMessage]) -> AIMessage:
#     return call_rapidapi_llm(messages[-1], "Synthèse GPT-4")

