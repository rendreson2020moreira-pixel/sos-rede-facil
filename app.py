from flask import Flask, render_template, request, redirect, session
import os
import socket
import platform
import time
import sqlite3
import concurrent.futures
import requests

app = Flask(__name__)
app.secret_key = 'sosrede'

# -------------------- BANCO DE DADOS --------------------

def conectar():
    return sqlite3.connect("usuarios.db")

def criar_banco():
    if not os.path.exists("usuarios.db"):
        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT,
                senha TEXT
            )
        """)
        conn.commit()
        conn.close()

criar_banco()

# -------------------- LOGIN --------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE email=? AND senha=?", (email, senha))
        user = cur.fetchone()
        conn.close()

        if user:
            session['usuario'] = user[1]
            return redirect('/painel')
        else:
            return render_template('login.html', erro="Login inválido")

    return render_template('login.html')

# -------------------- CADASTRO --------------------

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')

        conn = conectar()
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                    (nome, email, senha))
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('cadastro.html')

# -------------------- PAINEL --------------------

@app.route('/painel')
def painel():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('index.html', usuario=session['usuario'])

# -------------------- LOGOUT --------------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -------------------- PING --------------------

@app.route('/ping', methods=['GET', 'POST'])
def ping():
    resultado = ""

    if request.method == 'POST':
        host = request.form.get('host')

        if platform.system() == "Windows":
            comando = f"ping -n 4 {host}"
        else:
            comando = f"ping -c 4 {host}"

        resultado = os.popen(comando).read()

    return render_template("ping.html", resultado=resultado)

# -------------------- IP PROFISSIONAL --------------------

@app.route('/ip')
def ip():
    try:
        dados = requests.get("https://ipinfo.io/json").json()
        ip_publico = dados.get("ip", "Desconhecido")
        cidade = dados.get("city", "Desconhecida")
        regiao = dados.get("region", "")
        pais = dados.get("country", "")
        provedor = dados.get("org", "Desconhecido")
    except:
        ip_publico = cidade = regiao = pais = provedor = "Erro"

    return render_template("ip.html",
                           ip=ip_publico,
                           cidade=cidade,
                           regiao=regiao,
                           pais=pais,
                           provedor=provedor)

# -------------------- VELOCIDADE --------------------

@app.route('/velocidade')
def velocidade():
    inicio = time.time()

    if platform.system() == "Windows":
        os.system("ping -n 1 google.com > nul")
    else:
        os.system("ping -c 1 google.com > /dev/null")

    fim = time.time()

    tempo_ms = round((fim - inicio) * 1000, 2)

    return render_template("velocidade.html", tempo=tempo_ms)

# -------------------- SCANNER --------------------

@app.route('/scanner', methods=['GET'])
def scanner():
    base = "192.168.0."
    dispositivos = []

    def testar(ip):
        if platform.system() == "Windows":
            resposta = os.system(f"ping -n 1 -w 80 {ip} > nul")
        else:
            resposta = os.system(f"ping -c 1 -W 1 {ip} > /dev/null")

        if resposta == 0:
            return ip
        return None

    ips = [base + str(i) for i in range(1, 50)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        resultados = executor.map(testar, ips)

    for r in resultados:
        if r:
            dispositivos.append(r)

    return render_template("scanner.html", dispositivos=dispositivos)

# -------------------- TRACEROUTE --------------------

@app.route('/traceroute', methods=['GET', 'POST'])
def traceroute():
    resultado = ""

    if request.method == 'POST':
        destino = request.form.get('destino')

        if platform.system() == "Windows":
            comando = f"tracert {destino}"
        else:
            comando = f"traceroute {destino}"

        resultado = os.popen(comando).read()

    return render_template("traceroute.html", resultado=resultado)



