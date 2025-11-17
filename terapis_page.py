import pandas as pd
from pymongo import MongoClient
import math
import matplotlib.pyplot as plt
from PIL import Image
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pymongo import MongoClient
import numpy as np
from pymongo.server_api import ServerApi
import io
from datetime import datetime
import json  # ⬅️ TAMBAH INI
import google.generativeai as genai

# 🧩 Konfigurasi halaman
st.set_page_config(page_title="Dashboard GAIT Terapis", layout="wide")
# st.set_page_config(page_title="Dashboard GAIT Terapis", layout="wide", initial_sidebar_state="expanded")
# ======================= LOGIN FORM =======================
def login_form(role_label: str = "Terapis"):
    # ===== CSS agar tampil modern dan responsif =====
    st.markdown("""
    <style>
        /* Global layout responsif */
        .block-container {
            padding-top: 3vh !important;
            padding-bottom: 2rem !important;
            max-width: 90vw;
            margin: auto;
        }
        
        /* Tombol back tetap di pojok kiri atas, tidak responsif */
        .back-fixed {
            position: fixed;
            top: 30px;
            left: 40px;
            background-color: #a30000;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 20px;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            z-index: 999;
        }
        .back-fixed:hover {
            background-color: #660000;
        }

        @media (max-width: 900px) {
            .block-container {
                width: 95%;
                max-width: 95vw;
                padding-top: 6vh !important;
            }
        }

        h2 {
            color: #560000 !important;
            text-align: center;
            margin-bottom: 0rem !important;
            font-size: clamp(1.8rem, 2.5vw, 2.5rem);
        }

        p.subtitle {
            text-align: center;
            font-size: clamp(1rem, 1.5vw, 1.15rem);
            color: #222;
            margin-top: 0rem !important;
            margin-bottom: 0.4rem !important;
        }
        
        hr {
            margin-top: 0.4rem !important;
            margin-bottom: 1rem !important;
            border: 0;
            border-top: 1.5px solid #ccc;
            width: 60%;
            margin-left: auto;
            margin-right: auto;
        }

        label, .stTextInput label {
            font-weight: 600 !important;
        }

        .stTextInput>div>div>input {
            background-color: #f3ebeb !important;
            border: 1px solid #e2dada !important;
            border-radius: 6px;
            height: 42px;
            font-size: 1rem;
        }

        button[kind="primary"] {
            width: 100% !important;
            border-radius: 6px;
            background-color: #fff !important;
            color: #000 !important;
            border: 1px solid #ddd !important;
            font-weight: 500;
            height: 42px;
            font-size: 1rem;
        }

        button[kind="primary"]:hover {
            border-color: #5b0a0a !important;
            color: #5b0a0a !important;
        }

        a.forgot {
            color: #a30000 !important;
            font-size: 0.9rem;
            text-decoration: none;
        }

        p.footer {
            text-align: center;
            font-size: 0.85rem;
            color: #444;
            margin-top: 1rem;
        }

        /* Tombol hover halus */
        button:hover {
            transition: all 0.1s ease-in-out;
        }
        
        /* Custom styles untuk data tables */
        .dataframe {
            border: 1px solid #ddd !important;
            border-radius: 8px !important;
        }
        
        .action-buttons {
            display: flex;
            gap: 5px;
        }
        
        .stButton button {
            border-radius: 6px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Tombol kembali (HTML manual biar posisinya fixed)
    if st.button("Kembali", key="back_button"):
        st.session_state.role = None
        st.rerun()

    # ===== Konten login =====
    st.markdown("<h2>Aplikasi GAIT Clinic</h2>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Selamat Datang di Sistem Dashboard Pemeriksaan GAIT</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.subheader(f"Login - {role_label}")
    username = st.text_input("Username", placeholder="Masukkan username anda")
    password = st.text_input("Password", type="password", placeholder="Masukkan password anda")

    st.markdown("<a class='forgot' href='#'>Lupa kata sandi?</a>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    submit = st.button("Login", use_container_width=True)

    st.markdown(
        "<p class='footer'>Dengan masuk, Anda menyetujui kebijakan Privasi & Syarat Layanan sistem GAIT ini.</p>",
        unsafe_allow_html=True,
    )

    return username, password, submit

# Optimasi koneksi MongoDB
def get_mongo_client():
    return MongoClient(
        st.secrets["MONGO_URI"],
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000
    )

# Kelas GaitAnalysisData untuk data normal
class GaitAnalysisDataNormal:
    def __init__(self, content, usia, jenis_kelamin):
        try:
            # Membaca file Excel ke dalam DataFrame pandas
            self.df = pd.read_excel(io.BytesIO(content), sheet_name=[0, 1])
            self.suin = self.df[0]  # Lembar pertama untuk data mentah
            self.normkin = self.df[1].iloc[:, :31]  # Lembar kedua untuk kinematika terstandarisasi
        except Exception as e:
            st.error(f"Error reading the Excel file: {e}")
            return

        # Memproses data
        self.cleaned_data = self.clean_data()
        self.normkin_processed = self.process_normkin()
        self.trial_info = self.extract_trial_info()
        self.subject_params = self.extract_subject_params(usia, jenis_kelamin)
        self.body_measurements = self.extract_body_measurements()
        self.norm_kinematics = self.extract_norm_kinematics()

    def clean_data(self):
        cleaned_data = self.suin.dropna(how='all')
        cleaned_data.reset_index(drop=True, inplace=True)
        return cleaned_data

    def process_normkin(self):
        column_namesX = [col for col in self.normkin.columns if col.endswith('X')]
        normkin = self.normkin.loc[:, column_namesX]
        normkin.insert(0, "Percentage of Gait Cycle", self.df[1].iloc[:, 0].tolist())
        return normkin

    def extract_trial_info(self):
        return {
            "Trial Information": {
                "Trial Name": self.cleaned_data.iloc[1, 2]
            }
        }

    def extract_subject_params(self, usia, jenis_kelamin):
        bmi = (self.cleaned_data.iloc[4, 2])/((self.cleaned_data.iloc[5, 2]/1000)**2)
        bmi_class = (
            "Kurus Berat" if bmi < 17.0 else
            "Kurus Ringan" if 17.0 <= bmi <= 18.4 else
            "Normal" if 18.5 <= bmi <= 25.0 else
            "Gemuk Ringan" if 25.1 <= bmi <= 27.0 else
            "Gemuk Berat"
        )
        return {
            "Subject Parameters": {
                "Subject Name": self.cleaned_data.iloc[3, 2],
                "Age": usia,
                "Gender": jenis_kelamin.upper(),
                "Bodymass (kg)": self.cleaned_data.iloc[4, 2],
                "Height (mm)": self.cleaned_data.iloc[5, 2],
                "BMI": bmi,
                "BMI Classification": bmi_class
            }
        }

    def extract_body_measurements(self):
        return {
            "Body Measurements": {
                "Leg Length (mm)": {
                    "Left": self.cleaned_data.iloc[12, 2],
                    "Right": self.cleaned_data.iloc[12, 3]
                },
                "Knee Width (mm)": {
                    "Left": self.cleaned_data.iloc[13, 2],
                    "Right": self.cleaned_data.iloc[13, 3]
                },
                "Ankle Width (mm)": {
                    "Left": self.cleaned_data.iloc[14, 2],
                    "Right": self.cleaned_data.iloc[14, 3]
                }
            }
        }

    def extract_norm_kinematics(self):
        required_cols = [
        "Percentage of Gait Cycle", "LPelvisAngles_X", "RPelvisAngles_X",
        "LHipAngles_X", "RHipAngles_X", "LKneeAngles_X", "RKneeAngles_X",
        "LAnkleAngles_X", "RAnkleAngles_X", "LFootProgressAngles_X", "RFootProgressAngles_X"
    ]

        missing_cols = [col for col in required_cols if col not in self.normkin_processed.columns]
    
        if missing_cols:
            st.error(f"Incomplete kinematic data. Missing columns: {', '.join(missing_cols)}")
            st.stop()
        else:
            return {
                "Norm Kinematics": {
                    "Percentage of Gait Cycle": self.normkin_processed['Percentage of Gait Cycle'].tolist(),
                    "LPelvisAngles_X": self.normkin_processed["LPelvisAngles_X"].tolist(),
                    "RPelvisAngles_X": self.normkin_processed["RPelvisAngles_X"].tolist(),
                    "LHipAngles_X": self.normkin_processed["LHipAngles_X"].tolist(),
                    "RHipAngles_X": self.normkin_processed["RHipAngles_X"].tolist(),
                    "LKneeAngles_X": self.normkin_processed["LKneeAngles_X"].tolist(),
                    "RKneeAngles_X": self.normkin_processed["RKneeAngles_X"].tolist(),
                    "LAnkleAngles_X": self.normkin_processed["LAnkleAngles_X"].tolist(),
                    "RAnkleAngles_X": self.normkin_processed["RAnkleAngles_X"].tolist(),
                    "LFootProgressAngles_X": self.normkin_processed["LFootProgressAngles_X"].tolist(),
                    "RFootProgressAngles_X": self.normkin_processed["RFootProgressAngles_X"].tolist()
                }
            }

    def to_dict(self):
        return {
            **self.trial_info,
            **self.subject_params,
            **self.body_measurements,
            **self.norm_kinematics
        }
    
# Kelas GaitAnalysisData untuk data pasien (yang lama)
class GaitAnalysisData:
    def __init__(self, data):
        self.df = pd.read_excel(data, sheet_name=[0, 1])  # Read the uploaded file
        self.suin = self.df[0]
        self.normkin = self.df[1].iloc[:, :31]

        # Clean and extract necessary data
        self.cleaned_data = self.clean_data()
        self.normkin_processed = self.process_normkin()

        # Extract and store various sections
        self.trial_info = self.extract_trial_info()
        self.subject_params = self.extract_subject_params()
        self.body_measurements = self.extract_body_measurements()
        self.norm_kinematics = self.extract_norm_kinematics()

    def clean_data(self):
        cleaned_data = self.suin.dropna(how='all')
        cleaned_data.reset_index(drop=True, inplace=True)
        return cleaned_data

    def process_normkin(self):
        column_namesX = [col for col in self.normkin.columns if col.endswith('X')]
        normkin = self.normkin.loc[:, column_namesX]
        normkin.insert(0, "Percentage of Gait Cycle", self.df[1].iloc[:, 0].tolist())
        return normkin

    def extract_trial_info(self):
        return {
            "Trial Information": {
                "Trial Name": self.cleaned_data.iloc[1, 2]
            }
        }

    def extract_subject_params(self):
        return {
            "Subject Parameters": {
                "Subject Name": self.cleaned_data.iloc[3, 2],
                "Bodymass (kg)": self.cleaned_data.iloc[4, 2],
                "Height (mm)": self.cleaned_data.iloc[5, 2]
            }
        }

    def extract_body_measurements(self):
        return {
            "Body Measurements": {
                "Leg Length (mm)": {
                    "Left": self.cleaned_data.iloc[12, 2],
                    "Right": self.cleaned_data.iloc[12, 3]
                },
                "Knee Width (mm)": {
                    "Left": self.cleaned_data.iloc[13, 2],
                    "Right": self.cleaned_data.iloc[13, 3]
                },
                "Ankle Width (mm)": {
                    "Left": self.cleaned_data.iloc[14, 2],
                    "Right": self.cleaned_data.iloc[14, 3]
                }
            }
        }

    def extract_norm_kinematics(self):
        return {
            "Norm Kinematics": {
                "Percentage of Gait Cycle": self.normkin_processed['Percentage of Gait Cycle'].values.tolist(),  # Convert to list
                "LPelvisAngles_X": self.normkin_processed["LPelvisAngles_X"].values.tolist(),  # Convert to list
                "RPelvisAngles_X": self.normkin_processed["RPelvisAngles_X"].values.tolist(),  # Convert to list
                "LHipAngles_X": self.normkin_processed["LHipAngles_X"].values.tolist(),  # Convert to list
                "RHipAngles_X": self.normkin_processed["RHipAngles_X"].values.tolist(),  # Convert to list
                "LKneeAngles_X": self.normkin_processed["LKneeAngles_X"].values.tolist(),  # Convert to list
                "RKneeAngles_X": self.normkin_processed["RKneeAngles_X"].values.tolist(),  # Convert to list
                "LAnkleAngles_X": self.normkin_processed["LAnkleAngles_X"].values.tolist(),  # Convert to list
                "RAnkleAngles_X": self.normkin_processed["RAnkleAngles_X"].values.tolist(),  # Convert to list
                "LFootProgressAngles_X": self.normkin_processed["LFootProgressAngles_X"].values.tolist(),  # Convert to list
                "RFootProgressAngles_X": self.normkin_processed["RFootProgressAngles_X"].values.tolist()   # Convert to list
            }
        }

    def to_dict(self):
        # Combine all sections into a single dictionary
        return {
            **self.trial_info,
            **self.subject_params,
            **self.body_measurements,
            **self.norm_kinematics
        }
        
class TerapisPage:
    def __init__(self):
        # Hapus daftar user terapis sementara
        # self.terapis_users = {"terapis1": "1234"}  # DIHAPUS
        pass

    def run(self):
        # inisialisasi session state
        if 'uploaded_patient_data' not in st.session_state:
            st.session_state.uploaded_patient_data = None
        if 'norm_kinematics_df' not in st.session_state:
            st.session_state.norm_kinematics_df = None
        if "terapis_logged_in" not in st.session_state:
            st.session_state.terapis_logged_in = False

        # jika belum login → tampilkan form login
        if not st.session_state.terapis_logged_in:
            username, password, submit = login_form("Terapis")
            if submit:
                # Cek login dari database
                if self._check_terapis_login(username, password):
                    st.session_state.terapis_logged_in = True
                    st.session_state.terapis_username = username
                    st.rerun()
                else:
                    st.error("Login gagal! Username atau password salah.")
            return  # hentikan eksekusi di sini sampai login selesai

        # ====== CSS styling ======
        st.markdown("""
            <style>
                body { background-color: #f9f9f9; }

                /* Sidebar */
                section[data-testid="stSidebar"] {
                    background-color: #560000;
                }

                .sidebar-title {
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 10px 20px;
                }

                .sidebar-subtitle {
                    color: #ddd;
                    font-size: 14px;
                    padding-left: 20px;
                    margin-bottom: 10px;
                }

                .filter-box {
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0px 1px 3px rgba(0,0,0,0.1);
                    margin-bottom: 10px;
                }
        
                /* Mengubah warna teks di sidebar menjadi putih */
                section[data-testid="stSidebar"] div[class*="stRadio"] label {
                    color: white !important;
                }
                
                section[data-testid="stSidebar"] div[class*="stRadio"] div[role="radiogroup"] {
                    color: white !important;
                }
                
                /* Mengubah warna teks untuk semua elemen di sidebar */
                section[data-testid="stSidebar"] * {
                    color: white !important;
                }
                
                /* Khusus untuk radio button yang dipilih */
                section[data-testid="stSidebar"] div[class*="stRadio"] div[data-testid="stMarkdownContainer"] p {
                    color: white !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # ====== Sidebar ======
        st.sidebar.markdown("<p class='sidebar-title'>Sistem Dashboard Pemeriksaan GAIT</p>", unsafe_allow_html=True)
        st.sidebar.markdown("<p class='sidebar-subtitle'>Menu</p>", unsafe_allow_html=True)

        menu = st.sidebar.radio(
            "",
            ["Dashboard", "Input Data GAIT Normal", "Input Data GAIT Pasien", "Riwayat Pemeriksaan", "Logout"]
        )

        # ====== Konten utama ======
        if menu == "Dashboard":
            self.show_dashboard()
        elif menu == "Input Data GAIT Normal":
            self.input_data_gait_normal()

        elif menu == "Input Data GAIT Pasien":
            self.input_data_gait_pasien()

        elif menu == "Riwayat Pemeriksaan":
            self.show_examination_history()

        elif menu == "Logout":
            st.session_state.terapis_logged_in = False
            st.session_state.terapis_username = None
            st.session_state.role = None
            st.rerun()

    def _check_terapis_login(self, username, password):
        """Cek login terapis dari database"""
        try:
            client = get_mongo_client()
            db = client['GaitDB']
            collection = db['users']
            
            # Cari user dengan role terapis
            terapis = collection.find_one({
                'username': username,
                'role': 'terapis'
            })
            
            if terapis and terapis.get('password') == password:
                return True
            return False
            
        except Exception as e:
            st.error(f"Error checking login: {e}")
            return False
    
    def input_data_gait_normal(self):
        st.subheader("🧍 Input Data GAIT Normal")
        st.markdown("### Upload Data Subjek Normal")
        uploaded_file = st.file_uploader("Upload file data gait normal (Format .xlsx)", type=["xlsx"], key="normal_upload")
        
        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            with col1:
                usia = st.number_input("Masukkan Usia:", min_value=0, max_value=120, key="usia_normal")
            with col2:
                jenis_kelamin = st.text_input("Masukkan Jenis Kelamin (L/P):", key="gender_normal").strip().upper()

            if st.button("Proses Data Normal", key="process_normal"):
                if usia == 0 or jenis_kelamin == "":
                    st.warning("⚠️ Harap masukkan usia dan jenis kelamin sebelum memproses file.")
                elif jenis_kelamin not in ['L', 'P']:
                    st.warning("⚠️ Jenis kelamin harus 'L' (Laki-laki) atau 'P' (Perempuan).")
                else:
                    try:
                        content = uploaded_file.read()
                        gait_data = GaitAnalysisDataNormal(content, usia, jenis_kelamin)
                        
                        if hasattr(gait_data, 'df'):
                            data_dict = gait_data.to_dict()

                            # Periksa apakah ada data kosong (None atau NaN)
                            def check_missing(data):
                                if isinstance(data, dict):
                                    return any(check_missing(v) for v in data.values())
                                elif isinstance(data, list):
                                    return any(check_missing(v) for v in data)
                                else:
                                    # Cek apakah nilai kosong (NaN atau None)
                                    return pd.isna(data)

                            def check_norm_kinematics(norm_kinematics):
                                for key, value in norm_kinematics.items():
                                    if isinstance(value, list):
                                        for v in value:
                                            if pd.isna(v):
                                                return True  # Ada NaN/None
                                            try:
                                                float(v)  # pastikan bisa dikonversi ke angka
                                            except ValueError:
                                                return True  # Ada teks non-numerik
                                    else:
                                        return True  # Format tidak sesuai, harusnya list
                                return False  # Semua aman

                            norm_kin_data = data_dict.get("Norm Kinematics", {})
                            if check_missing(data_dict) or check_norm_kinematics(norm_kin_data):
                                st.error("⚠️ Data tidak valid: terdapat nilai kosong atau teks non-numerik.")
                            else:
                                try:
                                    client = get_mongo_client()
                                    db = client['GaitDB']
                                    collection = db['gait_data']
                                    collection.insert_one(data_dict)
                                    st.success("✅ Data berhasil disimpan ke database!")
                                    
                                    # Tampilkan ringkasan data
                                    st.markdown("### Ringkasan Data yang Disimpan")
                                    st.json({
                                        "Nama Subjek": data_dict["Subject Parameters"]["Subject Name"],
                                        "Usia": data_dict["Subject Parameters"]["Age"],
                                        "Jenis Kelamin": data_dict["Subject Parameters"]["Gender"],
                                        "BMI": f"{data_dict['Subject Parameters']['BMI']:.2f}",
                                        "Klasifikasi BMI": data_dict["Subject Parameters"]["BMI Classification"]
                                    })
                                    
                                except Exception as e:
                                    st.error(f"❌ Error menyimpan data ke database: {e}")
                        else:
                            st.error("❌ Gagal memproses data yang diupload.")
                            
                    except Exception as e:
                        st.error(f"❌ Error dalam memproses file: {e}")        
    def input_data_gait_pasien(self):
        st.subheader("👤 Input Data GAIT Pasien")
        
        # Ambil data pasien dari database untuk dropdown
        try:
            client = get_mongo_client()
            db = client['GaitDB']
            collection = db['pasien_users']
            
            # Ambil semua data pasien
            pasien_data = list(collection.find({}, {'nik': 1, 'nama_lengkap': 1}))
            
            # Buat opsi dropdown
            pasien_options = ["Pilih Data Pasien yang akan diperiksa"] + [
                f"{pasien['nik']} - {pasien['nama_lengkap']}" for pasien in pasien_data
            ]
            
        except Exception as e:
            st.error(f"❌ Error mengambil data pasien: {e}")
            pasien_options = ["Pilih Data Pasien yang akan diperiksa"]
        
        # Dropdown untuk memilih pasien
        selected_pasien = st.selectbox(
            "Pilih Data Pasien yang akan diperiksa",
            options=pasien_options,
            key="pasien_dropdown"
        )
        
        # Jika pasien dipilih, ekstrak NIK dan nama
        pasien_nik = ""
        nama_pasien = ""
        
        if selected_pasien != "Pilih Data Pasien yang akan diperiksa":
            # Ekstrak NIK dan nama dari string yang dipilih
            try:
                nik_nama = selected_pasien.split(" - ")
                if len(nik_nama) == 2:
                    pasien_nik = nik_nama[0]
                    nama_pasien = nik_nama[1]
                    
                    # Tampilkan informasi pasien yang dipilih
                    st.info(f"**Pasien Terpilih:** {nama_pasien} (NIK: {pasien_nik})")
            except Exception as e:
                st.error(f"❌ Error memproses data pasien: {e}")
        
        # Input tanggal pemeriksaan
        tanggal = st.date_input("Tanggal Pemeriksaan")
        
        # Upload file data GAIT pasien
        st.markdown("---")
        st.markdown("### Upload Data GAIT Pasien")
        uploaded_file = st.file_uploader("Upload file data gait pasien (Format .xlsx)", type=["xlsx"])
        
        if uploaded_file is not None:
            # Validasi: pastikan pasien sudah dipilih
            if selected_pasien == "Pilih Data Pasien yang akan diperiksa":
                st.warning("⚠️ Silakan pilih pasien terlebih dahulu sebelum mengupload file.")
                return
            
            # Hanya proses data ketika tombol submit ditekan
            if st.button("Simpan Data Pasien", key="save_patient"):
                try:
                    with st.spinner("Memproses data pasien..."):
                        # Proses file dengan GaitAnalysisData
                        gait_data = GaitAnalysisData(uploaded_file)
                        processed_data = gait_data.to_dict()

                        # Ekstrak data untuk Norm Kinematics (hanya yang diperlukan)
                        norm_kinematics = processed_data["Norm Kinematics"]
                        rows = []
                        
                        for i in range(len(norm_kinematics["Percentage of Gait Cycle"])):
                            row = {
                                "%cycle": norm_kinematics["Percentage of Gait Cycle"][i],
                                "LPelvisAngles_X": norm_kinematics["LPelvisAngles_X"][i],
                                "RPelvisAngles_X": norm_kinematics["RPelvisAngles_X"][i],
                                "LHipAngles_X": norm_kinematics["LHipAngles_X"][i],
                                "RHipAngles_X": norm_kinematics["RHipAngles_X"][i],
                                "LKneeAngles_X": norm_kinematics["LKneeAngles_X"][i],
                                "RKneeAngles_X": norm_kinematics["RKneeAngles_X"][i],
                                "LAnkleAngles_X": norm_kinematics["LAnkleAngles_X"][i],
                                "RAnkleAngles_X": norm_kinematics["RAnkleAngles_X"][i],
                            }
                            rows.append(row)

                        # Simpan ke session state - HANYA DATA YANG DIPERLUKAN
                        st.session_state.norm_kinematics_df = pd.DataFrame(rows)
                        
                        # Simpan data pasien ke MongoDB (tanpa diagnosa)
                        patient_data = {
                            'patient_info': {
                                'nik': pasien_nik,
                                'nama': nama_pasien,
                                'tanggal_pemeriksaan': tanggal.strftime("%Y-%m-%d"),
                                'upload_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            },
                            'file_info': {
                                'file_name': uploaded_file.name,
                                'upload_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            },
                            'gait_data': processed_data,
                            'norm_kinematics': rows
                        }
                        
                        # Simpan ke MongoDB
                        client = get_mongo_client()
                        db = client['GaitDB']
                        collection = db['patient_examinations']
                        
                        # Cek apakah sudah ada pemeriksaan untuk pasien di tanggal yang sama
                        existing_exam = collection.find_one({
                            'patient_info.nik': pasien_nik,
                            'patient_info.tanggal_pemeriksaan': tanggal.strftime("%Y-%m-%d")
                        })
                        
                        if existing_exam:
                            st.warning(f"⚠️ Pasien {nama_pasien} sudah memiliki data pemeriksaan pada tanggal {tanggal.strftime('%d %B %Y')}. Data akan diupdate.")
                            # Update data yang sudah ada
                            collection.update_one(
                                {'_id': existing_exam['_id']},
                                {'$set': patient_data}
                            )
                            st.success(f"✅ Data gait pasien berhasil diupdate!")
                        else:
                            # Insert data baru
                            result = collection.insert_one(patient_data)
                            st.success(f"✅ Data gait pasien berhasil disimpan!")
                        
                        st.info(f"File: {uploaded_file.name}")
                        st.info(f"Pasien: {nama_pasien} (NIK: {pasien_nik})")
                        st.info(f"Tanggal Pemeriksaan: {tanggal.strftime('%d %B %Y')}")
                            
                except Exception as e:
                    st.error(f"❌ Error dalam memproses file: {e}")
        else:
            # Reset session state jika tidak ada file yang diupload
            if 'uploaded_patient_data' in st.session_state:
                del st.session_state.uploaded_patient_data
            if 'norm_kinematics_df' in st.session_state:
                del st.session_state.norm_kinematics_df

    def show_examination_history(self):
        st.subheader("📜 Riwayat Pemeriksaan")
        
        try:
            # Koneksi ke MongoDB
            client = get_mongo_client()
            db = client['GaitDB']
            collection = db['patient_examinations']
            
            # Ambil semua data pemeriksaan
            examinations = list(collection.find().sort('patient_info.upload_date', -1))
            
            if not examinations:
                st.info("📝 Belum ada riwayat pemeriksaan pasien.")
                return
            
            # Siapkan data untuk tabel
            table_data = []
            for exam in examinations:
                patient_info = exam.get('patient_info', {})
                file_info = exam.get('file_info', {})
                
                table_data.append({
                    'Tanggal Pemeriksaan': patient_info.get('tanggal_pemeriksaan', 'N/A'),
                    'NIK Pasien': patient_info.get('nik', 'N/A'),
                    'Nama Pasien': patient_info.get('nama', 'N/A'),
                    # 'Diagnosa': patient_info.get('diagnosa', 'N/A'),
                    'File Name': file_info.get('file_name', 'N/A'),
                    'Tanggal Upload': patient_info.get('upload_date', 'N/A')
                })
            
            # Tampilkan dalam tabel
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True)
            
            # Fitur filter
            st.markdown("### 🔍 Filter Riwayat")
            col1, col2 = st.columns(2)
            
            with col1:
                filter_nik = st.text_input("Filter berdasarkan NIK:")
            with col2:
                filter_nama = st.text_input("Filter berdasarkan Nama:")
            
            # Apply filters
            filtered_df = df.copy()
            if filter_nik:
                filtered_df = filtered_df[filtered_df['NIK Pasien'].str.contains(filter_nik, case=False, na=False)]
            if filter_nama:
                filtered_df = filtered_df[filtered_df['Nama Pasien'].str.contains(filter_nama, case=False, na=False)]
            
            if len(filtered_df) != len(df):
                st.markdown(f"**Menampilkan {len(filtered_df)} dari {len(df)} data**")
                st.dataframe(filtered_df, use_container_width=True)
            
            # Tombol download
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Riwayat sebagai CSV",
                data=csv,
                file_name=f"riwayat_pemeriksaan_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"❌ Error mengambil data riwayat: {e}")

    def show_dashboard(self):
        st.markdown("## Dashboard Gait Analysis")

        # CEK LEBIH EFISIEN - hanya cek key existence
        has_patient_data = ('uploaded_patient_data' in st.session_state and 
                           'norm_kinematics_df' in st.session_state and
                           st.session_state.norm_kinematics_df is not None)

        if has_patient_data:
            try:
                with st.spinner("Memuat data dan membuat visualisasi..."):
                    self.process_dashboard_with_patient()
            except Exception as e:
                st.error(f"❌ Error dalam memproses dashboard: {e}")
        else:
            # Tampilkan dashboard tanpa data pasien
            st.warning("ℹ️ Tidak ada data pasien yang diupload. Silakan upload data pasien di menu 'Input Data GAIT Pasien' untuk melihat analisis perbandingan.")
            # st.markdown("---")
            self.show_normal_dashboard()

    def process_dashboard_with_patient(self):
        """Method terpisah untuk memproses dashboard dengan data pasien"""
        px.defaults.template = 'plotly_dark'
        px.defaults.color_continuous_scale = 'reds'
        
        # Koneksi ke MongoDB - dengan timeout
        client = get_mongo_client()
        db = client['GaitDB']
        collection = db['gait_data']
        
        # Membaca data dari MongoDB dengan limit
        cursor = collection.find().limit(100)  # Batasi data untuk performa
        data = list(cursor)
        
        if len(data) == 0:
            st.error("❌ Database Normal Belum Ada. Silahkan Upload Data Normal pada Menu 'Input Data GAIT Normal'")
            return
        
        # Normalisasi data untuk DataFrame
        df = pd.json_normalize(data)
        df.columns = df.columns.str.replace('Trial Information.', '')
        df.columns = df.columns.str.replace('Subject Parameters.', '')
        df.columns = df.columns.str.replace('Body Measurements.', '')
        df.columns = df.columns.str.replace('Norm Kinematics.', '')

        # ====== FILTER ======
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        st.markdown("### Filter Data")

        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            min_age = df['Age'].min()
            max_age = df['Age'].max()
            age_range = st.slider(
                'Filter by Age Range:',
                min_value=min_age,
                max_value=max_age,
                value=(min_age, max_age)
            )

        with col2:
            bmi_options = ["All BMI Classification"] + list(df["BMI Classification"].value_counts().keys().sort_values())
            classbmi = st.selectbox(label="BMI Classification", options=bmi_options)

        with col3:
            gender_mapping = {"L": "Pria", "P": "Wanita"}
            df["Gender"] = df["Gender"].map(gender_mapping)
            gender_options = ["All Gender"] + list(df["Gender"].value_counts().keys().sort_values())
            gender = st.selectbox(label="Gender", options=gender_options)

        st.markdown("</div>", unsafe_allow_html=True)
        # st.markdown("---")
            
        # Apply filters
        filtered_df = df[(df['Age'] >= age_range[0]) & (df['Age'] <= age_range[1])]
        if classbmi != "All BMI Classification":
            filtered_df = filtered_df[filtered_df['BMI Classification'] == classbmi]
        if gender != "All Gender":
            filtered_df = filtered_df[filtered_df["Gender"] == gender]
            
        if filtered_df.empty:
            st.error(f"Tidak terdapat data dengan jenis kelamin {gender} yang terklasifikasi {classbmi}")
            return
            
        st.markdown(f"**Total Records:** {len(filtered_df)}")

        # Gunakan data pasien dari session state
        norm_kinematics_df = st.session_state.norm_kinematics_df

        # Buat visualisasi untuk setiap joint
        self.create_visualizations(filtered_df, norm_kinematics_df)

    def create_visualizations(self, filtered_df, norm_kinematics_df):
        """Membuat visualisasi untuk semua joint"""
        # Pelvis
        percentage_cycle = pd.DataFrame(filtered_df['Percentage of Gait Cycle'].tolist())
        l_pelvis_angles = pd.DataFrame(filtered_df['LPelvisAngles_X'].tolist())
        r_pelvis_angles = pd.DataFrame(filtered_df['RPelvisAngles_X'].tolist())

        percentage_cycle.columns = [f"%cycle_{i}" for i in range(percentage_cycle.shape[1])]
        l_pelvis_angles.columns = [f"L_Pelvis_{i}" for i in range(l_pelvis_angles.shape[1])]
        r_pelvis_angles.columns = [f"R_Pelvis_{i}" for i in range(r_pelvis_angles.shape[1])]
        
        mean_l_pelvis = l_pelvis_angles.mean(axis=0).values
        std_l_pelvis = l_pelvis_angles.std(axis=0)/np.sqrt(l_pelvis_angles.shape[0])
        mean_r_pelvis = r_pelvis_angles.mean(axis=0).values
        std_r_pelvis = r_pelvis_angles.std(axis=0)/np.sqrt(r_pelvis_angles.shape[0])

        std_l_pelvis = std_l_pelvis.values if isinstance(std_l_pelvis, pd.Series) else std_l_pelvis
        std_r_pelvis = std_r_pelvis.values if isinstance(std_r_pelvis, pd.Series) else std_r_pelvis

        lpelvis = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lpelvis': mean_l_pelvis,
            'std_Lpelvis': std_l_pelvis,
            'your left pelvis': norm_kinematics_df['LPelvisAngles_X']
        })

        rpelvis = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rpelvis': mean_r_pelvis,
            'std_Rpelvis': std_r_pelvis,
            'your right pelvis': norm_kinematics_df['RPelvisAngles_X']
        })

        # Create figures
        fig1 = self.create_pelvis_figure(lpelvis, "Left Pelvis", 'orange')
        fig2 = self.create_pelvis_figure(rpelvis, "Right Pelvis", 'dark blue')

        # Knee
        l_knee_angles = pd.DataFrame(filtered_df['LKneeAngles_X'].tolist())
        r_knee_angles = pd.DataFrame(filtered_df['RKneeAngles_X'].tolist())

        l_knee_angles.columns = [f"L_Knee_{i}" for i in range(l_knee_angles.shape[1])]
        r_knee_angles.columns = [f"R_Knee_{i}" for i in range(r_knee_angles.shape[1])]

        mean_l_knee = l_knee_angles.mean(axis=0).values
        std_l_knee = l_knee_angles.std(axis=0) / np.sqrt(l_knee_angles.shape[0])
        mean_r_knee = r_knee_angles.mean(axis=0).values
        std_r_knee = r_knee_angles.std(axis=0) / np.sqrt(r_knee_angles.shape[0])

        std_l_knee = std_l_knee.values if isinstance(std_l_knee, pd.Series) else std_l_knee
        std_r_knee = std_r_knee.values if isinstance(std_r_knee, pd.Series) else std_r_knee

        lknee = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lknee': mean_l_knee,
            'std_Lknee': std_l_knee,
            'your left knee': norm_kinematics_df['LKneeAngles_X']
        })
        
        rknee = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rknee': mean_r_knee,
            'std_Rknee': std_r_knee,
            'your right knee': norm_kinematics_df['RKneeAngles_X']
        })

        fig3 = self.create_joint_figure(lknee, "Left Knee", 'orange')
        fig4 = self.create_joint_figure(rknee, "Right Knee", 'dark blue')

        # Hip
        l_hip_angles = pd.DataFrame(filtered_df['LHipAngles_X'].tolist())
        r_hip_angles = pd.DataFrame(filtered_df['RHipAngles_X'].tolist())

        l_hip_angles.columns = [f"L_Hip_{i}" for i in range(l_hip_angles.shape[1])]
        r_hip_angles.columns = [f"R_Hip_{i}" for i in range(r_hip_angles.shape[1])]

        mean_l_hip = l_hip_angles.mean(axis=0).values
        std_l_hip = l_hip_angles.std(axis=0) / np.sqrt(l_hip_angles.shape[0])
        mean_r_hip = r_hip_angles.mean(axis=0).values
        std_r_hip = r_hip_angles.std(axis=0) / np.sqrt(r_hip_angles.shape[0])

        std_l_hip = std_l_hip.values if isinstance(std_l_hip, pd.Series) else std_l_hip
        std_r_hip = std_r_hip.values if isinstance(std_r_hip, pd.Series) else std_r_hip

        lhip = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lhip': mean_l_hip,
            'std_Lhip': std_l_hip,
            'your left hip': norm_kinematics_df['LHipAngles_X']
        })
        
        rhip = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rhip': mean_r_hip,
            'std_Rhip': std_r_hip,
            'your right hip': norm_kinematics_df['RHipAngles_X']
        })

        fig5 = self.create_joint_figure(lhip, "Left Hip", 'orange')
        fig6 = self.create_joint_figure(rhip, "Right Hip", 'dark blue')

        # Ankle
        l_ankle_angles = pd.DataFrame(filtered_df['LAnkleAngles_X'].tolist())
        r_ankle_angles = pd.DataFrame(filtered_df['RAnkleAngles_X'].tolist())

        l_ankle_angles.columns = [f"L_Ankle_{i}" for i in range(l_ankle_angles.shape[1])]
        r_ankle_angles.columns = [f"R_Ankle_{i}" for i in range(r_ankle_angles.shape[1])]

        mean_l_ankle = l_ankle_angles.mean(axis=0).values
        std_l_ankle = l_ankle_angles.std(axis=0) / np.sqrt(l_ankle_angles.shape[0])
        mean_r_ankle = r_ankle_angles.mean(axis=0).values
        std_r_ankle = r_ankle_angles.std(axis=0) / np.sqrt(r_ankle_angles.shape[0])

        std_l_ankle = std_l_ankle.values if isinstance(std_l_ankle, pd.Series) else std_l_ankle
        std_r_ankle = std_r_ankle.values if isinstance(std_r_ankle, pd.Series) else std_r_ankle

        lankle = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lankle': mean_l_ankle,
            'std_Lankle': std_l_ankle,
            'your left ankle': norm_kinematics_df['LAnkleAngles_X']
        })

        rankle = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rankle': mean_r_ankle,
            'std_Rankle': std_r_ankle,
            'your right ankle': norm_kinematics_df['RAnkleAngles_X']
        })
        
        fig7 = self.create_joint_figure(lankle, "Left Ankle", 'orange')
        fig8 = self.create_joint_figure(rankle, "Right Ankle", 'dark blue')

        # Tampilkan dalam tabs
        tab1, tab2, tab3, tab4 = st.tabs(["PELVIS", "KNEE", "HIP", "ANKLE"])

        with tab1:
            tab1.subheader("PELVIS")
            tab1.write('Pelvis (dalam bahasa Indonesia: panggul) adalah struktur tulang yang berbentuk cekungan di bawah perut, di antara tulang pinggul, dan di atas paha.')
            maelpelvis = np.mean(np.abs(lpelvis["your left pelvis"] - lpelvis["Mean_Lpelvis"]))
            maerpelvis = np.mean(np.abs(rpelvis["your right pelvis"] - rpelvis["Mean_Rpelvis"]))
            col1, col2 = tab1.columns(2)
            with col1:
                st.plotly_chart(fig1, use_container_width=True)
                st.write(f"**Mean difference in left pelvis angle (Patient vs Normal): {maelpelvis:.2f}°**")
            with col2:
                st.plotly_chart(fig2, use_container_width=True)
                st.write(f"**Mean difference in right pelvis angle (Patient vs Normal): {maerpelvis:.2f}°**")
                
        with tab2:
            tab2.subheader("KNEE")
            tab2.write('Knee (dalam bahasa Indonesia: lutut) adalah bagian tubuh manusia yang terletak di antara paha dan betis, berfungsi sebagai sendi yang menghubungkan tulang femur (paha) dengan tulang tibia (betis).')
            maelknee = np.mean(np.abs(lknee["your left knee"] - lknee["Mean_Lknee"]))
            maerknee = np.mean(np.abs(rknee["your right knee"] - rknee["Mean_Rknee"]))
            col1, col2 = tab2.columns(2)
            with col1:
                st.plotly_chart(fig3, use_container_width=True)
                st.write(f"**Mean difference in left knee angle (Patient vs Normal): {maelknee:.2f}°**")
            with col2:
                st.plotly_chart(fig4, use_container_width=True)
                st.write(f"**Mean difference in right knee angle (Patient vs Normal): {maerknee:.2f}°**")

        with tab3:
            tab3.subheader("HIP")
            tab3.write('Hip (dalam bahasa Indonesia: pinggul) adalah bagian tubuh yang terletak di bawah perut, menghubungkan tubuh bagian atas dengan kaki.')
            maelhip = np.mean(np.abs(lhip["your left hip"] - lhip["Mean_Lhip"]))
            maerhip = np.mean(np.abs(rhip["your right hip"] - rhip["Mean_Rhip"]))
            col1, col2 = tab3.columns(2)
            with col1:
                st.plotly_chart(fig5, use_container_width=True)
                st.write(f"**Mean difference in left hip angle (Patient vs Normal): {maelhip:.2f}°**")
            with col2:
                st.plotly_chart(fig6, use_container_width=True)
                st.write(f"**Mean difference in right hip angle (Patient vs Normal): {maerhip:.2f}°**")

        with tab4:
            tab4.subheader("ANKLE")
            tab4.write('Ankle (dalam bahasa Indonesia: pergelangan kaki) adalah sendi yang terletak di antara kaki bagian bawah (tulang tibia dan fibula) dan bagian atas kaki (tulang talus).')
            maelankle = np.mean(np.abs(lankle["your left ankle"] - lankle["Mean_Lankle"]))
            maerankle = np.mean(np.abs(rankle["your right ankle"] - rankle["Mean_Rankle"]))
            col1, col2 = tab4.columns(2)
            with col1:
                st.plotly_chart(fig7, use_container_width=True)
                st.write(f"**Mean difference in left ankle angle (Patient vs Normal): {maelankle:.2f}°**")
            with col2:
                st.plotly_chart(fig8, use_container_width=True)
                st.write(f"**Mean difference in right ankle angle (Patient vs Normal): {maerankle:.2f}°**")

    def create_pelvis_figure(self, data, title, color):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data["Mean_Lpelvis" if "Mean_Lpelvis" in data.columns else "Mean_Rpelvis"], 
            mode='lines',
            name=f'Average {title}<br>(Normal Subjects)',
            line=dict(color=color),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(data["%cycle"], data["Mean_Lpelvis" if "Mean_Lpelvis" in data.columns else "Mean_Rpelvis"])]
        ))
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data["your left pelvis" if "your left pelvis" in data.columns else "your right pelvis"], 
            mode='lines',
            name='Patient',
            line=dict(color='black')
        ))
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data["Mean_Lpelvis" if "Mean_Lpelvis" in data.columns else "Mean_Rpelvis"] + data["std_Lpelvis" if "std_Lpelvis" in data.columns else "std_Rpelvis"], 
            mode='lines',
            name='Upper Bound',
            line=dict(color=color, width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data["Mean_Lpelvis" if "Mean_Lpelvis" in data.columns else "Mean_Rpelvis"] - data["std_Lpelvis" if "std_Lpelvis" in data.columns else "std_Rpelvis"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color=color, width=0),
            fill='tonexty',
            fillcolor=f'rgba({255 if color=="orange" else 0}, {165 if color=="orange" else 255}, {0 if color=="orange" else 255}, 0.2)',
            showlegend=True,
            hoverinfo='text',
            text=[f"Upper Bound: {cycle}%, {valup:.2f}°<br>Lower Bound: {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(data["%cycle"], data["Mean_Lpelvis" if "Mean_Lpelvis" in data.columns else "Mean_Rpelvis"] - data["std_Lpelvis" if "std_Lpelvis" in data.columns else "std_Rpelvis"], data["Mean_Lpelvis" if "Mean_Lpelvis" in data.columns else "Mean_Rpelvis"] + data["std_Lpelvis" if "std_Lpelvis" in data.columns else "std_Rpelvis"])]
        ))
        fig.update_layout(
            title=title,
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        return fig

    def create_joint_figure(self, data, title, color):
        mean_col = [col for col in data.columns if col.startswith('Mean_')][0]
        std_col = [col for col in data.columns if col.startswith('std_')][0]
        patient_col = [col for col in data.columns if col.startswith('your ')][0]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data[mean_col], 
            mode='lines',
            name=f'Average {title}<br>(Normal Subjects)',
            line=dict(color=color),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(data["%cycle"], data[mean_col])]
        ))
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data[patient_col], 
            mode='lines',
            name='Patient',
            line=dict(color='black')
        ))
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data[mean_col] + data[std_col], 
            mode='lines',
            name='Upper Bound',
            line=dict(color=color, width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data[mean_col] - data[std_col], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color=color, width=0),
            fill='tonexty',
            fillcolor=f'rgba({255 if color=="orange" else 0}, {165 if color=="orange" else 255}, {0 if color=="orange" else 255}, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound: {cycle}%, {valup:.2f}°<br>Lower Bound: {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(data["%cycle"], data[mean_col] - data[std_col], data[mean_col] + data[std_col])]
        ))
        fig.update_layout(
            title=title,
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        return fig

    def show_normal_dashboard(self):
        # st.markdown("---")
        
        # Tampilkan grafik normal tanpa data pasien
        px.defaults.template = 'plotly_dark'
        px.defaults.color_continuous_scale = 'reds'
        
        # Koneksi ke MongoDB
        client = get_mongo_client()
        db = client['GaitDB']
        collection = db['gait_data']

        # Membaca data dari MongoDB
        cursor = collection.find().limit(100)
        data = list(cursor)
        if len(data) == 0:
            st.error("❌ Database Normal Belum Ada. Silahkan Upload Data Normal pada Menu 'Input Data GAIT Normal'")
            st.info("📝 Untuk melihat dashboard analisis gait, Anda perlu mengupload data subjek normal terlebih dahulu.")
            return
            
        # Normalisasi data untuk DataFrame
        df = pd.json_normalize(data)
        # Mengubah nama kolom untuk mempermudah akses
        df.columns = df.columns.str.replace('Trial Information.', '')
        df.columns = df.columns.str.replace('Subject Parameters.', '')
        df.columns = df.columns.str.replace('Body Measurements.', '')
        df.columns = df.columns.str.replace('Norm Kinematics.', '')

        # ====== FILTER DI ATAS ======
        st.markdown("<div class='filter-box'>", unsafe_allow_html=True)
        st.markdown("### Filter Data")

        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            # Filter usia
            min_age = df['Age'].min()
            max_age = df['Age'].max()
            age_range = st.slider(
                'Filter by Age Range:',
                min_value=min_age,
                max_value=max_age,
                value=(min_age, max_age)
            )

        with col2:
            # filter BMI
            bmi_options = ["All BMI Classification"] + list(df["BMI Classification"].value_counts().keys().sort_values())
            classbmi = st.selectbox(label="BMI Classification", options=bmi_options)

        with col3:
            # filter gender
            gender_mapping = {
                "L": "Pria",
                "P": "Wanita"
            }
            df["Gender"] = df["Gender"].map(gender_mapping)
            gender_options = ["All Gender"] + list(df["Gender"].value_counts().keys().sort_values())
            gender = st.selectbox(label="Gender", options=gender_options)

        st.markdown("</div>", unsafe_allow_html=True)
        # st.markdown("---")
            
        # Apply filters
        filtered_df = df[(df['Age'] >= age_range[0]) & (df['Age'] <= age_range[1])]
        if classbmi != "All BMI Classification":
            filtered_df = filtered_df[filtered_df['BMI Classification'] == classbmi]
        if gender != "All Gender":
            filtered_df = filtered_df[filtered_df["Gender"] == gender]
            
        if filtered_df.empty:
            st.error(f"There is no data with gender {gender} classified as {classbmi}.")
        else:
            st.markdown(f"**Total Records:** {len(filtered_df)}")
            
            # Tampilkan grafik normal saja (tanpa data pasien)
            self.show_normal_charts_only(filtered_df)
            
    def show_normal_charts_only(self, filtered_df):
        # Pelvis
        percentage_cycle = pd.DataFrame(filtered_df['Percentage of Gait Cycle'].tolist())
        l_pelvis_angles = pd.DataFrame(filtered_df['LPelvisAngles_X'].tolist())
        r_pelvis_angles = pd.DataFrame(filtered_df['RPelvisAngles_X'].tolist())

        percentage_cycle.columns = [f"%cycle_{i}" for i in range(percentage_cycle.shape[1])]
        l_pelvis_angles.columns = [f"L_Pelvis_{i}" for i in range(l_pelvis_angles.shape[1])]
        r_pelvis_angles.columns = [f"R_Pelvis_{i}" for i in range(r_pelvis_angles.shape[1])]

        mean_l_pelvis = l_pelvis_angles.mean(axis=0).values
        std_l_pelvis = l_pelvis_angles.std(axis=0)/np.sqrt(l_pelvis_angles.shape[0])
        mean_r_pelvis = r_pelvis_angles.mean(axis=0).values
        std_r_pelvis = r_pelvis_angles.std(axis=0)/np.sqrt(r_pelvis_angles.shape[0])

        std_l_pelvis = std_l_pelvis.values if isinstance(std_l_pelvis, pd.Series) else std_l_pelvis
        std_r_pelvis = std_r_pelvis.values if isinstance(std_r_pelvis, pd.Series) else std_r_pelvis

        lpelvis = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lpelvis': mean_l_pelvis,
            'std_Lpelvis': std_l_pelvis
        })

        rpelvis = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rpelvis': mean_r_pelvis,
            'std_Rpelvis': std_r_pelvis
        })
        
        ## Create the figure for Pelvis
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=lpelvis["%cycle"], 
            y=lpelvis["Mean_Lpelvis"], 
            mode='lines',
            name='Average Left Pelvis<br>(Normal Subjects)',
            line=dict(color='orange'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lpelvis["%cycle"], lpelvis["Mean_Lpelvis"])]
        ))
        fig1.add_trace(go.Scatter(
            x=lpelvis["%cycle"], 
            y=lpelvis["Mean_Lpelvis"] + lpelvis["std_Lpelvis"], 
            mode='lines',
            name='Upper Bound (Left)',
            line=dict(color='orange', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig1.add_trace(go.Scatter(
            x=lpelvis["%cycle"], 
            y=lpelvis["Mean_Lpelvis"] - lpelvis["std_Lpelvis"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='orange', width=0),
            fill='tonexty',
            fillcolor='rgba(255, 165, 0, 0.2)',
            showlegend=True,
            hoverinfo='text',
            text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lpelvis["%cycle"], lpelvis["Mean_Lpelvis"] - lpelvis["std_Lpelvis"], lpelvis["Mean_Lpelvis"] + lpelvis["std_Lpelvis"])]
        ))
        fig1.update_layout(
            title="Left Pelvis",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=rpelvis["%cycle"], 
            y=rpelvis["Mean_Rpelvis"], 
            mode='lines',
            name='Average Right Pelvis<br>(Normal Subjects)',
            line=dict(color='dark blue'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rpelvis["%cycle"], rpelvis["Mean_Rpelvis"])]
        ))
        fig2.add_trace(go.Scatter(
            x=rpelvis["%cycle"], 
            y=rpelvis["Mean_Rpelvis"] + rpelvis["std_Rpelvis"], 
            mode='lines',
            name='Upper Bound (Right)',
            line=dict(color='dark blue', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig2.add_trace(go.Scatter(
            x=rpelvis["%cycle"], 
            y=rpelvis["Mean_Rpelvis"] - rpelvis["std_Rpelvis"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='dark blue', width=0),
            fill='tonexty',
            fillcolor='rgba(0, 255, 255, 0.2)',
            showlegend=True,
            hoverinfo='text',
            text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rpelvis["%cycle"], rpelvis["Mean_Rpelvis"] - rpelvis["std_Rpelvis"], rpelvis["Mean_Rpelvis"] + rpelvis["std_Rpelvis"])]
        ))
        fig2.update_layout(
            title="Right Pelvis",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )

        # KNEE
        l_knee_angles = pd.DataFrame(filtered_df['LKneeAngles_X'].tolist())
        r_knee_angles = pd.DataFrame(filtered_df['RKneeAngles_X'].tolist())

        l_knee_angles.columns = [f"L_Knee_{i}" for i in range(l_knee_angles.shape[1])]
        r_knee_angles.columns = [f"R_Knee_{i}" for i in range(r_knee_angles.shape[1])]

        mean_l_knee = l_knee_angles.mean(axis=0).values
        std_l_knee = l_knee_angles.std(axis=0) / np.sqrt(l_knee_angles.shape[0])
        mean_r_knee = r_knee_angles.mean(axis=0).values
        std_r_knee = r_knee_angles.std(axis=0) / np.sqrt(r_knee_angles.shape[0])

        std_l_knee = std_l_knee.values if isinstance(std_l_knee, pd.Series) else std_l_knee
        std_r_knee = std_r_knee.values if isinstance(std_r_knee, pd.Series) else std_r_knee

        lknee = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lknee': mean_l_knee,
            'std_Lknee': std_l_knee
        })
        
        rknee = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rknee': mean_r_knee,
            'std_Rknee': std_r_knee
        })

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=lknee["%cycle"], 
            y=lknee["Mean_Lknee"], 
            mode='lines',
            name='Average Left Knee<br>(Normal Subjects)',
            line=dict(color='orange'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lknee["%cycle"], lknee["Mean_Lknee"])]
        ))
        fig3.add_trace(go.Scatter(
            x=lknee["%cycle"], 
            y=lknee["Mean_Lknee"] + lknee["std_Lknee"], 
            mode='lines',
            name='Upper Bound (Left)',
            line=dict(color='orange', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig3.add_trace(go.Scatter(
            x=lknee["%cycle"], 
            y=lknee["Mean_Lknee"] - lknee["std_Lknee"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='orange', width=0),
            fill='tonexty',
            fillcolor='rgba(255, 165, 0, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lknee["%cycle"], lknee["Mean_Lknee"] - lknee["std_Lknee"], lknee["Mean_Lknee"] + lknee["std_Lknee"])]
        ))
        fig3.update_layout(
            title="Left Knee",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=rknee["%cycle"], 
            y=rknee["Mean_Rknee"], 
            mode='lines',
            name='Average Right Knee<br>(Normal Subjects)',
            line=dict(color='dark blue'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rknee["%cycle"], rknee["Mean_Rknee"])]
        ))
        fig4.add_trace(go.Scatter(
            x=rknee["%cycle"], 
            y=rknee["Mean_Rknee"] + rknee["std_Rknee"], 
            mode='lines',
            name='Upper Bound (Right)',
            line=dict(color='dark blue', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig4.add_trace(go.Scatter(
            x=rknee["%cycle"], 
            y=rknee["Mean_Rknee"] - rknee["std_Rknee"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='dark blue', width=0),
            fill='tonexty',
            fillcolor='rgba(0, 255, 255, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rknee["%cycle"], rknee["Mean_Rknee"] - rknee["std_Rknee"], rknee["Mean_Rknee"] + rknee["std_Rknee"])]
        ))
        fig4.update_layout(
            title="Right Knee",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )

        # HIP
        l_hip_angles = pd.DataFrame(filtered_df['LHipAngles_X'].tolist())
        r_hip_angles = pd.DataFrame(filtered_df['RHipAngles_X'].tolist())

        l_hip_angles.columns = [f"L_Hip_{i}" for i in range(l_hip_angles.shape[1])]
        r_hip_angles.columns = [f"R_Hip_{i}" for i in range(r_hip_angles.shape[1])]

        mean_l_hip = l_hip_angles.mean(axis=0).values
        std_l_hip = l_hip_angles.std(axis=0) / np.sqrt(l_hip_angles.shape[0])
        mean_r_hip = r_hip_angles.mean(axis=0).values
        std_r_hip = r_hip_angles.std(axis=0) / np.sqrt(r_hip_angles.shape[0])

        std_l_hip = std_l_hip.values if isinstance(std_l_hip, pd.Series) else std_l_hip
        std_r_hip = std_r_hip.values if isinstance(std_r_hip, pd.Series) else std_r_hip

        lhip = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lhip': mean_l_hip,
            'std_Lhip': std_l_hip
        })
        
        rhip = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rhip': mean_r_hip,
            'std_Rhip': std_r_hip
        })

        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(
            x=lhip["%cycle"], 
            y=lhip["Mean_Lhip"], 
            mode='lines',
            name='Average Left Hip<br>(Normal Subjects)',
            line=dict(color='orange'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lhip["%cycle"], lhip["Mean_Lhip"])]
        ))
        fig5.add_trace(go.Scatter(
            x=lhip["%cycle"], 
            y=lhip["Mean_Lhip"] + lhip["std_Lhip"], 
            mode='lines',
            name='Upper Bound (Left)',
            line=dict(color='orange', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig5.add_trace(go.Scatter(
            x=lhip["%cycle"], 
            y=lhip["Mean_Lhip"] - lhip["std_Lhip"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='orange', width=0),
            fill='tonexty',
            fillcolor='rgba(255, 165, 0, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lhip["%cycle"], lhip["Mean_Lhip"] - lhip["std_Lhip"], lhip["Mean_Lhip"] + lhip["std_Lhip"])]
        ))
        fig5.update_layout(
            title="Left Hip",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )
        
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(
            x=rhip["%cycle"], 
            y=rhip["Mean_Rhip"], 
            mode='lines',
            name='Average Right Hip<br>(Normal Subjects)',
            line=dict(color='dark blue'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rhip["%cycle"], rhip["Mean_Rhip"])]
        ))
        fig6.add_trace(go.Scatter(
            x=rhip["%cycle"], 
            y=rhip["Mean_Rhip"] + rhip["std_Rhip"], 
            mode='lines',
            name='Upper Bound (Right)',
            line=dict(color='dark blue', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig6.add_trace(go.Scatter(
            x=rhip["%cycle"], 
            y=rhip["Mean_Rhip"] - rhip["std_Rhip"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='dark blue', width=0),
            fill='tonexty',
            fillcolor='rgba(0, 255, 255, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rhip["%cycle"], rhip["Mean_Rhip"] - rhip["std_Rhip"], rhip["Mean_Rhip"] + rhip["std_Rhip"])]
        ))
        fig6.update_layout(
            title="Right Hip",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )

        # ANKLE
        l_ankle_angles = pd.DataFrame(filtered_df['LAnkleAngles_X'].tolist())
        r_ankle_angles = pd.DataFrame(filtered_df['RAnkleAngles_X'].tolist())

        l_ankle_angles.columns = [f"L_Ankle_{i}" for i in range(l_ankle_angles.shape[1])]
        r_ankle_angles.columns = [f"R_Ankle_{i}" for i in range(r_ankle_angles.shape[1])]

        mean_l_ankle = l_ankle_angles.mean(axis=0).values
        std_l_ankle = l_ankle_angles.std(axis=0) / np.sqrt(l_ankle_angles.shape[0])
        mean_r_ankle = r_ankle_angles.mean(axis=0).values
        std_r_ankle = r_ankle_angles.std(axis=0) / np.sqrt(r_ankle_angles.shape[0])

        std_l_ankle = std_l_ankle.values if isinstance(std_l_ankle, pd.Series) else std_l_ankle
        std_r_ankle = std_r_ankle.values if isinstance(std_r_ankle, pd.Series) else std_r_ankle

        lankle = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Lankle': mean_l_ankle,
            'std_Lankle': std_l_ankle
        })

        rankle = pd.DataFrame({
            "%cycle": list(range(101)),
            'Mean_Rankle': mean_r_ankle,
            'std_Rankle': std_r_ankle
        })
        
        fig7 = go.Figure()
        fig7.add_trace(go.Scatter(
            x=lankle["%cycle"], 
            y=lankle["Mean_Lankle"], 
            mode='lines',
            name='Average Left Ankle<br>(Normal Subjects)',
            line=dict(color='orange'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(lankle["%cycle"], lankle["Mean_Lankle"])]
        ))
        fig7.add_trace(go.Scatter(
            x=lankle["%cycle"], 
            y=lankle["Mean_Lankle"] + lankle["std_Lankle"], 
            mode='lines',
            name='Upper Bound (Left)',
            line=dict(color='orange', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig7.add_trace(go.Scatter(
            x=lankle["%cycle"], 
            y=lankle["Mean_Lankle"] - lankle["std_Lankle"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='orange', width=0),
            fill='tonexty',
            fillcolor='rgba(255, 165, 0, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Left): {cycle}%, {valup:.2f}°<br>Lower Bound (Left): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(lankle["%cycle"], lankle["Mean_Lankle"] - lankle["std_Lankle"], lankle["Mean_Lankle"] + lankle["std_Lankle"])]
        ))
        fig7.update_layout(
            title="Left Ankle",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )

        fig8 = go.Figure()
        fig8.add_trace(go.Scatter(
            x=rankle["%cycle"], 
            y=rankle["Mean_Rankle"], 
            mode='lines',
            name='Average Right Ankle<br>(Normal Subjects)',
            line=dict(color='dark blue'),
            hoverinfo='text',
            text=[f"Average Normal Subjects: {cycle}%, {val:.2f}°" for cycle, val in zip(rankle["%cycle"], rankle["Mean_Rankle"])]
        ))
        fig8.add_trace(go.Scatter(
            x=rankle["%cycle"], 
            y=rankle["Mean_Rankle"] + rankle["std_Rankle"], 
            mode='lines',
            name='Upper Bound (Right)',
            line=dict(color='dark blue', width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig8.add_trace(go.Scatter(
            x=rankle["%cycle"], 
            y=rankle["Mean_Rankle"] - rankle["std_Rankle"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color='dark blue', width=0),
            fill='tonexty',
            fillcolor='rgba(0, 255, 255, 0.2)',
            showlegend=False,
            hoverinfo='text',
            text=[f"Upper Bound (Right): {cycle}%, {valup:.2f}°<br>Lower Bound (Right): {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(rankle["%cycle"], rankle["Mean_Rankle"] - rankle["std_Rankle"], rankle["Mean_Rankle"] + rankle["std_Rankle"])]
        ))
        fig8.update_layout(
            title="Right Ankle",
            xaxis_title="%Cycle",
            yaxis_title="Value",
            template="plotly_dark",
            title_x=0.5,
            hovermode="x unified"
        )

        tab1, tab2, tab3, tab4 = st.tabs(["PELVIS", "KNEE","HIP","ANKLE"])

        with tab1:
            tab1.subheader("PELVIS")
            tab1.write(
                'Pelvis (dalam bahasa Indonesia: panggul) adalah struktur tulang yang berbentuk cekungan di bawah perut, '
                'di antara tulang pinggul, dan di atas paha.'
            )
            col1, col2 = tab1.columns(2)
            with col1:
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                st.plotly_chart(fig2, use_container_width=True)
                
        with tab2:
            tab2.subheader("KNEE")
            tab2.write(
                'Knee (dalam bahasa Indonesia: lutut) adalah bagian tubuh manusia yang terletak di antara paha dan betis, '
                'berfungsi sebagai sendi yang menghubungkan tulang femur (paha) dengan tulang tibia (betis).'
            )
            col1, col2 = tab2.columns(2)
            with col1:
                st.plotly_chart(fig3, use_container_width=True)
            with col2:
                st.plotly_chart(fig4, use_container_width=True)

        with tab3:
            tab3.subheader("HIP")
            tab3.write(
                'Hip (dalam bahasa Indonesia: pinggul) adalah bagian tubuh yang terletak di bawah perut, menghubungkan tubuh bagian atas dengan kaki.'
            )
            col1, col2 = tab3.columns(2)
            with col1:
                st.plotly_chart(fig5, use_container_width=True)
            with col2:
                st.plotly_chart(fig6, use_container_width=True)

        with tab4:
            tab4.subheader("ANKLE")
            tab4.write(
                'Ankle (dalam bahasa Indonesia: pergelangan kaki) adalah sendi yang terletak di antara kaki bagian bawah (tulang tibia dan fibula) dan bagian atas kaki (tulang talus).'
            )
            col1, col2 = tab4.columns(2)
            with col1:
                st.plotly_chart(fig7, use_container_width=True)
            with col2:
                st.plotly_chart(fig8, use_container_width=True)

# # Jalankan aplikasi
# if __name__ == "__main__":
#     app = TerapisPage()
#     app.run()