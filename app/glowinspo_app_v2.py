import streamlit as st
import pandas as pd
import os
import re
import time
import anthropic
import random

# -----------------------------
# CONFIG
# -----------------------------

st.set_page_config(page_title="GlowInspo", layout="wide")

# -----------------------------
# LOAD DATA (CACHED)
# -----------------------------

@st.cache_data
def load_data():
    df = pd.read_csv("data/glowinspo_outfits_retagged_v2.csv")

    df["tone_list"] = df["tone_tags_v2"].apply(
        lambda x: [t.strip().lower() for t in str(x).split(",")]
    )

    df["energy_bucket"] = df["energy_bucket"].str.strip()

    return df

df = load_data()

# -----------------------------
# SESSION STATE INIT
# -----------------------------

if "current_samples" not in st.session_state:
    st.session_state.current_samples = None

if "response_text" not in st.session_state:
    st.session_state.response_text = None

if "shown_images" not in st.session_state:
    st.session_state.shown_images = set()

if "mood_history" not in st.session_state:
    st.session_state.mood_history = []

if "feedback_mode" not in st.session_state:
    st.session_state.feedback_mode = None

# -----------------------------
# LANDING
# -----------------------------

st.markdown("""
# 🌿 GlowInspo

### Dress for the energy you want to bring into the day.

Before you grab whatever’s closest,
pause for a second.

How are you feeling?
A little off? A little nervous? A little “let’s do this”?

GlowInspo turns getting dressed into a tiny daily reset —
so you can pick something that helps you feel more like yourself.

No trends.
No pressure.
Just you, but aligned.
""")

st.markdown("Ready? Let’s check in.")

# -----------------------------
# USER INPUT
# -----------------------------

col1, col2 = st.columns(2)

mood = col1.text_input("How are you arriving today?")

energy_direction = col2.radio(
    "How do you want to show up?",
    ["Soften", "Stabilize", "Brighten", "Amplify"]
)

# -----------------------------
# CLAUDE FUNCTION
# -----------------------------

