from flask import Flask, render_template, request, redirect, session
import os
import socket
import time
import sqlite3
import concurrent.futures
import requests
import subprocess
import platform

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

        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            comando = ["ping", param, "4", host]
            resultado = subprocess.check_output(comando, universal_newlines=True, timeout=15)
        except:
            resultado = "Erro ao executar ping."

    return render_template("ping.html", resultado=resultado)

# -------------------- IP PROFISSIONAL --------------------

@app.route('/ip')
def ip():
    try:
        dados = requests.get("https://ipinfo.io/json", timeout=5).json()
    except:
        dados = {}

    return render_template("ip.html", dados=dados)

# -------------------- VELOCIDADE --------------------

@app.route('/velocidade', methods=['GET', 'POST'])
def velocidade():
    tempo = None

    if request.method == 'POST':
        inicio = time.time()

        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            subprocess.call(["ping", param, "1", "google.com"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            timeout=10)
        except:
            pass

        fim = time.time()
        tempo = round((fim - inicio) * 1000, 2)

    return render_template("velocidade.html", tempo=tempo)

# -------------------- SCANNER --------------------

@app.route('/scanner', methods=['GET', 'POST'])
def scanner():
    dispositivos = []

    if request.method == 'POST':
        base = "192.168.0."

        def testar(ip):
            try:
                param = "-n" if platform.system().lower() == "windows" else "-c"
                resposta = subprocess.call(
                    ["ping", param, "1", ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2
                )
                if resposta == 0:
                    return ip
            except:
                pass
            return None

        ips = [base + str(i) for i in range(1, 50)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
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

        try:
            comando = ["tracert", destino] if platform.system().lower() == "windows" else ["traceroute", destino]
            resultado = subprocess.check_output(comando, universal_newlines=True, timeout=30)
        except:
            resultado = "Erro ao executar traceroute."

    return render_template("traceroute.html", resultado=resultado)

# -------------------- START --------------------

if __name__ == '__main__':
    app.run()
