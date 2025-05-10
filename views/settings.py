import streamlit as st
from database import get_user, update_settings

def show_settings():
    st.title("Settings")
    username = st.session_state.username
    user = get_user(username)
    settings = user.get("settings", {"theme": "light", "background_color": "#f0f0f0"})

    with st.form("settings_form"):
        st.subheader("Appearance")
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark"],
            index=0 if settings.get("theme", "light") == "light" else 1,
            key="theme_select"
        )
        background_color = st.color_picker(
            "Background Color",
            value=settings.get("background_color", "#f0f0f0"),
            help="Choose a background color for the app"
        )
        
        submitted = st.form_submit_button("Save")
        if submitted:
            new_settings = {
                "theme": theme.lower(),
                "background_color": background_color
            }
            update_settings(username, new_settings)
            st.session_state.theme = new_settings["theme"]
            st.session_state.background_color = new_settings["background_color"]
            st.success("Settings saved!")
            st.rerun()