import streamlit as st
from datetime import date

st.set_page_config(page_title="Registrasi Pasien - GAIT Clinic", page_icon="🦶", layout="wide")

# ===== CSS Styling =====
st.markdown("""
<style>
.block-container {
    padding-top: 3vh !important;
    max-width: 700px !important;
    margin: auto;
}

h2 {
    text-align: center;
    color: #560000 !important;
    font-weight: 700;
    margin-bottom: 0.2rem !important;
}
.subtitle {
    text-align: center;
    font-size: 1.1rem;
    color: #333;
    margin-bottom: 1.2rem;
}

hr {
    margin-top: 0.4rem;
    margin-bottom: 1.2rem;
    border: 0;
    border-top: 1.5px solid #ccc;
    width: 60%;
    margin-left: auto;
    margin-right: auto;
}

label, .stTextInput label {
    font-weight: 600 !important;
}

.stTextInput > div > div > input, .stNumberInput input, .stDateInput input, .stSelectbox select {
    background-color: #f4eded !important;
    border: 1px solid #e1dada !important;
    border-radius: 6px;
    height: 42px !important;
    font-size: 1rem !important;
}

div[data-testid="stButton"] > button {
    width: 100% !important;
    height: 45px;
    border-radius: 8px;
    border: 1px solid #ccc;
    font-weight: 600;
    font-size: 1rem;
    background-color: white;
    color: black;
    margin-top: 0.5rem;
}
div[data-testid="stButton"] > button:hover {
    border-color: #5b0a0a;
    color: #5b0a0a;
    background-color: #fafafa;
}

p.login-link {
    text-align: center;
    color: #8b0000;
    font-weight: 600;
    margin-top: 0.8rem;
    margin-bottom: 0.2rem;
}

button.login-btn {
    background-color: #a30000 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
}
button.login-btn:hover {
    background-color: #660000 !important;
}
</style>
""", unsafe_allow_html=True)

# ===== HEADER =====
st.markdown("<h2>Aplikasi GAIT Clinic</h2>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Selamat Datang di Sistem Dashboard Pemeriksaan GAIT</p>", unsafe_allow_html=True)
st.markdown("---")

# ===== FORM REGISTRASI =====
st.markdown("### Registrasi Pasien")

with st.form("register_form"):
    nik = st.text_input("NIK", placeholder="Mohon masukkan NIK anda dengan benar")
    nama = st.text_input("Nama Lengkap", placeholder="Masukkan nama lengkap anda")
    password = st.text_input("Password", type="password", placeholder="Masukkan password anda")
    ttl = st.date_input("Tanggal Lahir", help="Masukkan tanggal lahir anda")
    jk = st.selectbox("Jenis Kelamin", ["Pilih Jenis Kelamin", "Laki-laki", "Perempuan"])
    tb = st.text_input("Tinggi Badan", placeholder="Masukkan Tinggi Badan anda")
    bb = st.text_input("Berat Badan", placeholder="Masukkan Berat Badan anda")
    submit = st.form_submit_button("Registrasi")

if submit:
    if nik and nama and password and jk != "Pilih Jenis Kelamin":
        st.success("✅ Pendaftaran berhasil! Silakan login dengan akun anda.")
    else:
        st.warning("⚠️ Mohon isi semua data dengan benar sebelum melanjutkan.")

# ===== FOOTER =====
st.markdown("<p class='login-link'>Sudah punya akun?</p>", unsafe_allow_html=True)
if st.button("Kembali ke Login"):
    st.switch_page("pasien_page.py")