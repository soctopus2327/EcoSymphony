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

# Initialize session state variables
if "real_data" not in st.session_state:
    st.session_state.real_data = {}
if "story" not in st.session_state:
    st.session_state.story = ""
if "music_bytes" not in st.session_state:
    st.session_state.music_bytes = None
if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None
if "ngos" not in st.session_state:
    st.session_state.ngos = []
if "points" not in st.session_state:
    st.session_state.points = 0
if "daily_challenges" not in st.session_state:
    st.session_state.daily_challenges = []

# Function to generate daily eco-friendly challenges
def generate_daily_challenges() -> list:
    prompt = "Give me 5 small, easy-to-do eco-friendly daily challenges that can be completed in a day."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.8
    )
    challenges = response.choices[0].message['content'].strip().split("\n")
    return [challenge.strip() for challenge in challenges if challenge.strip()]

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

# Function to fetch endangered species data
def fetch_endangered_species(city: str) -> dict:
    prompt = f"Provide details of an endangered species which is highly specific in {city}, including its name, image description, and current population."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.8
    )
    response_content = response.choices[0].message['content'].strip()
    try:
        return eval(response_content)  # Assuming the response is a JSON-like structure
    except Exception as e:
        st.error(f"Error parsing endangered species data: {e}")
        return {}

# Function to fetch NGOs using OpenAI
def fetch_nearby_ngos_with_openai(city: str, interests: list) -> list:
    prompt = (
        f"List NGOs near {city} that focus on {', '.join(interests)}. "
        "Provide the names, locations, and focus areas in JSON format as a list of dictionaries."
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.7
    )
    response_content = response.choices[0].message['content'].strip()
    
    try:
        ngo_list = eval(response_content)
        if isinstance(ngo_list, list) and all(isinstance(ngo, dict) for ngo in ngo_list):
            return ngo_list
        else:
            st.error("Unexpected response format. Could not parse NGO data.")
            return []
    except Exception as e:
        st.error(f"Error fetching NGO data: {e}")
        return []

# Streamlit UI
st.title("🌿 Eco-Symphony 🎶")
st.write("Enter a city to explore real-time environmental data, complete daily challenges, and unlock hidden content!")

city = st.text_input("Enter City Name:", placeholder="Type the name of a city...")

if st.button("Generate Environmental Data, Music, and Image"):
    st.session_state.real_data = fetch_real_data(city)
    if st.session_state.real_data:
        # Generate narrative and mood
        narrative = create_narrative(city, st.session_state.real_data)
        mood = determine_mood(st.session_state.real_data)
        
        # Generate AI story
        st.session_state.story = generate_story_with_ai(narrative, mood)

        # Generate Music and Image Based on Story and Mood
        music_description = f"{mood} mood with {st.session_state.real_data['weather_condition'].lower()} weather"
        st.session_state.music_bytes = generate_music(music_description)
        st.session_state.image_bytes = generate_image(st.session_state.story)

# Display Music and Image at the Top
if st.session_state.music_bytes:
    st.subheader("🎶 Generated Music")
    st.audio(BytesIO(st.session_state.music_bytes), format="audio/wav")

if st.session_state.image_bytes:
    st.subheader("🖼️ Generated Image")
    st.image(Image.open(BytesIO(st.session_state.image_bytes)), caption="Generated Image based on Story", use_column_width=True)

# Display Environmental Narrative and Data
if st.session_state.real_data:
    st.subheader("📜 Environmental Narrative")
    narrative = create_narrative(city, st.session_state.real_data)
    st.write(narrative)
    
    st.subheader("📊 Real Weather Data")
    st.write("Temperature (°C):", st.session_state.real_data.get("temperature", "Data not available"))
    st.write("Humidity (%):", st.session_state.real_data.get("humidity", "Data not available"))
    st.write("Weather Condition:", st.session_state.real_data.get("weather_condition", "Data not available"))

if st.session_state.story:
    st.subheader("🌈 AI-Generated Story")
    st.write(st.session_state.story)

# Daily Challenges Section
st.subheader("🏆 Daily Challenges")

if not st.session_state.daily_challenges:
    st.session_state.daily_challenges = generate_daily_challenges()

completed_challenges = []
for i, challenge in enumerate(st.session_state.daily_challenges):
    if st.checkbox(challenge, key=f"challenge_{i}"):
        completed_challenges.append(i)

# Update points based on completed challenges
st.session_state.points = len(completed_challenges) * 10  # 10 points per challenge
st.markdown(f"<h2 style='text-align: center;'>💰 Points: {st.session_state.points}</h2>", unsafe_allow_html=True)

# Function to fetch endangered species data for a region
def fetch_all_endangered_species(city: str) -> list:
    prompt = (
        f"Provide a list of endangered species found near {city}, "
        "including their names, population estimates, and descriptions. "
        "Return the data in JSON format as a list of dictionaries."
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.8
    )
    response_content = response.choices[0].message['content'].strip()
    
    try:
        species_list = eval(response_content)  # Assuming the response is a JSON-like structure
        if isinstance(species_list, list) and all(isinstance(species, dict) for species in species_list):
            return species_list
        else:
            st.error("Unexpected response format. Could not parse species data.")
            return []
    except Exception as e:
        st.error(f"Error fetching endangered species data: {e}")
        return []

# Display the endangered species section
if len(completed_challenges) == len(st.session_state.daily_challenges):
    st.success("All challenges completed! 🎉 You've unlocked the secret section!")

    # Fetch endangered species data for the user's city
    species_data_list = fetch_all_endangered_species(city)
    if species_data_list:
        st.subheader("🦋 Endangered Species in Your Region")
        
        for species_data in species_data_list:
            species_name = species_data.get('name', 'Unknown')
            st.write(f"**Species**: {species_name}")
            st.write(f"**Population**: {species_data.get('population', 'Unknown')}")
            st.write(f"**Description**: {species_data.get('description', 'No description available')}")

            # Generate an image of each endangered species
            image_description = f"Generate an image of the endangered species: {species_name}"
            species_image_bytes = generate_image(image_description)
            if species_image_bytes:
                species_image = Image.open(BytesIO(species_image_bytes))
                st.image(species_image, caption=f"Endangered Species: {species_name}", use_column_width=True)
            st.write("---")

# User's Environmental Interests Section
st.subheader("🌍 Get Involved!")
st.write("Choose your areas of interest for saving the environment:")
interests = st.multiselect(
    "Select Areas of Interest:",
    ["Afforestation", "Water Conservation", "Biodiversity Protection", "Recycling", "Climate Change Awareness"]
)

if st.button("Find Nearby NGOs"):
    if interests:
        st.session_state.ngos = fetch_nearby_ngos_with_openai(city, interests)
    else:
        st.warning("Please select at least one area of interest.")

# Display NGO information
if st.session_state.ngos:
    st.subheader("🌟 NGOs Near You")
    for ngo in st.session_state.ngos:
        st.write(f"**{ngo.get('name', 'Unknown NGO')}**")
        st.write(f"📍 Location: {ngo.get('location', 'Unknown Location')}")
        st.write(f"🌱 Focus Area: {ngo.get('focus', 'Unknown Focus Area')}")
        st.write("---")
