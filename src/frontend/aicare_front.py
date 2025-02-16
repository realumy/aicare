import streamlit as st
from datetime import datetime
import json
import os
import requests
from streamlit.components.v1 import html

def generate_summary_and_questions(text):
    url = 'https://nervous-gwennie-aicare-337f70e5.koyeb.app/summary-and-questions'
    payload = {
        "text" : text
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return json.loads(response.text)

# Function to safely load JSON data
def load_journal_entries():
    if os.path.exists("journal_entries.json"):
        try:
            with open("journal_entries.json", "r") as f:
                content = f.read().strip()
                return json.loads(content) if content else []
        except json.JSONDecodeError:
            st.warning("Warning: JSON file is corrupted. Initializing with an empty journal.")
            return []
    return []

# Function to save JSON data
def save_journal_entries(entries):
    with open("journal_entries.json", "w") as f:
        json.dump(entries, f, indent=4)

# Custom HTML/JavaScript component for voice input
def voice_input(key):
    return html(
        f"""
        <div>
            <button id="start_{key}" onclick="startRecording('{key}')" class="btn">Start Voice Input</button>
            <p id="status_{key}"></p>
        </div>

        <script>
        let recognition_{key};

        function startRecording(key) {{
            if ('webkitSpeechRecognition' in window) {{
                recognition_{key} = new webkitSpeechRecognition();
                recognition_{key}.continuous = false;
                recognition_{key}.interimResults = false;
                recognition_{key}.lang = 'en-US';

                recognition_{key}.onstart = () => {{
                    document.getElementById('status_' + key).textContent = 'Listening...';
                }};

                recognition_{key}.onresult = (event) => {{
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('status_' + key).textContent = 'You said: ' + transcript;
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        value: transcript,
                        key: key
                    }}, '*');
                }};

                recognition_{key}.onerror = (event) => {{
                    document.getElementById('status_' + key).textContent = 'Error: ' + event.error;
                }};

                recognition_{key}.start();
            }} else {{
                document.getElementById('status_' + key).textContent = 'Speech recognition not supported in this browser.';
            }}
        }}
        </script>
        """,
        height=100,
    )

# App title
st.title("🏥 AI Care App: Your Health is Our Priority")

# Load previous journal entries safely
st.session_state.journal_entries = load_journal_entries()

# Sidebar with user settings and input mode selection
with st.sidebar:
    st.title("📝 User Details")
    user_name = st.text_input("Your Name", "Patient Name")
    condition = st.text_input("Current Condition/Illness", "")
    temperature = st.number_input("Temperature (°F)", 95.0, 105.0, 98.6, 0.1)
    pain_level = st.slider("Pain Level (1-10)", 1, 10, 1)
    mood = st.selectbox("Please Choose Your Current Mood", ["😊 Good", "😐 Neutral", "😔 Poor", "😣 Very Poor"])
    
    st.write("## Input Mode")
    input_mode = st.radio("Select Input Mode", ["Talk", "Load Audio File", "Text Only"])

    if st.button("Clear All Entries"):
        st.session_state.journal_entries = []
        os.remove("journal_entries.json") if os.path.exists("journal_entries.json") else None
        st.success("All entries cleared!")

# Symptoms input based on selected input mode
symptoms = ""
if input_mode == "Talk":
    st.subheader("Please talk about your medical issues")
    st.write("Symptoms (Click button below to use voice input)")
    voice_input("symptoms")
    symptoms = st.text_area("Symptoms", value=st.session_state.get("voice_symptoms", ""))

elif input_mode == "Load Audio File":
    st.subheader("Please Upload an audio file for transcription")
    audio_symptoms = st.file_uploader("Upload Audio File", type=["wav", "mp3", "m4a"], key="symptoms_audio")
    symptoms = f"Audio file uploaded: {audio_symptoms.name}" if audio_symptoms else ""

elif input_mode == "Text Only":
    st.subheader("Please Enter the text")
    symptoms = st.text_area("Symptoms")

# Save entry
if st.button("Save Entry"):
    if symptoms.strip():
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_name": user_name,
            "condition": condition,
            "temperature": temperature,
            "pain_level": pain_level,
            "symptoms": symptoms,
            "mood": mood,
        }
        response = generate_summary_and_questions(symptoms)
        st.session_state.journal_entries.append(str(response))
        save_journal_entries(st.session_state.journal_entries)
        st.success("Entry saved successfully!")
    else:
        st.error("Please provide symptoms before saving your entry")

# Display previous entries
st.subheader("Previous Entries")
for entry in reversed(st.session_state.journal_entries):
    with st.expander(f"{entry.get('user_name', 'Unknown')} - {entry.get('timestamp', '')[:10]}"):
        st.write(f"**Condition:** {entry.get('condition', 'N/A')}")
        st.write(f"**Temperature:** {entry.get('temperature', 'N/A')}°F")
        st.write(f"**Pain Level:** {entry.get('pain_level', 'N/A')}/10")
        st.write(f"**Mood:** {entry.get('mood', 'N/A')}")
        st.write("**Symptoms:**")
        st.write(entry.get('symptoms', 'No symptoms recorded'))
        st.write(f"*Recorded on: {entry.get('timestamp', 'Unknown')}*")
