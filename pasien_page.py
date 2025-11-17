import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, datetime
from pymongo import MongoClient

# Optimasi koneksi MongoDB
def get_mongo_client():
    return MongoClient(
        st.secrets["MONGO_URI"],
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=5000
    )

# ====================== LOGIN FORM PASIEN ======================
def login_form_pasien():
    st.markdown("""
    <style>
        .block-container {
            padding-top: 4vh !important;
            padding-bottom: 2rem !important;
            max-width: 90vw;
            margin: auto;
        }

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
        .back-fixed:hover { background-color: #660000; }

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

        label, .stTextInput label { font-weight: 600 !important; }

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

        p.register-link {
            color: #a30000 !important;
            font-weight: 600;
            text-align: center;
            margin-top: 1rem;
            margin-bottom: 0.4rem;
        }

        p.footer {
            text-align: center;
            font-size: 0.85rem;
            color: #444;
            margin-top: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Tombol kembali
    if st.button("Kembali", key="back_btn"):
        st.session_state.role = None
        st.rerun()

    # Judul
    st.markdown("<h2>Aplikasi GAIT Clinic</h2>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Selamat Datang di Sistem Dashboard Pemeriksaan GAIT</p>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    # Form login
    st.subheader("Login - Pasien")
    nik = st.text_input("NIK", placeholder="Masukkan NIK anda")
    password = st.text_input("Password", type="password", placeholder="Masukkan password anda")

    submit = st.button("Login", use_container_width=True)

    st.markdown("<p class='register-link'>Belum punya akun?</p>", unsafe_allow_html=True)
    if st.button("Register", use_container_width=True):
        st.session_state.show_register = True
        st.rerun()

    return nik, password, submit


# ====================== KELAS PASIEN PAGE ======================
class PasienPage:
    def __init__(self):
        # Inisialisasi session state
        st.session_state.setdefault("pasien_auth", {})
        st.session_state.setdefault("pasien_list", [])
        st.session_state.setdefault("show_register", False)
        st.session_state.setdefault("pasien_logged_in", False)
        st.session_state.setdefault("pasien_nik", None)
        
        # Load data dari database saat inisialisasi
        self._load_pasien_data_from_db()

    def _load_pasien_data_from_db(self):
        """Memuat data pasien dari database MongoDB"""
        try:
            client = get_mongo_client()
            db = client['GaitDB']
            collection = db['pasien_users']
            
            # Ambil semua data pasien
            pasien_data = list(collection.find({}))
            
            # Update session state dengan data dari database
            for pasien in pasien_data:
                nik = pasien.get('nik')
                password = pasien.get('password')
                if nik and password:
                    st.session_state["pasien_auth"][nik] = password
                    st.session_state["pasien_list"].append({
                        "NIK": nik,
                        "Nama Lengkap": pasien.get('nama_lengkap', ''),
                        "TTL": pasien.get('ttl', ''),
                        "TB": pasien.get('tb', ''),
                        "BB": pasien.get('bb', ''),
                        "Jenis Kelamin": pasien.get('jenis_kelamin', ''),
                        "Tanggal Dibuat": pasien.get('tanggal_dibuat', '')
                    })
                    
        except Exception as e:
            st.error(f"Error loading patient data: {e}")

    def _save_registration_to_db(self, data):
        """Menyimpan data registrasi ke database MongoDB"""
        try:
            client = get_mongo_client()
            db = client['GaitDB']
            collection = db['pasien_users']
            
            # Cek apakah NIK sudah ada
            existing_pasien = collection.find_one({"nik": data["NIK"]})
            if existing_pasien:
                st.error("❌ NIK sudah terdaftar. Silakan gunakan NIK lain.")
                return False
            
            # Simpan data ke database
            pasien_doc = {
                "nik": data["NIK"],
                "password": data["Password"],
                "nama_lengkap": data["Nama Lengkap"],
                "ttl": data["TTL"].strftime("%d-%m-%Y"),
                "tb": data["TB"],
                "bb": data["BB"],
                "jenis_kelamin": data["Jenis Kelamin"],
                "tanggal_dibuat": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "role": "pasien"
            }
            
            result = collection.insert_one(pasien_doc)
            
            # Update session state
            st.session_state["pasien_auth"][data["NIK"]] = data["Password"]
            st.session_state["pasien_list"].append({
                "NIK": data["NIK"],
                "Nama Lengkap": data["Nama Lengkap"],
                "TTL": data["TTL"].strftime("%d-%m-%Y"),
                "TB": data["TB"],
                "BB": data["BB"],
                "Jenis Kelamin": data["Jenis Kelamin"],
                "Tanggal Dibuat": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error menyimpan data ke database: {e}")
            return False

    def _get_pemeriksaan_data(self, nik, tanggal):
        """Fungsi untuk mendapatkan data pemeriksaan berdasarkan NIK dan tanggal dari database"""
        try:
            client = get_mongo_client()
            db = client['GaitDB']
            collection = db['patient_examinations']
            
            # Cari data pemeriksaan berdasarkan NIK dan tanggal
            pemeriksaan = collection.find_one({
                'patient_info.nik': nik,
                'patient_info.tanggal_pemeriksaan': tanggal.strftime("%Y-%m-%d")
            })
            
            return pemeriksaan
            
        except Exception as e:
            st.error(f"Error mengambil data pemeriksaan: {e}")
            return None

    def _get_all_pemeriksaan_dates(self, nik):
        """Mendapatkan semua tanggal pemeriksaan untuk pasien tertentu"""
        try:
            client = get_mongo_client()
            db = client['GaitDB']
            collection = db['patient_examinations']
            
            # Ambil semua tanggal pemeriksaan untuk pasien ini
            pemeriksaan_list = collection.find(
                {'patient_info.nik': nik},
                {'patient_info.tanggal_pemeriksaan': 1}
            )
            
            dates = []
            for exam in pemeriksaan_list:
                tanggal_str = exam.get('patient_info', {}).get('tanggal_pemeriksaan')
                if tanggal_str:
                    try:
                        dates.append(datetime.strptime(tanggal_str, "%Y-%m-%d").date())
                    except:
                        continue
            
            return sorted(dates, reverse=True)  # Urutkan dari terbaru
            
        except Exception as e:
            st.error(f"Error mengambil daftar pemeriksaan: {e}")
            return []

    def _get_normal_data(self):
        """Mendapatkan data normal dari database"""
        try:
            client = get_mongo_client()
            db = client['GaitDB']
            collection = db['gait_data']
            
            # Ambil data normal
            cursor = collection.find().limit(100)
            data = list(cursor)
            
            if len(data) == 0:
                return None
                
            # Normalisasi data untuk DataFrame
            df = pd.json_normalize(data)
            df.columns = df.columns.str.replace('Trial Information.', '')
            df.columns = df.columns.str.replace('Subject Parameters.', '')
            df.columns = df.columns.str.replace('Body Measurements.', '')
            df.columns = df.columns.str.replace('Norm Kinematics.', '')
            
            return df
            
        except Exception as e:
            st.error(f"Error mengambil data normal: {e}")
            return None

    def _create_joint_figure(self, data, title, color, patient_data=None):
        """Membuat figure untuk joint tertentu"""
        fig = go.Figure()
        
        # Data normal (rata-rata)
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data["mean"], 
            mode='lines',
            name=f'Rata-rata Subjek Normal',
            line=dict(color=color),
            hoverinfo='text',
            text=[f"Rata-rata Normal: {cycle}%, {val:.2f}°" for cycle, val in zip(data["%cycle"], data["mean"])]
        ))
        
        # Data pasien jika ada
        if patient_data is not None:
            fig.add_trace(go.Scatter(
                x=data["%cycle"], 
                y=patient_data, 
                mode='lines',
                name='Data Anda',
                line=dict(color='black', width=3)
            ))
        
        # Area standar error
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data["mean"] + data["std"], 
            mode='lines',
            name='Upper Bound',
            line=dict(color=color, width=0),
            showlegend=False,
            hoverinfo='skip'
        ))
        fig.add_trace(go.Scatter(
            x=data["%cycle"], 
            y=data["mean"] - data["std"], 
            mode='lines',
            name='Standard Error Area',
            line=dict(color=color, width=0),
            fill='tonexty',
            fillcolor=f'rgba({255 if color=="orange" else 0}, {165 if color=="orange" else 255}, {0 if color=="orange" else 255}, 0.2)',
            showlegend=True,
            hoverinfo='text',
            text=[f"Batas Atas: {cycle}%, {valup:.2f}°<br>Batas Bawah: {cycle}%, {vallow:.2f}°" for cycle, vallow, valup in zip(data["%cycle"], data["mean"] - data["std"], data["mean"] + data["std"])]
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="% Siklus Gait",
            yaxis_title="Sudut (Derajat)",
            template="plotly_white",
            title_x=0.5,
            hovermode="x unified",
            height=400
        )
        return fig

    def _process_kinematic_data(self, filtered_df, patient_kinematics=None):
        """Memproses data kinematik untuk visualisasi"""
        # Pelvis
        l_pelvis_angles = pd.DataFrame(filtered_df['LPelvisAngles_X'].tolist())
        r_pelvis_angles = pd.DataFrame(filtered_df['RPelvisAngles_X'].tolist())

        mean_l_pelvis = l_pelvis_angles.mean(axis=0).values
        std_l_pelvis = l_pelvis_angles.std(axis=0)/np.sqrt(l_pelvis_angles.shape[0])
        mean_r_pelvis = r_pelvis_angles.mean(axis=0).values
        std_r_pelvis = r_pelvis_angles.std(axis=0)/np.sqrt(r_pelvis_angles.shape[0])

        lpelvis = pd.DataFrame({
            "%cycle": list(range(101)),
            'mean': mean_l_pelvis,
            'std': std_l_pelvis
        })

        rpelvis = pd.DataFrame({
            "%cycle": list(range(101)),
            'mean': mean_r_pelvis,
            'std': std_r_pelvis
        })

        # Knee
        l_knee_angles = pd.DataFrame(filtered_df['LKneeAngles_X'].tolist())
        r_knee_angles = pd.DataFrame(filtered_df['RKneeAngles_X'].tolist())

        mean_l_knee = l_knee_angles.mean(axis=0).values
        std_l_knee = l_knee_angles.std(axis=0) / np.sqrt(l_knee_angles.shape[0])
        mean_r_knee = r_knee_angles.mean(axis=0).values
        std_r_knee = r_knee_angles.std(axis=0) / np.sqrt(r_knee_angles.shape[0])

        lknee = pd.DataFrame({
            "%cycle": list(range(101)),
            'mean': mean_l_knee,
            'std': std_l_knee
        })
        
        rknee = pd.DataFrame({
            "%cycle": list(range(101)),
            'mean': mean_r_knee,
            'std': std_r_knee
        })

        # Hip
        l_hip_angles = pd.DataFrame(filtered_df['LHipAngles_X'].tolist())
        r_hip_angles = pd.DataFrame(filtered_df['RHipAngles_X'].tolist())

        mean_l_hip = l_hip_angles.mean(axis=0).values
        std_l_hip = l_hip_angles.std(axis=0) / np.sqrt(l_hip_angles.shape[0])
        mean_r_hip = r_hip_angles.mean(axis=0).values
        std_r_hip = r_hip_angles.std(axis=0) / np.sqrt(r_hip_angles.shape[0])

        lhip = pd.DataFrame({
            "%cycle": list(range(101)),
            'mean': mean_l_hip,
            'std': std_l_hip
        })
        
        rhip = pd.DataFrame({
            "%cycle": list(range(101)),
            'mean': mean_r_hip,
            'std': std_r_hip
        })

        # Ankle
        l_ankle_angles = pd.DataFrame(filtered_df['LAnkleAngles_X'].tolist())
        r_ankle_angles = pd.DataFrame(filtered_df['RAnkleAngles_X'].tolist())

        mean_l_ankle = l_ankle_angles.mean(axis=0).values
        std_l_ankle = l_ankle_angles.std(axis=0) / np.sqrt(l_ankle_angles.shape[0])
        mean_r_ankle = r_ankle_angles.mean(axis=0).values
        std_r_ankle = r_ankle_angles.std(axis=0) / np.sqrt(r_ankle_angles.shape[0])

        lankle = pd.DataFrame({
            "%cycle": list(range(101)),
            'mean': mean_l_ankle,
            'std': std_l_ankle
        })

        rankle = pd.DataFrame({
            "%cycle": list(range(101)),
            'mean': mean_r_ankle,
            'std': std_r_ankle
        })

        # Data pasien jika ada
        patient_data = {}
        if patient_kinematics:
            patient_data = {
                'l_pelvis': patient_kinematics.get('LPelvisAngles_X', []),
                'r_pelvis': patient_kinematics.get('RPelvisAngles_X', []),
                'l_knee': patient_kinematics.get('LKneeAngles_X', []),
                'r_knee': patient_kinematics.get('RKneeAngles_X', []),
                'l_hip': patient_kinematics.get('LHipAngles_X', []),
                'r_hip': patient_kinematics.get('RHipAngles_X', []),
                'l_ankle': patient_kinematics.get('LAnkleAngles_X', []),
                'r_ankle': patient_kinematics.get('RAnkleAngles_X', [])
            }

        return {
            'lpelvis': lpelvis, 'rpelvis': rpelvis,
            'lknee': lknee, 'rknee': rknee,
            'lhip': lhip, 'rhip': rhip,
            'lankle': lankle, 'rankle': rankle,
            'patient_data': patient_data
        }

    def _show_dashboard_visualization(self, kinematic_data):
        """Menampilkan visualisasi dashboard"""
        # Buat visualisasi untuk setiap joint
        fig1 = self._create_joint_figure(kinematic_data['lpelvis'], "Left Pelvis", 'orange', 
                                       kinematic_data['patient_data'].get('l_pelvis'))
        fig2 = self._create_joint_figure(kinematic_data['rpelvis'], "Right Pelvis", 'darkblue', 
                                       kinematic_data['patient_data'].get('r_pelvis'))
        fig3 = self._create_joint_figure(kinematic_data['lknee'], "Left Knee", 'orange', 
                                       kinematic_data['patient_data'].get('l_knee'))
        fig4 = self._create_joint_figure(kinematic_data['rknee'], "Right Knee", 'darkblue', 
                                       kinematic_data['patient_data'].get('r_knee'))
        fig5 = self._create_joint_figure(kinematic_data['lhip'], "Left Hip", 'orange', 
                                       kinematic_data['patient_data'].get('l_hip'))
        fig6 = self._create_joint_figure(kinematic_data['rhip'], "Right Hip", 'darkblue', 
                                       kinematic_data['patient_data'].get('r_hip'))
        fig7 = self._create_joint_figure(kinematic_data['lankle'], "Left Ankle", 'orange', 
                                       kinematic_data['patient_data'].get('l_ankle'))
        fig8 = self._create_joint_figure(kinematic_data['rankle'], "Right Ankle", 'darkblue', 
                                       kinematic_data['patient_data'].get('r_ankle'))

        # Tampilkan dalam tabs
        tab1, tab2, tab3, tab4 = st.tabs(["PELVIS", "KNEE", "HIP", "ANKLE"])

        with tab1:
            st.subheader("PELVIS")
            st.write('Pelvis (dalam bahasa Indonesia: panggul) adalah struktur tulang yang berbentuk cekungan di bawah perut, di antara tulang pinggul, dan di atas paha.')
            
            # Hitung mean differences
            if kinematic_data['patient_data'].get('l_pelvis'):
                maelpelvis = np.mean(np.abs(np.array(kinematic_data['patient_data']['l_pelvis']) - kinematic_data['lpelvis']["mean"]))
                maerpelvis = np.mean(np.abs(np.array(kinematic_data['patient_data']['r_pelvis']) - kinematic_data['rpelvis']["mean"]))
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig1, use_container_width=True)
                if kinematic_data['patient_data'].get('l_pelvis'):
                    st.write(f"**Perbedaan rata-rata sudut pelvis kiri (Anda vs Normal): {maelpelvis:.2f}°**")
            with col2:
                st.plotly_chart(fig2, use_container_width=True)
                if kinematic_data['patient_data'].get('r_pelvis'):
                    st.write(f"**Perbedaan rata-rata sudut pelvis kanan (Anda vs Normal): {maerpelvis:.2f}°**")
                
        with tab2:
            st.subheader("KNEE")
            st.write('Knee (dalam bahasa Indonesia: lutut) adalah bagian tubuh manusia yang terletak di antara paha dan betis, berfungsi sebagai sendi yang menghubungkan tulang femur (paha) dengan tulang tibia (betis).')
            
            if kinematic_data['patient_data'].get('l_knee'):
                maelknee = np.mean(np.abs(np.array(kinematic_data['patient_data']['l_knee']) - kinematic_data['lknee']["mean"]))
                maerknee = np.mean(np.abs(np.array(kinematic_data['patient_data']['r_knee']) - kinematic_data['rknee']["mean"]))
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig3, use_container_width=True)
                if kinematic_data['patient_data'].get('l_knee'):
                    st.write(f"**Perbedaan rata-rata sudut lutut kiri (Anda vs Normal): {maelknee:.2f}°**")
            with col2:
                st.plotly_chart(fig4, use_container_width=True)
                if kinematic_data['patient_data'].get('r_knee'):
                    st.write(f"**Perbedaan rata-rata sudut lutut kanan (Anda vs Normal): {maerknee:.2f}°**")

        with tab3:
            st.subheader("HIP")
            st.write('Hip (dalam bahasa Indonesia: pinggul) adalah bagian tubuh yang terletak di bawah perut, menghubungkan tubuh bagian atas dengan kaki.')
            
            if kinematic_data['patient_data'].get('l_hip'):
                maelhip = np.mean(np.abs(np.array(kinematic_data['patient_data']['l_hip']) - kinematic_data['lhip']["mean"]))
                maerhip = np.mean(np.abs(np.array(kinematic_data['patient_data']['r_hip']) - kinematic_data['rhip']["mean"]))
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig5, use_container_width=True)
                if kinematic_data['patient_data'].get('l_hip'):
                    st.write(f"**Perbedaan rata-rata sudut pinggul kiri (Anda vs Normal): {maelhip:.2f}°**")
            with col2:
                st.plotly_chart(fig6, use_container_width=True)
                if kinematic_data['patient_data'].get('r_hip'):
                    st.write(f"**Perbedaan rata-rata sudut pinggul kanan (Anda vs Normal): {maerhip:.2f}°**")

        with tab4:
            st.subheader("ANKLE")
            st.write('Ankle (dalam bahasa Indonesia: pergelangan kaki) adalah sendi yang terletak di antara kaki bagian bawah (tulang tibia dan fibula) dan bagian atas kaki (tulang talus).')
            
            if kinematic_data['patient_data'].get('l_ankle'):
                maelankle = np.mean(np.abs(np.array(kinematic_data['patient_data']['l_ankle']) - kinematic_data['lankle']["mean"]))
                maerankle = np.mean(np.abs(np.array(kinematic_data['patient_data']['r_ankle']) - kinematic_data['rankle']["mean"]))
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig7, use_container_width=True)
                if kinematic_data['patient_data'].get('l_ankle'):
                    st.write(f"**Perbedaan rata-rata sudut pergelangan kaki kiri (Anda vs Normal): {maelankle:.2f}°**")
            with col2:
                st.plotly_chart(fig8, use_container_width=True)
                if kinematic_data['patient_data'].get('r_ankle'):
                    st.write(f"**Perbedaan rata-rata sudut pergelangan kaki kanan (Anda vs Normal): {maerankle:.2f}°**")

    def _register_page(self):
        st.markdown("### 🧾 Form Pendaftaran Pasien")
        with st.form("register_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nik = st.text_input("NIK", max_chars=20, key="reg_nik")
                nama = st.text_input("Nama Lengkap", key="reg_nama")
                password = st.text_input("Password", type="password", key="reg_password")
                ttl = st.date_input("Tanggal Lahir", min_value=date(1900, 1, 1), max_value=date(2100, 12, 31), key="reg_ttl")
            with col2:
                jk = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"], key="reg_jk")
                tb = st.number_input("Tinggi Badan (cm)", min_value=0, max_value=250, step=1, key="reg_tb")
                bb = st.number_input("Berat Badan (kg)", min_value=0, max_value=300, step=1, key="reg_bb")
            daftar = st.form_submit_button("Daftar", use_container_width=True)

        if daftar:
            if nik and nama and password:
                if self._save_registration_to_db({
                    "NIK": nik, "Nama Lengkap": nama, "Password": password,
                    "TTL": ttl, "Jenis Kelamin": jk, "TB": tb, "BB": bb
                }):
                    st.success("✅ Pendaftaran berhasil! Silakan login.")
                    st.session_state.show_register = False
                    st.rerun()
            else:
                st.warning("Mohon isi semua kolom wajib.")

        if st.button("⬅ Kembali ke Login", key="back_login"):
            st.session_state.show_register = False
            st.rerun()

    def _dashboard_page(self):
        nik = st.session_state.get("pasien_nik")
        profil = next((p for p in st.session_state["pasien_list"] if p["NIK"] == nik), None)
        
        st.markdown("<h1 style='text-align: center; color: #560000;'>Dashboard Pemeriksaan GAIT</h1>", unsafe_allow_html=True)
        
        # Dapatkan semua tanggal pemeriksaan untuk pasien ini
        available_dates = self._get_all_pemeriksaan_dates(nik)
        
        if not available_dates:
            st.warning("🔍 Silahkan periksa dulu ke dokter agar dashboard pemeriksaan GAIT anda muncul")
            return
        
        # Pilih tanggal pemeriksaan
        selected_date = st.selectbox(
            "Pilih Tanggal Pemeriksaan",
            options=available_dates,
            format_func=lambda x: x.strftime("%d %B %Y")
        )
        
        # Dapatkan data pemeriksaan untuk tanggal yang dipilih
        pemeriksaan = self._get_pemeriksaan_data(nik, selected_date)
        
        if not pemeriksaan:
            st.warning(f"❌ Tidak ada data pemeriksaan untuk tanggal {selected_date.strftime('%d %B %Y')}")
            return
        
        # Dapatkan data normal
        normal_data = self._get_normal_data()
        if normal_data is None:
            st.error("❌ Data normal belum tersedia. Silakan hubungi administrator.")
            return
        
        # Tampilkan informasi pemeriksaan
        patient_info = pemeriksaan.get('patient_info', {})
        st.markdown(f"### Hasil Pemeriksaan - {selected_date.strftime('%d %B %Y')}")
        # st.markdown(f"**Diagnosa:** {patient_info.get('diagnosa', 'Tidak tersedia')}")
        
        # Proses data untuk visualisasi
        with st.spinner("Memuat visualisasi data..."):
            kinematic_data = self._process_kinematic_data(
                normal_data, 
                pemeriksaan.get('gait_data', {}).get('Norm Kinematics', {})
            )
            
            # Tampilkan visualisasi
            self._show_dashboard_visualization(kinematic_data)

    def _profile_page(self):
        nik = st.session_state.get("pasien_nik")
        profil = next((p for p in st.session_state["pasien_list"] if p["NIK"] == nik), None)
        
        st.markdown("<h1 style='text-align: center; color: #560000;'>Profil Pasien</h1>", unsafe_allow_html=True)
        
        if profil:
            st.subheader("Data Profil")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**NIK:** {profil['NIK']}")
                st.markdown(f"**Nama Lengkap:** {profil['Nama Lengkap']}")
                st.markdown(f"**Tanggal Lahir:** {profil['TTL']}")
                
            with col2:
                st.markdown(f"**Jenis Kelamin:** {profil['Jenis Kelamin']}")
                st.markdown(f"**Tinggi Badan:** {profil['TB']} cm")
                st.markdown(f"**Berat Badan:** {profil['BB']} kg")
                st.markdown(f"**Tanggal Pendaftaran:** {profil['Tanggal Dibuat']}")
                
        else:
            st.warning("Data profil tidak ditemukan")

    def run(self):
        if not st.session_state.get("pasien_logged_in", False):
            # Tampilkan halaman Register jika tombol Register diklik
            if st.session_state.get("show_register", False):
                self._register_page()
                return

            # Kalau belum login, tampilkan form login
            nik, password, submit = login_form_pasien()
            if submit:
                auth = st.session_state["pasien_auth"]
                if nik in auth and auth[nik] == password:
                    st.session_state.pasien_logged_in = True
                    st.session_state.pasien_nik = nik
                    st.success("Login berhasil!")
                    st.rerun()
                else:
                    st.error("NIK atau password salah!")
            return

        # ========== DASHBOARD PASIEN ==========
        # Sidebar menu dengan styling yang sama seperti terapis
        st.sidebar.markdown("""
        <style>
            section[data-testid="stSidebar"] {
                background-color: #560000;
            }
            .sidebar-title {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 10px 20px;
            }
            section[data-testid="stSidebar"] div[class*="stRadio"] label {
                color: white !important;
            }
            section[data-testid="stSidebar"] div[class*="stRadio"] div[role="radiogroup"] {
                color: white !important;
            }
            section[data-testid="stSidebar"] * {
                color: white !important;
            }
            section[data-testid="stSidebar"] div[class*="stRadio"] div[data-testid="stMarkdownContainer"] p {
                color: white !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.sidebar.markdown("<p class='sidebar-title'>Menu Pasien</p>", unsafe_allow_html=True)
        menu = st.sidebar.radio("Navigasi", ["Dashboard", "Profile", "Logout"])

        if menu == "Dashboard":
            self._dashboard_page()
        elif menu == "Profile":
            self._profile_page()
        else:  # Logout
            st.session_state.pasien_logged_in = False
            st.session_state.show_register = False
            st.session_state.role = None
            st.rerun()