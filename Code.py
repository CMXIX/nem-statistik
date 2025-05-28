import streamlit as st
import numpy as np
import re
import matplotlib.pyplot as plt
import streamlit_authenticator as stauth

# ---------- PAGE CONFIG AND STYLING ----------
st.set_page_config(page_title="Nem Statistik", page_icon="📊", layout="wide")

st.markdown("""
<style>
body {
    background-color: #0e1117;
    font-family: 'Segoe UI', sans-serif;
    color: #f0f2f6;
}
.stTextInput, .stTextArea, .stButton {
    background: #1e1e26;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 0 10px rgba(0,0,0,0.3);
    color: #f0f2f6;
}
input, textarea, label, div[role="textbox"] {
    color: #f0f2f6 !important;
    background-color: #1e1e26 !important;
    border: 1px solid #333 !important;
}
h1, h2, h3, .stMarkdown {
    font-family: 'Segoe UI', sans-serif;
    color: #f0f2f6;
}
</style>
""", unsafe_allow_html=True)

# Matplotlib should use light style for plots, despite dark theme
plt.style.use("default")

# ---------- USERS ----------
import pandas as pd

# Load users from CSV
user_df = pd.read_csv("Users.csv")

# Hash passwords
hashed_passwords = stauth.Hasher(user_df["password"].tolist()).generate()

# Build credentials dict
credentials = {
    "usernames": {
        row["email"]: {
            "name": row["email"],
            "password": hashed_passwords[i]
        }
        for i, row in user_df.iterrows()
    }
}

# ---------- AUTHENTICATOR ----------
import random
import string

# Force logout workaround: regenerate cookie name if force_logout is set
if st.session_state.get("force_logout"):
    cookie_token = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    st.session_state.pop("force_logout")
else:
    cookie_token = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

authenticator = stauth.Authenticate(
    credentials,
    "nem_statistik_cookie",
    cookie_token,
    cookie_expiry_days=1
)


if 'authentication_status' not in st.session_state:
    st.session_state.authentication_status = None

with st.columns(3)[1]:
    login_data = authenticator.login(fields={"Form name": "Login"}, location="main")

if login_data:
    name, authentication_status, username = login_data
    st.session_state.authentication_status = authentication_status
else:
    authentication_status = st.session_state.authentication_status

if authentication_status is False:
    st.error("Forkert brugernavn eller adgangskode.")
elif authentication_status is None:
    st.stop()
elif authentication_status:
    if st.button("Log ud"):
        authenticator.logout("main")
        st.session_state.clear()
        st.session_state["force_logout"] = True
        st.rerun()

    st.title("Nem Statistik")

    col_input, col_stats, col_plot = st.columns([2, 2, 3])

    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
        st.session_state.analysis_error = None
        st.session_state.data = []

    with col_input:
        raw_data = st.text_area(
            "Indtast dine tal (adskilt med mellemrum, komma, semikolon eller linjeskift):",
            height=300
        )
        if st.button("Lav analyse"):
            try:
                values = re.split(r"[,\s;\n]+", raw_data)
                data = [float(x) for x in values if x.strip() != ""]

                if not data:
                    st.session_state.analysis_error = "Ingen gyldige tal fundet."
                    st.session_state.analysis_result = None
                    st.session_state.data = []
                else:
                    st.session_state.data = data
                    st.session_state.analysis_error = None
                    st.session_state.analysis_result = {
                        "mean": np.mean(data),
                        "median": np.median(data),
                        "q1": np.percentile(data, 25),
                        "q3": np.percentile(data, 75),
                        "min": np.min(data),
                        "max": np.max(data),
                        "range": np.max(data) - np.min(data),
                    }
            except Exception:
                st.session_state.analysis_error = "Kun gyldige tal er tilladt."
                st.session_state.analysis_result = None
                st.session_state.data = []

    with col_stats:
        result = st.session_state.analysis_result
        error = st.session_state.analysis_error

        if error:
            st.error(error)
        elif result:
            st.markdown("### Resultater")
            st.markdown(f"**Gennemsnit:** {result['mean']:.2f}")
            st.markdown(f"**Median:** {result['median']:.2f}")
            st.markdown(f"**Nedre kvartil (25%):** {result['q1']:.2f}")
            st.markdown(f"**Øvre kvartil (75%):** {result['q3']:.2f}")
            st.markdown(f"**Mindsteværdi:** {result['min']:.2f}")
            st.markdown(f"**Højesteværdi:** {result['max']:.2f}")
            st.markdown(f"**Variationsbredde:** {result['range']:.2f}")

    with col_plot:
        if st.session_state.data:
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.boxplot(
                st.session_state.data,
                vert=False,
                whis=[0, 100],
                showfliers=False
            )
            ax.set_title("Boxplot")
            ax.set_xlabel("Værdi")
            st.pyplot(fig)

