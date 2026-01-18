import streamlit as st
import pandas as pd
from pymongo import MongoClient
from datetime import datetime

# ======================= LOGIN FORM =======================
def login_form(role_label: str = "Admin"):
    st.set_page_config(page_title="Login Admin GAIT", page_icon="🦶", layout="wide")

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


# ======================= HALAMAN ADMIN =======================
class AdminPage:
    def __init__(self):
        self.admin_user = st.secrets["ADMIN_USERNAME"]
        self.admin_pass = st.secrets["ADMIN_PASSWORD"]
        # Koneksi MongoDB
        self.client = MongoClient(st.secrets["MONGO_URI"])
        self.db = self.client['GaitDB']
        self.collection = self.db['gait_data']
        
        # Inisialisasi session state untuk data pasien
        if 'pasien_list_initialized' not in st.session_state:
            st.session_state.pasien_list_initialized = False
            st.session_state.pasien_list = []

    # ---------- Styling ----------
    def _inject_css(self):
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

            /* Main content area */
            .main .block-container {
                padding-top: 2rem;
                padding-left: 2rem;
                padding-right: 2rem;
            }

            /* Stats cards */
            .stats-card {
                background: #ffffff !important;
                color: #000000 !important;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                border: 1px solid #ddd;
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .stats-number {
                font-size: 2rem;
                font-weight: bold;
                margin: 10px 0;
            }

            /* Panel styling */
            .panel {
                background-color: #fff;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }

            /* Account card */
            .account-card {
                background-color: #fff;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
                border-left: 4px solid #560000;
            }
        </style>
        """, unsafe_allow_html=True)

    def _load_pasien_data(self):
        """Memuat data pasien dari database sekali saja"""
        if not st.session_state.pasien_list_initialized:
            try:
                client = MongoClient(st.secrets["MONGO_URI"])
                db = client['GaitDB']
                collection = db['pasien_users']
                
                # Ambil semua data pasien
                pasien_data = list(collection.find({}))
                
                # Reset dan isi session state
                st.session_state.pasien_list = []
                for pasien in pasien_data:
                    st.session_state.pasien_list.append({
                        "NIK": pasien.get('nik', ''),
                        "Nama Lengkap": pasien.get('nama_lengkap', ''),
                        "TTL": pasien.get('ttl', ''),
                        "TB": pasien.get('tb', ''),
                        "BB": pasien.get('bb', ''),
                        "Jenis Kelamin": pasien.get('jenis_kelamin', ''),
                        "Tanggal Dibuat": pasien.get('tanggal_dibuat', '')
                    })
                
                st.session_state.pasien_list_initialized = True
                    
            except Exception as e:
                st.error(f"Error loading patient data: {e}")

    # ---------- Sidebar ----------
    def _sidebar(self):
        st.sidebar.markdown("<p class='sidebar-title'>Sistem Dashboard Pemeriksaan GAIT</p>", unsafe_allow_html=True)
        st.sidebar.markdown("<p class='sidebar-subtitle'>Menu</p>", unsafe_allow_html=True)

        menu = st.sidebar.radio(
            "",
            ["Home", "Manajemen User", "Data Normal GAIT", "Riwayat Pemeriksaan Pasien", "Logout"]
        )
        return menu

    # ---------- Kartu Admin ----------
    def _account_card(self, username="adminutama"):
        st.markdown("### Beranda Admin")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="stats-card">
                <div>Total Pasien</div>
                <div class="stats-number">{len(st.session_state.pasien_list)}</div>
                <div>Terdaftar</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_data = self.collection.count_documents({})
            st.markdown(f"""
            <div class="stats-card">
                <div>Data Normal</div>
                <div class="stats-number">{total_data}</div>
                <div>Dataset</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Hitung pemeriksaan pasien
            try:
                client = MongoClient(st.secrets["MONGO_URI"])
                db = client['GaitDB']
                collection = db['patient_examinations']
                total_exams = collection.count_documents({})
                st.markdown(f"""
                <div class="stats-card">
                    <div>Pemeriksaan</div>
                    <div class="stats-number">{total_exams}</div>
                    <div>Total</div>
                </div>
                """, unsafe_allow_html=True)
            except:
                st.markdown(f"""
                <div class="stats-card">
                    <div>Pemeriksaan</div>
                    <div class="stats-number">0</div>
                    <div>Total</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("""
        <div class="account-card">
            <h4>👤 ADMIN UTAMA</h4>
            <p>Selamat datang di Dashboard Admin GAIT Clinic. Gunakan menu di sidebar untuk mengelola sistem.</p>
        </div>
        """, unsafe_allow_html=True)

    # ---------- Data Pasien & Terapis ----------
    def _panel_data(self):
        # Load data pasien sebelum menampilkan
        self._load_pasien_data()
        
        st.markdown("### 👥 Manajemen Data Pengguna")
        
        # Tab untuk jenis user yang berbeda
        tabs = st.tabs(["📋 Pasien", "🧑‍⚕️ Terapis", "👨‍💼 Admin", "➕ Tambah User Baru"])

        pasien_data = st.session_state.get("pasien_list", [])

        # Data terapis dari database
        terapis_data = self._get_terapis_data()
        
        # Data admin dari database
        admin_data = self._get_admin_data()

        with tabs[0]:
            st.subheader("Daftar Pasien Terdaftar")
            
            if pasien_data:
                # Tampilkan statistik
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Pasien", len(pasien_data))
                with col2:
                    male_count = len([p for p in pasien_data if p.get('Jenis Kelamin') == 'Laki-laki'])
                    st.metric("Pasien Laki-laki", male_count)
                with col3:
                    female_count = len([p for p in pasien_data if p.get('Jenis Kelamin') == 'Perempuan'])
                    st.metric("Pasien Perempuan", female_count)
                
                # Buat dataframe dengan nomor urut
                df_pasien = pd.DataFrame(pasien_data)
                df_pasien.insert(0, 'No', range(1, len(df_pasien) + 1))
                
                st.dataframe(df_pasien, use_container_width=True, hide_index=True)
            else:
                st.info("📝 Belum ada data pasien terdaftar")

        with tabs[1]:
            st.subheader("Daftar Terapis Terdaftar")
            
            if terapis_data:
                df_terapis = pd.DataFrame(terapis_data)
                df_terapis.insert(0, 'No', range(1, len(df_terapis) + 1))
                
                st.metric("Total Terapis", len(terapis_data))
                st.dataframe(df_terapis, use_container_width=True, hide_index=True)
            else:
                st.info("🧑‍⚕️ Belum ada data terapis terdaftar")

        with tabs[2]:
            st.subheader("Daftar Admin Terdaftar")
            
            if admin_data:
                df_admin = pd.DataFrame(admin_data)
                df_admin.insert(0, 'No', range(1, len(df_admin) + 1))
                
                st.metric("Total Admin", len(admin_data))
                st.dataframe(df_admin, use_container_width=True, hide_index=True)
            else:
                st.info("👨‍💼 Belum ada data admin terdaftar")

        with tabs[3]:
            st.subheader("➕ Tambah User Baru")
            
            with st.form("tambah_user_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    role = st.selectbox("Jenis User", ["Pasien", "Terapis", "Admin"])
                    username = st.text_input("Username/NIK", placeholder="Masukkan NIK untuk pasien, username untuk lainnya")
                    nama_lengkap = st.text_input("Nama Lengkap")
                    password = st.text_input("Password", type="password")
                    
                with col2:
                    if role != "Admin":
                        # Ganti TTL dengan tanggal lahir menggunakan kalender
                        tanggal_lahir = st.date_input(
                            "Tanggal Lahir",
                            min_value=datetime(1900, 1, 1),
                            max_value=datetime.now(),
                            value=datetime(1990, 1, 1)
                        )
                        tb = st.number_input("Tinggi Badan (cm)", min_value=0)
                        bb = st.number_input("Berat Badan (kg)", min_value=0)
                        jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
                    else:
                        # Untuk admin, sembunyikan field yang tidak perlu
                        tanggal_lahir = datetime(1990, 1, 1)
                        tb = 0
                        bb = 0
                        jenis_kelamin = "Laki-laki"
                        st.info("🔒 Field tambahan tidak diperlukan untuk Admin")
                
                submitted = st.form_submit_button("💾 Tambah User Baru")
                
                if submitted:
                    if not username or not nama_lengkap or not password:
                        st.error("❌ Harap isi semua field yang wajib!")
                    else:
                        if self._add_new_user({
                            'role': role.lower(),
                            'username': username,
                            'nama_lengkap': nama_lengkap,
                            'password': password,
                            'tanggal_lahir': tanggal_lahir.strftime("%d-%m-%Y"),  # Format DD-MM-YYYY
                            'tb': tb,
                            'bb': bb,
                            'jenis_kelamin': jenis_kelamin
                        }):
                            st.success(f"✅ User {nama_lengkap} berhasil ditambahkan sebagai {role}!")
                            st.balloons()
                            
                            # Reset form
                            st.rerun()

    def _get_terapis_data(self):
        """Mendapatkan data terapis dari database"""
        try:
            client = MongoClient(st.secrets["MONGO_URI"])
            db = client['GaitDB']
            collection = db['users']
            
            terapis_data = list(collection.find({'role': 'terapis'}))
            
            data = []
            for terapis in terapis_data:
                data.append({
                    "NIK": terapis.get('username', ''),
                    "Nama Lengkap": terapis.get('nama_lengkap', ''),
                    "Tanggal Lahir": terapis.get('tanggal_lahir', ''),  # Ganti TTL jadi Tanggal Lahir
                    "TB": terapis.get('tb', ''),
                    "BB": terapis.get('bb', ''),
                    "Jenis Kelamin": terapis.get('jenis_kelamin', ''),
                    "Tanggal Dibuat": terapis.get('tanggal_dibuat', '')
                })
            
            return data
        except Exception as e:
            st.error(f"Error loading therapist data: {e}")
            return []

    def _get_admin_data(self):
        """Mendapatkan data admin dari database"""
        try:
            client = MongoClient(st.secrets["MONGO_URI"])
            db = client['GaitDB']
            collection = db['users']
            
            admin_data = list(collection.find({'role': 'admin'}))
            
            data = []
            for admin in admin_data:
                data.append({
                    "username": admin.get('username', ''),
                    "nama_lengkap": admin.get('nama_lengkap', ''),
                    "role": admin.get('role', ''),
                    "Tanggal Dibuat": admin.get('tanggal_dibuat', '')
                })
            
            return data
        except Exception as e:
            st.error(f"Error loading admin data: {e}")
            return []

    def _add_new_user(self, user_data):
        """Menambahkan user baru ke database"""
        try:
            client = MongoClient(st.secrets["MONGO_URI"])
            db = client['GaitDB']
            
            # Cek apakah username sudah ada
            if user_data['role'] == 'pasien':
                collection = db['pasien_users']
                existing_user = collection.find_one({'nik': user_data['username']})
                if existing_user:
                    st.error("❌ NIK sudah terdaftar sebagai pasien")
                    return False
            else:
                collection = db['users']
                existing_user = collection.find_one({
                    'username': user_data['username'],
                    'role': user_data['role']
                })
                if existing_user:
                    st.error(f"❌ Username sudah terdaftar sebagai {user_data['role']}")
                    return False
            
            # Siapkan data untuk disimpan
            if user_data['role'] == 'pasien':
                new_user = {
                    'nik': user_data['username'],
                    'nama_lengkap': user_data['nama_lengkap'],
                    'password': user_data['password'],
                    'tanggal_lahir': user_data['tanggal_lahir'],  # Ganti ttl jadi tanggal_lahir
                    'tb': user_data['tb'],
                    'bb': user_data['bb'],
                    'jenis_kelamin': user_data['jenis_kelamin'],
                    'tanggal_dibuat': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                result = db['pasien_users'].insert_one(new_user)
                # Update session state untuk pasien
                st.session_state.pasien_list_initialized = False
            else:
                new_user = {
                    'username': user_data['username'],
                    'nama_lengkap': user_data['nama_lengkap'],
                    'password': user_data['password'],
                    'role': user_data['role'],
                    'tanggal_lahir': user_data['tanggal_lahir'],  # Ganti ttl jadi tanggal_lahir
                    'tb': user_data['tb'],
                    'bb': user_data['bb'],
                    'jenis_kelamin': user_data['jenis_kelamin'],
                    'tanggal_dibuat': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                result = db['users'].insert_one(new_user)
            
            return result.inserted_id is not None
            
        except Exception as e:
            st.error(f"❌ Error menambahkan user: {e}")
            return False

    # ---------- Manajemen Data Normal GAIT ----------
    def _manage_normal_data(self):
        st.markdown("### 📊 Manajemen Data Normal GAIT")
        
        # Stats Overview
        total_data = self.collection.count_documents({})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Data Normal", total_data)
        
        with col2:
            male_count = self.collection.count_documents({"Subject Parameters.Gender": "L"})
            st.metric("Data Pria", male_count)
        
        with col3:
            female_count = self.collection.count_documents({"Subject Parameters.Gender": "P"})
            st.metric("Data Wanita", female_count)
            
        # with col4:
        #     # Data dengan usia di bawah 30
        #     young_count = self.collection.count_documents({"Subject Parameters.Age": {"$lt": 30}})
        #     st.metric("Usia < 30", young_count)
        
        st.markdown("---")
        
        # Tampilkan data dalam tabel
        st.subheader("📋 Daftar Data Normal")
        
        # Ambil semua data dari MongoDB
        data = list(self.collection.find())
        
        if not data:
            st.warning("❌ Tidak ada data normal di database. Silakan upload data melalui menu terapis.")
            return
        
        # Siapkan data untuk dataframe
        table_data = []
        for doc in data:
            subject_params = doc.get('Subject Parameters', {})
            table_data.append({
                '_id': str(doc['_id']),
                'Nama': subject_params.get('Subject Name', 'N/A'),
                'Usia': subject_params.get('Age', 'N/A'),
                'Gender': subject_params.get('Gender', 'N/A'),
                'Tinggi (cm)': round(subject_params.get('Height (mm)', 0) / 10, 1) if subject_params.get('Height (mm)') else 'N/A',
                'Berat (kg)': subject_params.get('Bodymass (kg)', 'N/A'),
                'BMI': round(subject_params.get('BMI', 0), 2) if subject_params.get('BMI') else 'N/A',
                'Klasifikasi BMI': subject_params.get('BMI Classification', 'N/A'),
                'Tanggal Upload': doc.get('upload_date', 'N/A')
            })
        
        df = pd.DataFrame(table_data)
        
        # Tampilkan dataframe tanpa kolom _id
        display_df = df.drop('_id', axis=1)
        st.dataframe(display_df, use_container_width=True)
        
        # Fitur Edit dan Delete
        st.markdown("---")
        st.subheader("🛠️ Kelola Data")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Edit Data")
            
            # Buat pilihan untuk selectbox dengan format: "Nama (Usia, Gender)"
            edit_options = []
            for doc in data:
                subject_params = doc.get('Subject Parameters', {})
                name = subject_params.get('Subject Name', 'N/A')
                age = subject_params.get('Age', 'N/A')
                gender = subject_params.get('Gender', 'N/A')
                display_text = f"{name} ({age} tahun, {gender})"
                edit_options.append((str(doc['_id']), display_text))
            
            if edit_options:
                # Tambahkan opsi default di awal
                options_with_default = [("", "Pilih Data untuk Diedit")] + edit_options
                
                selected_option = st.selectbox(
                    "Pilih data untuk diedit:",
                    options=[opt[0] for opt in options_with_default],
                    format_func=lambda x: next((display for id, display in options_with_default if id == x), 'Pilih Data untuk Diedit')
                )
                
                # Hanya tampilkan form edit jika user memilih data (bukan opsi default)
                if selected_option and selected_option != "":
                    selected_doc = next((doc for doc in data if str(doc['_id']) == selected_option), None)
                    if selected_doc:
                        with st.form("edit_form"):
                            subject_params = selected_doc.get('Subject Parameters', {})
                            new_name = st.text_input("Nama Subjek", value=subject_params.get('Subject Name', ''))
                            new_age = st.number_input("Usia", min_value=0, max_value=120, value=subject_params.get('Age', 0))
                            new_gender = st.selectbox("Jenis Kelamin", ["L", "P"], index=0 if subject_params.get('Gender') == 'L' else 1)
                            new_height = st.number_input("Tinggi (mm)", min_value=0, value=subject_params.get('Height (mm)', 0))
                            new_weight = st.number_input("Berat (kg)", min_value=0.0, value=subject_params.get('Bodymass (kg)', 0.0))
                            
                            if st.form_submit_button("💾 Update Data"):
                                update_data = {
                                    "Subject Parameters.Subject Name": new_name,
                                    "Subject Parameters.Age": new_age,
                                    "Subject Parameters.Gender": new_gender,
                                    "Subject Parameters.Height (mm)": new_height,
                                    "Subject Parameters.Bodymass (kg)": new_weight
                                }
                                # Hitung ulang BMI
                                height_m = new_height / 1000
                                new_bmi = new_weight / (height_m ** 2) if height_m > 0 else 0
                                bmi_class = (
                                    "Kurus Berat" if new_bmi < 17.0 else
                                    "Kurus Ringan" if 17.0 <= new_bmi <= 18.4 else
                                    "Normal" if 18.5 <= new_bmi <= 25.0 else
                                    "Gemuk Ringan" if 25.1 <= new_bmi <= 27.0 else
                                    "Gemuk Berat"
                                )
                                update_data["Subject Parameters.BMI"] = round(new_bmi, 2)
                                update_data["Subject Parameters.BMI Classification"] = bmi_class
                                
                                self.collection.update_one({'_id': selected_doc['_id']}, {'$set': update_data})
                                st.success("✅ Data berhasil diupdate!")
                                st.rerun()
                else:
                    st.info("👆 Pilih data dari dropdown di atas untuk mulai mengedit")
            else:
                st.info("Tidak ada data yang dapat diedit")
        
        with col2:
            st.markdown("#### Hapus Data")
            
            # Buat pilihan untuk delete dengan format yang sama
            delete_options = []
            for doc in data:
                subject_params = doc.get('Subject Parameters', {})
                name = subject_params.get('Subject Name', 'N/A')
                age = subject_params.get('Age', 'N/A')
                gender = subject_params.get('Gender', 'N/A')
                display_text = f"{name} ({age} tahun, {gender})"
                delete_options.append((str(doc['_id']), display_text))
            
            if delete_options:
                # Tambahkan opsi default di awal
                delete_options_with_default = [("", "Pilih Data untuk Dihapus")] + delete_options
                
                selected_delete_option = st.selectbox(
                    "Pilih data untuk dihapus:",
                    options=[opt[0] for opt in delete_options_with_default],
                    key="delete_select",
                    format_func=lambda x: next((display for id, display in delete_options_with_default if id == x), 'Pilih Data untuk Dihapus')
                )
                
                # Hanya tampilkan konfirmasi penghapusan jika user memilih data (bukan opsi default)
                if selected_delete_option and selected_delete_option != "":
                    selected_doc = next((doc for doc in data if str(doc['_id']) == selected_delete_option), None)
                    if selected_doc:
                        subject_params = selected_doc.get('Subject Parameters', {})
                        st.warning(f"⚠️ Anda akan menghapus data: **{subject_params.get('Subject Name', 'N/A')}**")
                        st.write(f"- Usia: {subject_params.get('Age', 'N/A')}")
                        st.write(f"- Gender: {subject_params.get('Gender', 'N/A')}")
                        st.write(f"- Tinggi: {subject_params.get('Height (mm)', 'N/A')} mm")
                        st.write(f"- Berat: {subject_params.get('Bodymass (kg)', 'N/A')} kg")
                        st.write(f"- BMI: {subject_params.get('BMI', 'N/A')} ({subject_params.get('BMI Classification', 'N/A')})")
                        
                        # Konfirmasi penghapusan
                        col_confirm1, col_confirm2 = st.columns(2)
                        with col_confirm1:
                            if st.button("🗑️ Hapus Permanen", type="secondary", use_container_width=True):
                                self.collection.delete_one({'_id': selected_doc['_id']})
                                st.success("✅ Data berhasil dihapus!")
                                st.rerun()
                        with col_confirm2:
                            if st.button("❌ Batal", use_container_width=True):
                                st.info("Penghapusan dibatalkan")
                else:
                    st.info("👆 Pilih data dari dropdown di atas untuk menghapus")
            else:
                st.info("Tidak ada data yang dapat dihapus")

    # ---------- Riwayat Pemeriksaan Pasien ----------
    def _patient_examination_history(self):
        st.markdown("### 🏥 Riwayat Pemeriksaan Pasien")
        
        try:
            # Koneksi ke MongoDB
            client = MongoClient(st.secrets["MONGO_URI"])
            db = client['GaitDB']
            collection = db['patient_examinations']
            
            # Ambil semua data pemeriksaan
            examinations = list(collection.find().sort('patient_info.upload_date', -1))
            
            if not examinations:
                st.info("📝 Belum ada riwayat pemeriksaan pasien.")
                return
            
            # Stats Overview
            total_exams = len(examinations)
            # unique_patients = len(set(exam['patient_info'].get('nik', '') for exam in examinations if exam['patient_info'].get('nik')))
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Pemeriksaan", total_exams)
            # with col2:
            #     st.metric("Total Pasien Unik", unique_patients)
            with col2:
                # Hitung pemeriksaan bulan ini
                current_month = datetime.now().strftime("%Y-%m")
                monthly_exams = len([exam for exam in examinations 
                                if exam['patient_info'].get('upload_date', '').startswith(current_month)])
                st.metric("Pemeriksaan Bulan Ini", monthly_exams)
            
            st.markdown("---")
            
            # Siapkan data untuk tabel
            table_data = []
            for exam in examinations:
                patient_info = exam.get('patient_info', {})
                file_info = exam.get('file_info', {})
                gait_data = exam.get('gait_data', {})
                subject_params = gait_data.get('Subject Parameters', {})
                
                table_data.append({
                    '_id': str(exam['_id']),
                    'Tanggal Pemeriksaan': patient_info.get('tanggal_pemeriksaan', 'N/A'),
                    'NIK Pasien': patient_info.get('nik', 'N/A'),
                    'Nama Pasien': patient_info.get('nama', 'N/A'),
                    'Usia': subject_params.get('Age', 'N/A'),
                    'Gender': subject_params.get('Gender', 'N/A'),
                    'Tinggi (cm)': round(subject_params.get('Height (mm)', 0) / 10, 1) if subject_params.get('Height (mm)') else 'N/A',
                    'Berat (kg)': subject_params.get('Bodymass (kg)', 'N/A'),
                    'File Name': file_info.get('file_name', 'N/A'),
                    'Tanggal Upload': patient_info.get('upload_date', 'N/A')
                })
            
            df = pd.DataFrame(table_data)
            
            # Filter options
            st.markdown("### 🔍 Filter Data")
            col1, col2 = st.columns(2)
            with col1:
                filter_nik = st.text_input("Filter NIK:")
            with col2:
                filter_nama = st.text_input("Filter Nama:")
            
            # Apply filters
            filtered_df = df.copy()
            if filter_nik:
                filtered_df = filtered_df[filtered_df['NIK Pasien'].str.contains(filter_nik, case=False, na=False)]
            if filter_nama:
                filtered_df = filtered_df[filtered_df['Nama Pasien'].str.contains(filter_nama, case=False, na=False)]
            
            # Tampilkan tabel
            display_df = filtered_df.drop('_id', axis=1)
            st.dataframe(display_df, use_container_width=True)
            
            # Download data
            csv = filtered_df.drop('_id', axis=1).to_csv(index=False)
            st.download_button(
                label="📥 Download Data Pemeriksaan sebagai CSV",
                data=csv,
                file_name=f"riwayat_pemeriksaan_pasien_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"❌ Error mengambil data riwayat pemeriksaan: {e}")

    # ---------- Halaman Utama ----------
    def run(self):
        self._inject_css()
        if 'admin_logged_in' not in st.session_state:
            st.session_state.admin_logged_in = False

        # Login Page
        if not st.session_state.admin_logged_in:
            username, password, submit = login_form("Admin")
            if submit:
                if username == self.admin_user and password == self.admin_pass:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Username atau password salah!")
            return

        # Setelah login
        menu = self._sidebar()
        if menu == "Home":
            self._account_card()
            st.success("🎉 Selamat datang di Dashboard Admin GAIT Clinic!")
            st.info("Gunakan menu di sidebar untuk mengelola data pengguna dan data normal GAIT.")
            
        elif menu == "Manajemen User":
            self._panel_data()
            
        elif menu == "Data Normal GAIT":
            self._manage_normal_data()
            
        elif menu == "Riwayat Pemeriksaan Pasien":
            self._patient_examination_history()
            
        elif menu == "Logout":
            st.session_state.admin_logged_in = False
            st.session_state.pasien_list_initialized = False  # Reset flag saat logout
            st.rerun()
