from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import httpx

# 1. Setup the Client (Using your GenAI Lab configuration)
client = httpx.Client(verify=False)

# NOTE: For strict JSON formatting required by the UI, GPT-4o is highly recommended. 
# You can easily swap this back to DeepSeek-V3 if preferred.
llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure/genailab-maas-gpt-4o", 
    api_key="sk-Mmdb57oKOaC2wefGLzmSTQ", # Replace during the event
    http_client=client
)

# 2. Define the Structured Output Parser
# This ensures LangChain automatically converts the AI's text string into a Python Dictionary
json_parser = JsonOutputParser()

# 3. Create the System Prompt (The "Rules")
# This prompt forces the AI to output the exact structure our Streamlit UI needs.
# 3. Create the System Prompt (The "Rules")
SYSTEM_PROMPT = """
You are an expert, highly organized AI Travel Itinerary Assistant.
Your goal is to process the user's travel request and output a detailed, realistic day-by-day itinerary.

CRITICAL RULE: You must ONLY output valid JSON. Do not include introductory text, conversational filler, or markdown block ticks (like ```json).

The JSON MUST exactly match this structure:
{{
    "title": "A catchy title for the trip (e.g., 3 Days of Parisian Art)",
    "days": [
        {{
            "day_label": "Day 1 - Theme of the day (e.g., Arrival & Classics)",
            "activities": [
                {{
                    "time": "09:00", 
                    "title": "Activity Name", 
                    "desc": "A brief 1-2 sentence description of what to do."
                }}
            ]
        }}
    ]
}}
"""

# 4. Build the LangChain Prompt Template
prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "User Request: {user_request}\n\nPlease generate the JSON itinerary.")
])

# 5. Chain it all together
# Flow: Prompt -> LLM -> JSON Parser -> Python Dictionary
itinerary_chain = prompt_template | llm | json_parser


def generate_itinerary(user_input: str):
    """
    This is the function the Streamlit UI will call.
    It takes the user text and returns the formatted dictionary.
    """
    try:
        # Run the chain
        result_dict = itinerary_chain.invoke({"user_request": user_input})
        
        # Create a friendly chat message to show in the left panel
        chat_message = "I've processed your request and generated a structured itinerary. Check the panel on the right!"
        
        return chat_message, result_dict
        
    except Exception as e:
        # Fallback just in case the AI hallucinates or API fails
        print(f"Error calling LLM: {e}")
        return "I encountered an error while formatting the trip. Please try again.", None