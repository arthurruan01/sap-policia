import streamlit as st
import psycopg2
from PIL import Image
import os

# Configuração da página Web
st.set_page_config(page_title="S.A.P. SYSTEM - Polícia", layout="wide", initial_sidebar_state="expanded")

# CSS Personalizado (Tema Dark / Preto e Azul)
st.markdown("""
    <style>
    .main { background-color: #0F0F12; color: #FFFFFF; }
    .stButton>button { background-color: #1E88E5; color: white; border-radius: 8px; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #1A1C23; color: white; border: 1px solid #1E88E5; }
    </style>
""", unsafe_allow_html=True)

# ⚠️ ALTERE PARA A SUA SENHA LOCAL OU URI DA NUVEM (Neon/Supabase)
DB_URI = "postgresql://postgres:sua_senha_aqui@localhost:5432/policia_db"

def get_db_connection():
    try:
        return psycopg2.connect(DB_URI)
    except Exception as e:
        st.error(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

# Gerenciamento de Sessão de Login
if "user" not in st.session_state:
    st.session_state["user"] = None

# ==================== TELA DE LOGIN / CADASTRO ====================
if st.session_state["user"] is None:
    st.title("🛡️ S.A.P. - Sistema de Arquivos Policiais")
    
    tab1, tab2 = st.tabs(["Entrar no Sistema", "Cadastrar Novo Policial"])
    
    with tab1:
        email = st.text_input("E-mail Corporativo")
        senha = st.text_input("Senha", type="password")
        if st.button("Acessar Conta"):
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute("SELECT id, nome, email, cargo, status FROM usuarios WHERE email=%s AND senha=%s", (email, senha))
                user = cur.fetchone()
                cur.close()
                conn.close()
                
                if user:
                    if user[4] == 'Banido':
                        st.error("Sua conta foi BANIDA pelo Administrador.")
                    else:
                        st.session_state["user"] = {"id": user[0], "nome": user[1], "email": user[2], "cargo": user[3]}
                        st.rerun()
                else:
                    st.error("Credenciais inválidas!")

    with tab2:
        novo_nome = st.text_input("Nome Completo")
        novo_email = st.text_input("E-mail Policial")
        nova_senha = st.text_input("Criar Senha", type="password")
        if st.button("Finalizar Cadastro"):
            if novo_nome and novo_email and nova_senha:
                conn = get_db_connection()
                if conn:
                    try:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO usuarios (nome, email, senha, cargo) VALUES (%s, %s, %s, 'POLICIAL')", (novo_nome, novo_email, nova_senha))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("Policial cadastrado com sucesso! Faça login na aba ao lado.")
                    except Exception:
                        st.error("E-mail já cadastrado!")

# ==================== PAINEL DO SISTEMA ====================
else:
    st.sidebar.title("S.A.P. SYSTEM")
    st.sidebar.write(f"**Policial:** {st.session_state['user']['nome']}")
    st.sidebar.write(f"**Cargo:** {st.session_state['user']['cargo']}")
    
    if st.sidebar.button("Sair / Logout"):
        st.session_state["user"] = None
        st.rerun()

    menu = ["Pesquisar Suspeitos", "Cadastrar Suspeito"]
    if st.session_state["user"]["cargo"] == "ADMIN":
        menu.append("Painel ADM")
        
    opcao = st.sidebar.selectbox("Navegação", menu)

    # ---------- ABA: PESQUISAR SUSPEITOS ----------
    if opcao == "Pesquisar Suspeitos":
        st.subheader("🔍 Pesquisa de Arquivos Policiais")
        busca = st.text_input("Buscar por Nome, CPF ou Vulgo")
        
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            termo = f"%{busca}%"
            cur.execute("SELECT id, nome, vulgo, status, endereco, latitude, longitude FROM suspeitos WHERE nome ILIKE %s OR cpf ILIKE %s OR vulgo ILIKE %s", (termo, termo, termo))
            suspeitos = cur.fetchall()
            cur.close()
            conn.close()
            
            for s in suspeitos:
                with st.expander(f"📌 {s[1]} (Vulgo: {s[2]}) - Status: {s[3]}"):
                    st.write(f"**Endereço:** {s[4]}")
                    if s[5] and s[6]:
                        st.markdown(f"[📍 Ver localização no Google Maps](https://www.google.com/maps?q={s[5]},{s[6]})")

    # ---------- ABA: CADASTRAR SUSPEITO ----------
    elif opcao == "Cadastrar Suspeito":
        st.subheader("📝 Novo Cadastro de Suspeito")
        c_nome = st.text_input("Nome Completo do Suspeito")
        c_cpf = st.text_input("CPF")
        c_vulgo = st.text_input("Vulgo / Alcunha")
        c_status = st.selectbox("Status", ["Procurado", "Com Passagem", "Livre / Investigado"])
        c_end = st.text_area("Endereço Completo")
        c_lat = st.text_input("Latitude (opcional)")
        c_lng = st.text_input("Longitude (opcional)")
        
        if st.button("Salvar Ficha Policial"):
            if c_nome:
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO suspeitos (nome, cpf, vulgo, status, endereco, latitude, longitude, cadastrado_por)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (c_nome, c_cpf, c_vulgo, c_status, c_end, c_lat, c_lng, st.session_state["user"]["id"]))
                    conn.commit()
                    cur.close()
                    conn.close()
                    st.success("Suspeito cadastrado com sucesso no banco em nuvem!")
