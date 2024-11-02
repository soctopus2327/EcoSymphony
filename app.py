import streamlit as st
import requests
import openai
from io import BytesIO
from PIL import Image

# Set page configuration as the first Streamlit command
st.set_page_config(page_title="Eco-Symphony", page_icon="🌱", layout="centered")

# Set API keys from Streamlit Secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
OPENWEATHER_API_KEY = st.secrets["OPENWEATHER_API_KEY"]
HUGGINGFACE_API_KEY = st.secrets["HUGGINGFACE_API_KEY"]

# Hugging Face API URLs
MUSICGEN_API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
IMAGEGEN_API_URL = "https://api-inference.huggingface.co/models/Artples/LAI-ImageGeneration-vSDXL-2"

# Headers for Hugging Face API requests
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}

# Inject custom CSS for green theme
st.markdown("""
    <style>
    body {
        background-color: #ffffff;
    }
    .stApp {
        color: #2e7d32;
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        background-color: #66bb6a;
        color: #fff;
        font-weight: bold;
    }
    .stTextInput>div>input {
        background-color: #e8f5e9;
        color: #2e7d32;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown p {
        color: #388e3c;
    }
    .stMarkdown h2 {
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Function to fetch weather data
def fetch_real_data(city: str) -> dict:
    weather_url = f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric'
    weather_response = requests.get(weather_url)
    if weather_response.status_code != 200:
        st.error("Error fetching weather data.")
        return {}
    weather_data = weather_response.json()
    return {
        "temperature": weather_data['main'].get('temp', 'Data not available'),
        "humidity": weather_data['main'].get('humidity', 'Data not available'),
        "weather_condition": weather_data['weather'][0].get('main', 'Data not available')
    }

# Function to determine mood based on weather data
def determine_mood(data: dict) -> str:
    weather_condition = data["weather_condition"].lower()
    temperature = data["temperature"]
    if "rain" in weather_condition:
        return "rainy"
    elif "clear" in weather_condition and temperature > 25:
        return "sunny"
    elif "cloud" in weather_condition:
        return "cloudy"
    elif temperature < 15:
        return "cool"
    else:
        return "neutral"

# Function to create a narrative
def create_narrative(city: str, data: dict) -> str:
    return f"In {city}, the weather is {data['weather_condition']} with a temperature of {data['temperature']}°C."

# Function to generate a story using OpenAI
def generate_story_with_ai(narrative: str, mood: str) -> str:
    messages = [
        {"role": "system", "content": "You are a creative storyteller using characters and imagery."},
        {"role": "user", "content": f"{narrative} The mood is '{mood}', write a story about how the environment feels in 50 words."}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].message['content'].strip()

# Function to generate simulated environmental data
def generate_simulated_data(city: str) -> dict:
    prompt = (
        f"Generate simulated environmental data for {city} in JSON format with fields:\n"
        f"1. AQI\n2. Deforestation Rate\n3. Water Quality\n4. Biodiversity Impact"
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.8
    )
    response_content = response.choices[0].message['content'].strip()
    try:
        return eval(response_content)
    except Exception as e:
        st.error(f"Error parsing simulated data: {e}")
        return {}

# Function to generate music from Hugging Face API
def generate_music(description: str) -> bytes:
    payload = {"inputs": description}
    response = requests.post(MUSICGEN_API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        st.error(f"Error generating music: {response.status_code} {response.text}")
        return None
    return response.content

# Function to generate an image based on the story
def generate_image(description: str) -> bytes:
    payload = {"inputs": description}
    response = requests.post(IMAGEGEN_API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        st.error(f"Error generating image: {response.status_code} {response.text}")
        return None
    return response.content

# Function to create a dynamic music description
def create_music_description(data):
    mood = data["mood"]
    weather_condition = data["real_data"]["weather_condition"].lower()
    temperature = data["real_data"]["temperature"]
    
    description = f"{mood} mood with {weather_condition} weather"
    
    if temperature < 10:
        description += " and a cold ambiance"
    elif 10 <= temperature <= 20:
        description += " and a cool feel"
    elif 20 < temperature <= 30:
        description += " and a warm, lively environment"
    else:
        description += " and a hot, energetic vibe"
    
    return description

# Streamlit UI
st.title("🌿 Eco-Symphony 🎶")
st.write("Enter a city to explore real-time environmental data, generate AI-created music, and see an AI-generated image based on the story.")

# Input box for city
city = st.text_input("Enter City Name:", placeholder="Type the name of a city...")

# Generate Button
if st.button("Generate Environmental Narrative, Music, and Image"):
    # Fetch real weather data
    real_data = fetch_real_data(city)
    
    if real_data:
        # Generate narrative and mood
        narrative = create_narrative(city, real_data)
        mood = determine_mood(real_data)
        
        # Generate AI story
        story = generate_story_with_ai(narrative, mood)

        # Generate Music and Image Based on Story and Mood
        music_description = create_music_description({"mood": mood, "real_data": real_data})
        
        st.subheader("🎶 Generated Music")
        st.write(f"Generating music based on: {music_description}")
        music_bytes = generate_music(music_description)
        if music_bytes:
            audio_data = BytesIO(music_bytes)
            st.audio(audio_data, format="audio/wav")

        st.subheader("🖼️ Generated Image")
        st.write("Generating image based on the story...")
        image_bytes = generate_image(story)
        if image_bytes:
            image = Image.open(BytesIO(image_bytes))
            st.image(image, caption="Generated Image based on Story", use_column_width=True)

        # Display Environmental Narrative and Data
        st.subheader("📜 Environmental Narrative")
        st.write(narrative)
        
        st.subheader("💭 Mood")
        st.write(f"**Mood**: {mood}")

        st.subheader("🌈 AI-Generated Story")
        st.write(story)

        # Generate and Display Simulated Environmental Data
        simulated_data = generate_simulated_data(city)
        simulated_inner_data = simulated_data.get("data", {})
        st.subheader("📊 Real Weather Data")
        st.write("Temperature (°C):", real_data.get("temperature", "Data not available"))
        st.write("Humidity (%):", real_data.get("humidity", "Data not available"))
        st.write("Weather Condition:", real_data.get("weather_condition", "Data not available"))

        st.subheader("🧪 Simulated Environmental Data")
        st.write("AQI:", simulated_inner_data.get("AQI", "Data not available"))
        st.write("Deforestation Rate:", simulated_inner_data.get("Deforestation Rate", "Data not available"))
        st.write("Water Quality:", simulated_inner_data.get("Water Quality", "Data not available"))
        st.write("Biodiversity Impact:", simulated_inner_data.get("Biodiversity Impact", "Data not available"))
