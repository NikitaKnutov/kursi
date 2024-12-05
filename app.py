from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = '761-922-263'  # Секретный ключ для сессий

def get_db_connection():
    conn = sqlite3.connect('database/database.db', timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            gender TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            duration TEXT NOT NULL,
            cost REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (child_id) REFERENCES children (id)
        )
    ''')
    conn.commit()
    conn.close()

def reset_autoincrement(table_name):
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()

    # Удаляем все записи из таблицы
    cursor.execute(f'DELETE FROM {table_name}')

    # Сбрасываем автоинкрементный счетчик
    cursor.execute(f'UPDATE sqlite_sequence SET seq = 0 WHERE name = "{table_name}"')

    conn.commit()
    conn.close()

def init_courses():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Очищаем таблицу курсов
    cursor.execute('DELETE FROM courses')
    
    # Добавляем курсы
    courses = [
        ('Математика', '60 минут', 2000),
        ('Чтение', '45 минут', 2500),
        ('Письмо', '45 минут', 1800),
        ('Мир вокруг', '60 минут', 2200),
        ('Творчество', '60 минут', 2100),
        ('Мышление', '45 минут', 2000)
    ]
    
    cursor.executemany('INSERT INTO courses (name, duration, cost) VALUES (?, ?, ?)', courses)
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('main.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data['name']
    email = data['email']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (name, email, password) VALUES (?, ?, ?)
        ''', (name, email, password))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User registered successfully'}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': 'Email already exists'}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        return jsonify({'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    return jsonify({'message': 'Logged out'}), 200

@app.route('/profile')
def profile():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT name, email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

        cursor.execute('''
            SELECT c.name AS child_name, co.name AS course_name, e.id AS enrollment_id
            FROM enrollments e
            JOIN children c ON e.child_id = c.id
            JOIN courses co ON e.course_id = co.id
            WHERE c.user_id = ?
        ''', (user_id,))
        enrollments = cursor.fetchall()

        conn.close()

        if user:
            name, email = user
            return render_template('profile.html', name=name, email=email, enrollments=enrollments)
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/add_child', methods=['GET', 'POST'])
def add_child():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        birth_date = request.form['birth_date']
        gender = request.form['gender']
        user_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO children (user_id, name, birth_date, gender) VALUES (?, ?, ?, ?)
        ''', (user_id, name, birth_date, gender))
        conn.commit()
        conn.close()

        return redirect(url_for('profile'))

    return render_template('add_child.html')

@app.route('/children_list', methods=['GET'])
def children_list():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, birth_date, gender FROM children WHERE user_id = ?', (user_id,))
    children = cursor.fetchall()
    conn.close()

    return render_template('children_list.html', children=children)

@app.route('/delete_child/<int:child_id>', methods=['POST'])
def delete_child(child_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM children WHERE id = ? AND user_id = ?', (child_id, user_id))
    conn.commit()
    conn.close()

    return redirect(url_for('children_list'))

@app.route('/course1')
def course1():
    children = []
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM children WHERE user_id = ?', (user_id,))
        children = cursor.fetchall()
        conn.close()
    return render_template('course1.html', children=children)

@app.route('/course2')
def course2():
    children = []
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM children WHERE user_id = ?', (user_id,))
        children = cursor.fetchall()
        conn.close()
    return render_template('course2.html', children=children)

@app.route('/course3')
def course3():
    children = []
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM children WHERE user_id = ?', (user_id,))
        children = cursor.fetchall()
        conn.close()
    return render_template('course3.html', children=children)

@app.route('/course4')
def course4():
    children = []
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM children WHERE user_id = ?', (user_id,))
        children = cursor.fetchall()
        conn.close()
    return render_template('course4.html', children=children)

@app.route('/course5')
def course5():
    children = []
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM children WHERE user_id = ?', (user_id,))
        children = cursor.fetchall()
        conn.close()
    return render_template('course5.html', children=children)

@app.route('/course6')
def course6():
    children = []
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM children WHERE user_id = ?', (user_id,))
        children = cursor.fetchall()
        conn.close()
    return render_template('course6.html', children=children)

@app.route('/enroll', methods=['POST'])
def enroll():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    course_id = request.form['course_id']
    children = request.form.getlist('children')

    conn = get_db_connection()
    cursor = conn.cursor()

    for child_id in children:
        cursor.execute('INSERT INTO enrollments (course_id, child_id) VALUES (?, ?)', (course_id, child_id))

    conn.commit()
    conn.close()

    return "Вы успешно записаны на курс!", 200

@app.route('/unenroll/<int:enrollment_id>', methods=['POST'])
def unenroll(enrollment_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Проверка, что запись принадлежит текущему пользователю
    cursor.execute('''
        SELECT e.id
        FROM enrollments e
        JOIN children c ON e.child_id = c.id
        WHERE e.id = ? AND c.user_id = ?
    ''', (enrollment_id, user_id))
    enrollment = cursor.fetchone()

    if enrollment:
        cursor.execute('DELETE FROM enrollments WHERE id = ?', (enrollment_id,))
        conn.commit()

    conn.close()

    return redirect(url_for('enrollments_list'))

@app.route('/enrollments_list', methods=['GET'])
def enrollments_list():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.name AS child_name, co.name AS course_name, e.id AS enrollment_id
        FROM enrollments e
        JOIN children c ON e.child_id = c.id
        JOIN courses co ON e.course_id = co.id
        WHERE c.user_id = ?
    ''', (user_id,))
    enrollments = cursor.fetchall()
    conn.close()

    return render_template('enrollments_list.html', enrollments=enrollments)
    

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/teachers')
def teachers():
    return render_template('teachers.html')

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.name AS child_name, co.name AS course_name, e.id AS enrollment_id
        FROM enrollments e
        JOIN children c ON e.child_id = c.id
        JOIN courses co ON e.course_id = co.id
        WHERE c.user_id = ?
    ''', (user_id,))
    enrollments = cursor.fetchall()
    conn.close()

    return render_template('enrollments_list.html', enrollments=enrollments)

if __name__ == '__main__':
    init_db()
    init_courses()
    app.run(debug=True)