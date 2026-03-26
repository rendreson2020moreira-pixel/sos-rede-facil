```python
from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import requests
import time
import re
import subprocess
import platform
import socket
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# 🔐 SECRET KEY SEGURA
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))


# -------------------- BANCO --------------------

def conectar():
    return sqlite3.connect("usuarios.db")


def criar_banco():
    conn = conectar()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT UNIQUE,
            senha TEXT
        )
    """)

    conn.commit()
    conn.close()


criar_banco()


# -------------------- SEGURANÇA --------------------

def login_obrigatorio(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


def host_valido(host):
    return re.match(r"^[a-zA-Z0-9.-]+$", host)


# -------------------- FUNÇÕES REAIS --------------------

def ping_real(host):
    try:
        sistema = platform.system().lower()

        if sistema == "windows":
            comando = ["ping", "-n", "1", host]
        else:
            comando = ["ping", "-c", "1", host]

        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True
        )

        return resultado.stdout

    except Exception as e:
        print(e)
        return "Erro ao executar ping"


def traceroute_real(host):
    try:
        sistema = platform.system().lower()

        if sistema == "windows":
            comando = ["tracert", host]
        else:
            comando = ["traceroute", host]

        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True
        )

        return resultado.stdout

    except Exception as e:
        print(e)
        return "Erro ao executar traceroute"


def scan_portas(host, portas):
    abertas = []

    for porta in portas:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            resultado = sock.connect_ex((host, porta))

            if resultado == 0:
                abertas.append(porta)

            sock.close()
        except:
            pass

    return abertas


# -------------------- LOGIN --------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[3], senha):
            session['usuario'] = user[1]
            return redirect('/painel')

        return render_template("login.html", erro="Login inválido")

    return render_template("login.html")


# -------------------- CADASTRO --------------------

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar = request.form['confirmar_senha']

        if senha != confirmar:
            return render_template("cadastro.html", erro="As senhas não coincidem")

        senha_hash = generate_password_hash(senha)

        try:
            conn = conectar()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO usuarios (nome,email,senha) VALUES (?,?,?)",
                (nome, email, senha_hash)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(e)
            return render_template("cadastro.html", erro="E-mail já cadastrado")

        return redirect('/')

    return render_template("cadastro.html")


# -------------------- PAINEL --------------------

@app.route('/painel')
@login_obrigatorio
def painel():
    return render_template("index.html", usuario=session['usuario'])


# -------------------- LOGOUT --------------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# -------------------- PING REAL --------------------

@app.route('/ping', methods=['GET', 'POST'])
@login_obrigatorio
def ping():
    resultado = ""

    if request.method == 'POST':
        host = request.form.get("host", "")

        if not host_valido(host):
            return render_template("ping.html", resultado="Host inválido")

        resultado = ping_real(host)

    return render_template("ping.html", resultado=resultado)


# -------------------- TRACEROUTE REAL --------------------

@app.route('/traceroute', methods=['GET', 'POST'])
@login_obrigatorio
def traceroute():
    resultado = ""

    if request.method == 'POST':
        host = request.form.get("host", "")

        if not host_valido(host):
            return render_template("traceroute.html", resultado="Host inválido")

        resultado = traceroute_real(host)

    return render_template("traceroute.html", resultado=resultado)


# -------------------- SCANNER DE PORTAS --------------------

@app.route('/scanner', methods=['GET', 'POST'])
@login_obrigatorio
def scanner():
    resultado = ""

    if request.method == 'POST':
        host = request.form.get("host", "")

        if not host_valido(host):
            return render_template("scanner.html", resultado="Host inválido")

        portas_comuns = [21, 22, 23, 25, 53, 80, 110, 139, 143, 443, 445, 3389]

        abertas = scan_portas(host, portas_comuns)

        if abertas:
            resultado = "🟢 Portas abertas: " + ", ".join(map(str, abertas))
        else:
            resultado = "🔴 Nenhuma porta comum aberta"

    return render_template("scanner.html", resultado=resultado)


# -------------------- IP PÚBLICO --------------------

@app.route('/ip')
@login_obrigatorio
def ip():
    try:
        dados = requests.get("https://ipinfo.io/json", timeout=5).json()

        return render_template(
            "ip.html",
            ip=dados.get("ip"),
            cidade=dados.get("city"),
            regiao=dados.get("region"),
            pais=dados.get("country"),
            provedor=dados.get("org")
        )

    except Exception as e:
        print(e)
        return "Erro ao obter IP"


# -------------------- VELOCIDADE --------------------

@app.route('/velocidade', methods=['GET', 'POST'])
@login_obrigatorio
def velocidade():
    tempo = None

    if request.method == 'POST':
        try:
            tempos = []

            for _ in range(3):
                inicio = time.time()
                requests.get("https://google.com", timeout=5)
                fim = time.time()
                tempos.append((fim - inicio) * 1000)

            tempo = round(sum(tempos) / len(tempos), 2)

        except Exception as e:
            print(e)
            tempo = "Erro"

    return render_template("velocidade.html", tempo=tempo)


# -------------------- START --------------------

if __name__ == '__main__':
    app.run(debug=True)
```
