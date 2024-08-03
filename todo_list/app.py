from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime


app = Flask(__name__)

app.secret_key = 'your_secret_key'

def connect_to_db():
    connection = sqlite3.connect('todoData.db')
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            task TEXT NOT NULL,
            task_date TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    connection.commit()
    connection.close()

@app.route('/')
def index():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT tasks.task, tasks.task_date, users.username 
        FROM tasks 
        JOIN users ON tasks.user_id = users.id
    ''')
    tasks=cursor.fetchall()
    if 'user_id' in session:
        return render_template('index.html', tasks=tasks,user = session['user_name'])
    connection.close()
    return render_template('index.html',tasks=tasks)


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = cursor.fetchone()
    connection.close()
    
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['username']
        return redirect(url_for('dashboard'))
    flash('Invalid username or password')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        connection = connect_to_db()
        cursor = connection.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            connection.commit()
            connection.close()
            flash('Registration successful! Please login.')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            connection.close()
            flash('Username already taken. Please choose another.')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('SELECT id, task, task_date FROM tasks WHERE user_id = ?', (session['user_id'],))
    tasks = cursor.fetchall()
    connection.close()
    
    return render_template('dashboard.html', tasks=tasks,user=session['user_name'])

@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    task = request.form['task']
    task_date = None
    if task_date is None:
        task_date=datetime.now().strftime('%Y-%m-%d')
    else:
        task_date = request.form['task_date']
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('INSERT INTO tasks (user_id, task, task_date) VALUES (?, ?, ?)', (session['user_id'], task, task_date))
    connection.commit()
    connection.close()
    
    return redirect(url_for('dashboard'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (task_id, session['user_id']))
    connection.commit()
    connection.close()
    
    return redirect(url_for('dashboard'))

@app.route('/all_tasks')
def all_tasks():
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute('''
        SELECT tasks.task, tasks.task_date, users.username 
        FROM tasks 
        JOIN users ON tasks.user_id = users.id
    ''')
    tasks = cursor.fetchall()
    connection.close()
    return render_template('all_tasks.html', tasks=tasks)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

create_tables()