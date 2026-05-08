import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from google import genai
from google.genai import types

app = FastAPI()

# Enable CORS for local testing if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from dotenv import load_dotenv

load_dotenv()

# Use the API key provided via environment variable
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is missing")
client = genai.Client(api_key=API_KEY)

class Message(BaseModel):
    role: str
    text: str

class ChatRequest(BaseModel):
    history: List[Message]

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    system_instruction = """You are a travel planning & experience engine expert - an expert AI copilot 

Your goal is to help users plan the perfect trip by gathering preferences and constraints step by step, then delivering sharp, actionable advice.

Rules:
Do not give answers more than 80 words
Do not give vague answers
Ask one clarification questions to give the best advise 
Adapt and replan if the user mentions changes (weather, budget shifts, new interests)

Ask the questions step by step not at once

Conversation flow — collect in this order:
1. Destination (city or country)
2. Travel dates and trip duration
3. Budget range (budget / mid-range / luxury)
4. Group type (solo / couple / family / friends) and size
5. Food preference (vegetarian / non-vegetarian / vegan)
6. Travel style (relaxed / adventure / culture / nightlife / mix)

Once you have all 6 inputs, provide,  Top 3 places to explore (with a one-line reason each)
Top 2 local food dishes and where to try them
Top 2 hotels matching their budget (name + why it fits)
One practical travel tip specific to the destination

If the user mentions a constraint or change mid-conversation (e.g. "we have less budget now" or "it might rain"), replan relevant suggestions immediately."""

    contents = []
    for msg in req.history:
        contents.append(
            types.Content(
                role=msg.role,
                parts=[types.Part.from_text(text=msg.text)]
            )
        )

    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level="HIGH",
        ),
        system_instruction=[
            types.Part.from_text(text=system_instruction)
        ]
    )

    def event_stream():
        response_stream = client.models.generate_content_stream(
            model="gemini-3-flash-preview",
            contents=contents,
            config=generate_content_config,
        )
        try:
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text.encode('utf-8')
        except Exception as e:
            yield f"\n\nError: {str(e)}".encode('utf-8')

    return StreamingResponse(event_stream(), media_type="text/plain")

# Mount frontend
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))

@app.get("/")
async def root():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(frontend_dir, "index.html"))

app.mount("/", StaticFiles(directory=frontend_dir), name="frontend")
