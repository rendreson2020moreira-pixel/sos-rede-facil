from flask import Flask, render_template, request, redirect, session
import os
import socket
import platform
import time
import sqlite3
import concurrent.futures

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

@app.route('/ping')
def ping():
    resultado = os.popen("ping google.com -n 2").read()
    return f"<pre>{resultado}</pre><br><a href='/painel'>Voltar</a>"

# -------------------- IP --------------------

@app.route('/ip')
def ip():
    hostname = socket.gethostname()
    ip_local = socket.gethostbyname(hostname)
    return f"<h3>Hostname:</h3> {hostname}<br><h3>IP Local:</h3> {ip_local}<br><br><a href='/painel'>Voltar</a>"

# -------------------- VELOCIDADE --------------------

@app.route('/velocidade')
def velocidade():
    inicio = time.time()
    resposta = os.system("ping google.com -n 1 > nul")
    fim = time.time()

    tempo_ms = round((fim - inicio) * 1000, 2)

    if resposta == 0:
        status = "🟢 Conectado à Internet"
    else:
        status = "🔴 Sem Conexão"

    return render_template("velocidade.html", status=status, tempo=tempo_ms)

# -------------------- SCANNER --------------------

@app.route('/scanner')
def scanner():
    base = "192.168.0."
    dispositivos = []

    def testar_ip(ip):
        resposta = os.system(f"ping -n 1 -w 50 {ip} > nul")
        if resposta == 0:
            return ip
        return None

    ips = [base + str(i) for i in range(1, 50)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        resultados = executor.map(testar_ip, ips)

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
        if destino:
            if platform.system() == "Windows":
                comando = f"tracert {destino}"
            else:
                comando = f"traceroute {destino}"

            resultado = os.popen(comando).read()

    return render_template("traceroute.html", resultado=resultado)

# -------------------- START --------------------

if __name__ == '__main__':
    app.run()