def get_outfit_directions(mood, energy_direction):

    if "ANTHROPIC_API_KEY" not in os.environ:
        return "Claude not configured. Please set ANTHROPIC_API_KEY."

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""
    You are a warm, emotionally intelligent friend helping someone get dressed with intention.

    Current mood:
    {mood}

    Desired energy direction:
    {energy_direction}

    Energy buckets:
    Soften, Stabilize, Brighten, Amplify

    Tone tags (choose 2–3 max from this list only):
    muted, minimal, soft, neutral, flowy,
    structured, balanced, earth-toned, steady, tailored,
    warm, playful, lively, colorful, expressive-light,
    bold, dramatic, elevated, commanding, statement

    Keep the response under 150 words.

    Structure exactly like this:

    Arrival:
    One sentence acknowledging how they feel.

    Reframe:
    1–2 sentences guiding them toward their chosen energy direction.

    Direction:
    Short outfit guidance aligned with the energy direction.

    Energy:
    One of Soften, Stabilize, Brighten, Amplify

    Tones:
    2–3 tone tags from the allowed list only.
    """

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text

# -----------------------------
# HELPER
# -----------------------------

def extract_section(text, section_name):
    pattern = rf"{section_name}:\s*(.*?)(?=\n[A-Z][a-z]+:|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

# -----------------------------
# GENERATE RITUAL
# -----------------------------

if st.button("✨ Start My 2-Minute Reset") and mood:

    st.markdown("Take one slow breath.")
    time.sleep(1)

    with st.spinner("Tuning into your emotional frequency..."):
        st.session_state.response_text = get_outfit_directions(mood, energy_direction)

# -----------------------------
# DISPLAY RITUAL
# -----------------------------

if st.session_state.response_text:

    text = st.session_state.response_text

    st.markdown("## 🌿 Your Morning Reset")

    st.markdown("### 🌧 Arrival")
    st.markdown(extract_section(text, "Arrival"))

    st.markdown("### 🌤 Reframe")
    st.markdown(extract_section(text, "Reframe"))

    st.markdown("### 👗 Direction")
    st.markdown(extract_section(text, "Direction"))

    # -------------------------
    # SURFACE PAST MATCH
    # -------------------------

    past_matches = [
        entry for entry in st.session_state.mood_history
        if entry["energy"] == energy_direction
    ]

    if past_matches:
        st.markdown("## 🌈 Last time you chose this energy...")
        last_entry = past_matches[-1]
        st.image(last_entry["user_photo"], width=220)
        st.markdown(f"🌿 **{last_entry['label']}**")

    # -------------------------
    # EXTRACT TONES
    # -------------------------

    match = re.search(r"Tones:\s*(.*)", text, re.IGNORECASE)
    tones = []

    if match:
        tone_line = match.group(1)
        tones = [t.strip().lower() for t in tone_line.split(",")]

    filtered = df[df["energy_bucket"] == energy_direction]

    if tones and not filtered.empty:
        filtered = filtered.copy()
        filtered["match_score"] = filtered["tone_list"].apply(
            lambda tl: len(set(tl).intersection(set(tones)))
        )
        filtered = filtered.sort_values("match_score", ascending=False)

    if not filtered.empty:

        available = filtered[~filtered["image_url"].isin(st.session_state.shown_images)]

        if available.empty:
            st.session_state.shown_images.clear()
            available = filtered

        # -----------------------------------
        # CATEGORY-AWARE SAMPLING (FROZEN UNTIL NOT QUITE)
        # -----------------------------------

        if st.session_state.current_samples is None:

            grouped = available.groupby("category")
            samples_list = []

            for category, group in grouped:
                take_n = min(2, len(group))
                samples_list.append(group.sample(take_n))

            samples = pd.concat(samples_list)

            if len(samples) > 6:
                samples = samples.sample(6)
            elif len(samples) < 6:
                remaining = available[~available["image_url"].isin(samples["image_url"])]
                if not remaining.empty:
                    extra = remaining.sample(min(6 - len(samples), len(remaining)))
                    samples = pd.concat([samples, extra])

            st.session_state.current_samples = samples

        # Always use frozen samples
        samples = st.session_state.current_samples

        # -----------------------------------
        # DISPLAY SUGGESTIONS
        # -----------------------------------

        st.markdown("### ✨ Let this spark something.")

        cols = st.columns(3)

        for i, (idx, row) in enumerate(samples.iterrows()):
            with cols[i % 3]:
                st.image(row["image_url"], width=220)

        # -----------------------------------
        # FEEDBACK OPTIONS
        # -----------------------------------

        st.markdown("---")
        st.markdown("### 💭 Did this spark something?")

        col1, col2, col3 = st.columns(3)

        if col1.button("✨ Inspired – Yes"):
            st.session_state.feedback_mode = "inspired"

        if col2.button("🔄 Not quite"):
            st.session_state.feedback_mode = "not_quite"

        if col3.button("💅 I styled something myself"):
            st.session_state.feedback_mode = "self_styled"

        # -----------------------------------
        # HANDLE MODES
        # -----------------------------------

        if st.session_state.feedback_mode == "inspired":

            st.success("Love that. Don’t forget to add your OOTD.")

            uploaded_file = st.file_uploader(
                "Upload a photo of your outfit",
                type=["jpg", "jpeg", "png"],
                key="upload_inspired"
            )

            if uploaded_file and st.button("Save this look", key="save_inspired"):

                entry = {
                    "mood": mood,
                    "energy": energy_direction,
                    "label": f"{mood.title()} + {energy_direction}",
                    "tones": tones,
                    "user_photo": uploaded_file
                }


                st.session_state.mood_history.append(entry)
                st.session_state.feedback_mode = None
                st.success("You showed up for yourself today ✨")

        if st.session_state.feedback_mode == "self_styled":

            st.success("Love that. Show me what made you feel good.")

            uploaded_file = st.file_uploader(
                "Upload your look",
                type=["jpg", "jpeg", "png"],
                key="upload_self"
            )

            if uploaded_file and st.button("Save this look", key="save_self"):

                entry = {
                    "mood": mood,
                    "energy": energy_direction,
                    "label": f"{mood.title()} + {energy_direction}",
                    "tones": tones,
                    "user_photo": uploaded_file
                }

                st.session_state.mood_history.append(entry)
                st.session_state.feedback_mode = None
                st.success("Saved to your emotional memory ✨")

        if st.session_state.feedback_mode == "not_quite":
            st.info("No worries. Let’s try another take.")
            st.session_state.shown_images.clear()
            st.session_state.current_samples = None
            st.session_state.feedback_mode = None
            st.rerun()
# -----------------------------
# MEMORY VIEW
# -----------------------------

if st.session_state.mood_history:

    st.markdown("---")
    st.markdown("## 🌈 Your Emotional Memory")

    cols = st.columns(3)

    for i, entry in enumerate(st.session_state.mood_history):
        with cols[i % 3]:
            st.image(entry["user_photo"], width=220)
            st.markdown(f"🌿 **{entry['label']}**")
