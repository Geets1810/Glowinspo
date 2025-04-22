import streamlit as st
import pandas as pd
import random
import os
from collections import defaultdict

# Load the tone-tagged dataset
df = pd.read_csv("../data/glowinspo_outfits_tone_multi.csv")

st.set_page_config(page_title="GlowInspo - Dress for Mood", layout="wide")

if "moodboard" not in st.session_state:
    st.session_state.moodboard = []
st.markdown("""
<style>
.fixed-header {
    position: fixed;
    top: 0;
    width: 100%;
    background-color: #0e1117;
    z-index: 1000;
    padding: 50px 30px 20px;
    border-bottom: 1px solid #444;
}
.spacer {
    margin-top: 120px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='fixed-header' style='display: flex; align-items: baseline;'>
    <span style='font-size: 2.4rem; padding-right: 12px;'>🌈</span>
    <div>
        <h1 style='color:white; margin: 0; font-size: 2.2rem; padding-top: 6px;'>GlowInspo</h1>
        <h3 style='color:white; margin: 0;'>Let your outfit match your emotional tone.</h3>
    </div>
</div>
<div class='spacer'></div>
""", unsafe_allow_html=True)

mood_buttons = [
    ("Calm", "calm"),
    ("Grounded", "grounding"),
    ("Playful", "playful"),
    ("Reflective", "reflective"),
    ("Uplifted", "uplifting")
]

st.markdown("### How are you feeling today?")
cols = st.columns(len(mood_buttons))
for i, (label, tone) in enumerate(mood_buttons):
    if cols[i].button(label):
        st.session_state.selected_tone = tone
        filtered = df[df['tone_tags_custom'].str.contains(tone, case=False, na=False)]
        st.session_state.sampled_rows = filtered.sample(min(9, len(filtered)))

# Show results based on selected tone
selected_tone = st.session_state.get("selected_tone")

if selected_tone:
    filtered = df[df['tone_tags_custom'].str.contains(selected_tone, case=False, na=False)]

    if not filtered.empty:
        samples = st.session_state.get("sampled_rows", pd.DataFrame())
        cols = st.columns(3)

        for i, (idx, row) in enumerate(samples.iterrows()):
            with cols[i % 3]:
                st.image(row["image_url"], width=200)
                if st.button("💾 Save to Moodboard", key=f"save_{row['image_url']}"):
                    item = {
                        "image_url": row["image_url"],
                        "tone_tag": row["tone_tags_custom"],
                        "description": row["image_description"]
                    }
                    if item not in st.session_state.moodboard:
                        st.session_state.moodboard.append(item)
                        st.success("Saved to Moodboard!")

        # Show moodboard section if there are saved items
        st.markdown("---")
        st.markdown("### 🧡 Your Moodboard")
        if st.button("📤 Export Moodboard as CSV"):
            export_df = pd.DataFrame(st.session_state.moodboard)
            export_df = export_df.rename(columns={"description": "image_description", "tone_tag": "tone_tags"})
            export_df.insert(0, "id", range(1, len(export_df) + 1))
            export_df = export_df[["id", "image_url", "image_description", "tone_tags"]]
            export_df.to_csv("moodboard_export.csv", index=False)
            st.success("✅ Moodboard exported as moodboard_export.csv")
        if st.button("🗑️ Clear Moodboard"):
            st.session_state.moodboard.clear()
            st.rerun()

        mood_cols = st.columns(3)
        for i, item in enumerate(st.session_state.moodboard):
            with mood_cols[i % 3]:
                st.image(item["image_url"], width=200)
                tones = [tone.strip() for tone in item['tone_tag'].split(',')]
                badge_html = " ".join([f"<span style='background-color:#333;border-radius:12px;padding:4px 10px;margin:2px;font-size:0.75rem;color:white;display:inline-block;'>{tone}</span>" for tone in tones])
                st.markdown(badge_html, unsafe_allow_html=True)
