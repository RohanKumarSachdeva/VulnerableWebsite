import os
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import re

app = Flask(__name__)
app.secret_key = 's3cr3t'


connection = mysql.connector.connect(
    host='db',
    user='root',
    password='root',
    port='3306',
    database='VulnerableWebsite'
)


@app.route("/")
def index():
    return render_template('index.html', msg='')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = connection.cursor()

        query = 'SELECT * FROM accounts WHERE username=\'' + username + '\' AND password=\'' + password + ' \''
        cursor.execute(query)
        account = cursor.fetchone()

        if account:
            # Create session data
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            # Redirect to home page
            return redirect(url_for('home'))
        else:
            # Account doesn't exist or username/password incorrect
            msg = 'Incorrect username/password!'

    return render_template('index.html', msg=msg)


@app.route('/logout/')
def logout():
    # Remove session data to logout the user
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)

    return redirect(url_for('login'))


@app.route('/register/', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        # Validation checks on registration entries
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Insert new account into accounts table
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'

    return render_template('register.html', msg=msg)


@app.route('/home/')
def home():
    # Check if user is logged in
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    # Redirect to login page if user not logged in
    return redirect(url_for('login'))


@app.route('/profile/')
def profile():
    # If user is logged in
    if 'loggedin' in session:
        cursor = connection.cursor()
        if session["username"] == "admin":
            cursor.execute('SELECT * FROM accounts')
        else:
            cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchall()

        return render_template('profile.html', account=account)
    # Redirect to login page if user not logged in
    return redirect(url_for('login'))


@app.route('/discussion/', methods=['GET', 'POST'])
def discussion():
    if 'loggedin' in session:
        msg = ''
        cursor = connection.cursor()
        if request.method == 'POST' and 'discussion' in request.form and len(request.form['discussion']) == 0:
            msg = 'Discussion cannot be empty!'

        elif request.method == 'POST' and 'discussion' in request.form:
            print("Hello")
            comment = request.form['discussion']
            user_id = session["id"]
            user_name = session["username"]
            # Insert new comment into discussions table
            cursor.execute('INSERT INTO discussions VALUES (NULL, %s, %s, %s)', (user_id, user_name, comment,))
            connection.commit()
            msg = 'Discussion posted successfully!'
        # Display all comments
        cursor.execute('SELECT * FROM discussions')
        data = cursor.fetchall()
        return render_template('discussion.html', data=data, msg=msg)
    # Redirect to login page if user not logged in
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
