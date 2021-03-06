from flask import Flask, render_template, request, redirect, url_for, make_response, session
import sqlite3
from datetime import date

today = date.today()

conn = sqlite3.connect('bankDB.db', check_same_thread=False)
c = conn.cursor()

app = Flask(__name__)
app.secret_key = 'summaSecret'


def updatePassbook(email, date, details, amt, fbal):
    c.execute(''' INSERT INTO passbook(email, date, details, amount, balance ) VALUES(?,?,?,?,?)''', (email, date, details, amt, fbal))
    conn.commit()


@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        cl = conn.cursor()
        email = str(request.form['email'])
        password = str(request.form['password'])
        cl.execute('SELECT COUNT(*) FROM user where email="%s" AND password="%s"' % (email, password))
        s = cl.fetchone()
        if str(s[0]) == "1":
            resp = redirect(url_for('home'))
            resp.set_cookie('userEmail', email)
            session['userEmail'] = email
            return resp
        else:
            return render_template('login.html', invalid="--> Invalid Credentials!")
    else:
        if session.get('userEmail') is not None:
            return redirect(url_for("home"))
        else:
            return render_template("login.html")


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        name = str(request.form['name'])
        email = str(request.form['email'])
        password = str(request.form['password'])

        c.execute('SELECT COUNT(*) FROM user where email="%s"' % email)
        sz = c.fetchone()
        if str(sz[0]) == "1":
            return "User Already Exists!"
        else:
            c.execute(''' INSERT INTO user(username, email, password, balance ) VALUES(?,?,?,?)''', (name, email, password, "500"))
            updatePassbook(email, date.today(), "Initial Deposit", "+ 500", "500")
            conn.commit()
            return redirect(url_for("login"))
    else:
        return render_template("register.html")


@app.route('/home', methods=['POST', 'GET'])
def home():
    return render_template("index.html")


@app.route('/deposit', methods=['POST', 'GET'])
def deposit():
    if request.method == 'POST':
        if session.get('userEmail') is not None:
            amount = str(request.form["amount"])
            if int(amount) > 0:
                email = session.get('userEmail')
                c.execute('SELECT balance FROM user WHERE email = "%s"' % email)
                t = c.fetchone()
                bal = str(int(t[0]) + int(amount))
                c.execute('UPDATE user SET balance = "%s" WHERE email = "%s";' % (bal, email))
                conn.commit()
                updatePassbook(email, date.today(), "Self Deposit", "+ "+amount, bal)
                return render_template("deposit.html", status="Amount Deposited Successfully!")
            else:
                return render_template("deposit.html", status="Deposit Amount Must be Greater than ZERO")
        else:
            return redirect(url_for("login"))
    else:
        return render_template("deposit.html", status="")


@app.route('/mybalance', methods=['POST', 'GET'])
def balance():
    if session.get('userEmail') is not None:
        email = str(session.get('userEmail'))
        c.execute('SELECT balance FROM user WHERE email = "%s"' % email)
        balan = c.fetchone()
        return render_template("balance.html", bal=str(balan[0]))
    else:
        return redirect(url_for('login'))


@app.route('/transfer', methods=['POST', 'GET'])
def transfer():
    if request.method == 'POST':
        if session.get('userEmail') is not None:
            email = str(session.get('userEmail'))
            c.execute('SELECT balance FROM user WHERE email = "%s"' % email)
            t = c.fetchone()
            currentBalance = int(t[0])
            transferAmount = int(request.form["transferAmt"])
            transferEmail = str(request.form["transferEmail"])

            c.execute('SELECT COUNT(*) from user WHERE email="%s"' % transferEmail)
            v = c.fetchone()

            if str(v[0]) == "1":
                if currentBalance >= transferAmount:
                    c.execute('SELECT balance FROM user WHERE email = "%s"' % transferEmail)
                    t1 = c.fetchone()
                    receiverBalance = int(t1[0])
                    senderFinalBalance = str(currentBalance - transferAmount)
                    receiverFinalBalance = str(receiverBalance + transferAmount)
                    c.execute('UPDATE user SET balance = "%s" WHERE email = "%s";' % (senderFinalBalance, email))
                    c.execute('UPDATE user SET balance = "%s" WHERE email = "%s";' % (receiverFinalBalance, transferEmail))
                    updatePassbook(email, date.today(), "Transferred to "+transferEmail, "- " + str(transferAmount), senderFinalBalance)
                    updatePassbook(transferEmail, date.today(), "Received From "+email, "+ " + str(transferAmount), receiverFinalBalance)
                    conn.commit()
                    return render_template("transfer.html", status="Transaction Successfull!")
                else:
                    statu = "Insufficient Balance! You have only %s" % currentBalance
                    return render_template("transfer.html", status=statu)
            else:
                return render_template("transfer.html", status="Transfer Email ID Invalid!")
        else:
                return redirect(url_for("login"))

    else:
        if session.get('userEmail') is None:
            return redirect(url_for("login"))
        else:
            return render_template("transfer.html", status="")


@app.route('/passbook')
def passbook():
    if session.get('userEmail') is not None:
        usermail = session.get('userEmail')
        c.execute('SELECT date, details, amount, balance FROM passbook WHERE email="%s"' % usermail)
        items = c.fetchall()
        return render_template("passbook.html", items=items)
    else:
        return redirect(url_for("login"))


@app.route('/logout')
def logout():
    re = redirect(url_for("login"))
    re.set_cookie('userEmail', "0")
    session.pop('userEmail', None)
    return re


@app.route('/createDB')
def createDB():
    # c.execute('''CREATE TABLE user (username VARCHAR(30),
    #                 email VARCHAR(50) PRIMARY KEY,
    #                 password VARCHAR(30),
    #                 balance VARCHAR(100))''')

    c.execute('CREATE TABLE passbook(email VARCHAR(50), date VARCHAR(50), details VARCHAR(100), amount VARCHAR(50), balance VARCHAR(50))')
    conn.commit()
    return "Database Created Successfully!"


@app.route('/showTables')
def showTables():
    c.execute('''SELECT * FROM user''')
    rows = c.fetchall()
    for row in rows:
        return str(rows)


if __name__ == '__main__':
    app.run(debug=True)

