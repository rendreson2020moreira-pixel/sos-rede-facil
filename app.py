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

# -------------------- PING WEB --------------------

@app.route('/ping', methods=['GET','POST'])
def ping():
    resultado = ""

    if request.method == 'POST':
        host = request.form.get("host", "google.com")

        try:
            inicio = time.time()
            requests.get(f"https://{host}", timeout=5)
            fim = time.time()

            tempo = round((fim - inicio) * 1000, 2)
            resultado = f"🟢 Host online - Tempo: {tempo} ms"

        except:
            resultado = "🔴 Host offline ou inacessível"

    return render_template("ping.html", resultado=resultado)

# -------------------- IP PÚBLICO --------------------

@app.route('/ip')
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

    except:
        return "Erro ao obter IP"

# -------------------- VELOCIDADE --------------------

@app.route('/velocidade', methods=['GET','POST'])
def velocidade():
    tempo = None

    if request.method == 'POST':
        try:
            inicio = time.time()
            requests.get("https://google.com", timeout=5)
            fim = time.time()

            tempo = round((fim - inicio) * 1000, 2)
        except:
            tempo = "Erro"

    return render_template("velocidade.html", tempo=tempo)

# -------------------- SCANNER SIMULADO --------------------

@app.route('/scanner', methods=['GET','POST'])
def scanner():
    resultado = ""

    if request.method == 'POST':
        host = request.form.get("host")

        try:
            requests.get(f"https://{host}", timeout=5)
            resultado = f"🟢 {host} está ONLINE"
        except:
            resultado = f"🔴 {host} está OFFLINE"

    return render_template("scanner.html", resultado=resultado)

# -------------------- TRACEROUTE SIMULADO --------------------

@app.route('/traceroute')
def traceroute():
    rota = [
        "Dispositivo Local",
        "Gateway ISP",
        "Backbone Cloud",
        "Firewall Global",
        "Servidor Destino"
    ]

    return render_template("traceroute.html", rota=rota)

# -------------------- START --------------------

if __name__ == '__main__':
    app.run(debug=True)