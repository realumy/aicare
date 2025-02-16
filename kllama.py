import streamlit as st
from datetime import datetime
import json
import os
from streamlit.components.v1 import html

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
                    // Send to Streamlit
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
st.title("🏥 Health Journal with Voice Input")

# Initialize session state
if "journal_entries" not in st.session_state:
    if os.path.exists("journal_entries.json"):
        with open("journal_entries.json", "r") as f:
            st.session_state.journal_entries = json.load(f)
    else:
        st.session_state.journal_entries = []

# Voice input states
if "voice_symptoms" not in st.session_state:
    st.session_state.voice_symptoms = ""
if "voice_notes" not in st.session_state:
    st.session_state.voice_notes = ""

# Sidebar
with st.sidebar:
    st.title("📝 Journal Settings")
    user_name = st.text_input("Your Name", "Patient Name")
    condition = st.text_input("Current Condition/Illness", "")
    temperature = st.number_input("Temperature (°F)", 95.0, 105.0, 98.6, 0.1)
    pain_level = st.slider("Pain Level (1-10)", 1, 10, 1)
    
    if st.button("Clear All Entries"):
        st.session_state.journal_entries = []
        if os.path.exists("journal_entries.json"):
            os.remove("journal_entries.json")
        st.success("All entries cleared!")

# Main journal entry section
st.subheader("New Journal Entry")

# Entry form with voice input
title = st.text_input("Entry Title", "")

st.write("Symptoms (Click button below to use voice input)")
voice_input("symptoms")
symptoms = st.text_area("Symptoms", value=st.session_state.voice_symptoms)

medications = st.text_area("Medications Taken")
mood = st.selectbox("Current Mood", ["😊 Good", "😐 Neutral", "😔 Poor", "😣 Very Poor"])

st.write("Additional Notes (Click button below to use voice input)")
voice_input("notes")
notes = st.text_area("Additional Notes", value=st.session_state.voice_notes)

# Save entry
if st.button("Save Entry"):
    if title:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "user_name": user_name,
            "condition": condition,
            "temperature": temperature,
            "pain_level": pain_level,
            "symptoms": symptoms,
            "medications": medications,
            "mood": mood,
            "notes": notes
        }
        st.session_state.journal_entries.append(entry)
        with open("journal_entries.json", "w") as f:
            json.dump(st.session_state.journal_entries, f)
        st.success("Entry saved successfully!")
    else:
        st.error("Please provide a title for your entry")

# Display previous entries
st.subheader("Previous Entries")
for entry in reversed(st.session_state.journal_entries):
    with st.expander(f"{entry['title']} - {entry['timestamp'][:10]}"):
        st.write(f"**Name:** {entry['user_name']}")
        st.write(f"**Condition:** {entry['condition']}")
        st.write(f"**Temperature:** {entry['temperature']}°F")
        st.write(f"**Pain Level:** {entry['pain_level']}/10")
        st.write(f"**Mood:** {entry['mood']}")
        if entry['symptoms']:
            st.write("**Symptoms:**")
            st.write(entry['symptoms'])
        if entry['medications']:
            st.write("**Medications:**")
            st.write(entry['medications'])
        if entry['notes']:
            st.write("**Additional Notes:**")
            st.write(entry['notes'])
        st.write(f"*Recorded on: {entry['timestamp']}*")