from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import requests
import time

app = Flask(__name__)
app.secret_key = 'sosrede'

# -------------------- BANCO --------------------

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

@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE email=? AND senha=?", (email,senha))
        user = cur.fetchone()
        conn.close()

        if user:
            session['usuario'] = user[1]
            return redirect('/painel')

        return render_template("login.html", erro="Login inválido")

    return render_template("login.html")

# -------------------- CADASTRO --------------------

@app.route('/cadastro', methods=['GET','POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        conn = conectar()
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (nome,email,senha) VALUES (?,?,?)",
                    (nome,email,senha))
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template("cadastro.html")

# -------------------- PAINEL --------------------

@app.route('/painel')
def painel():
    if 'usuario' not in session:
        return redirect('/')
    return render_template("index.html", usuario=session['usuario'])

# -------------------- LOGOUT --------------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# -------------------- PING (WEB) --------------------

@app.route('/ping')
def ping():
    try:
        inicio = time.time()
        requests.get("https://google.com", timeout=5)
        fim = time.time()
        tempo = round((fim - inicio)*1000,2)

        resultado = f"🟢 Conectado - Tempo: {tempo} ms"
    except:
        resultado = "🔴 Sem conexão com a internet"

    return render_template("ping.html", resultado=resultado)

# -------------------- VELOCIDADE --------------------

@app.route('/velocidade', methods=['GET', 'POST'])
def velocidade():
    tempo_ms = None

    if request.method == 'POST':
        inicio = time.time()
        try:
            param = "-n" if platform.system().lower() == "windows" else "-c"
            subprocess.call(["ping", param, "1", "google.com"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
        except:
            pass

        fim = time.time()
        tempo_ms = round((fim - inicio) * 1000, 2)

    return render_template("velocidade.html", tempo=tempo_ms)


# -------------------- SCANNER --------------------

@app.route('/scanner', methods=['GET', 'POST'])
def scanner():
    dispositivos = []

    if request.method == 'POST':
        base = "192.168.0."

        def testar(ip):
            try:
                param = "-n" if platform.system().lower() == "windows" else "-c"
                retorno = subprocess.call(["ping", param, "1", ip],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
                if retorno == 0:
                    return ip
            except:
                return None

        ips = [base + str(i) for i in range(1, 50)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            resultados = executor.map(testar, ips)

        for r in resultados:
            if r:
                dispositivos.append(r)

    return render_template("scanner.html", dispositivos=dispositivos)

# -------------------- TRACEROUTE (WEB SIMULADO) --------------------

@app.route('/traceroute')
def traceroute():
    rota = [
        "Servidor Local",
        "Gateway Cloud",
        "Firewall Global",
        "Google Backbone",
        "Destino Final"
    ]

    return render_template("traceroute.html", rota=rota)

# -------------------- START --------------------

if __name__ == '__main__':
    app.run(debug=True)