from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import re

app = Flask(__name__)

app.secret_key = 'xyzsdfg'

# Establish MySQL connection
connection = mysql.connector.connect(
    host='localhost',
    user='root',
    
    password='nivedhya@30',
    database='sql_db'
)
cursor = connection.cursor(dictionary=True)


@app.route('/')
def index():
    return render_template('index.html')
@app.route('/home')
def home():
    pending_tasks = get_pending_tasks()
    return render_template('home.html', pending_tasks=pending_tasks)


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            message = 'Please enter both email and password!'
        else:
            cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password,))
            user = cursor.fetchone()
            if user:
                session['loggedin'] = True
                session['userid'] = user['userid']
                session['name'] = user['name']
                session['email'] = user['email']
                message = 'Logged in successfully!'
                return redirect(url_for('home'))  
            else:
                message = 'Please enter correct email/password!'

    return render_template('login.html', message=message)



@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ''

    if request.method == 'POST':
        userName = request.form.get('name')
        password = request.form.get('password')
        email = request.form.get('email')

        # Check if any of the fields is empty
        if not userName or not password or not email:
            message = 'Please fill out all the form fields!'
        # Validate email
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        else:
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cursor.fetchone()

            if account:
                message = 'Account already exists!'
                return render_template('login.html', message=message)
            else:
                cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s)', (userName, email, password))
                connection.commit()
                message = 'You have successfully registered!'
                return render_template('login.html', message=message)

    return render_template('register.html', message=message)


def get_tasks():
    user_id = session['userid']
    cursor.execute('SELECT * FROM tasks WHERE user_id = %s', (user_id,))
    tasks = cursor.fetchall()
    return tasks


@app.route('/createtask', methods=['GET', 'POST'])
def createtask():
    if 'loggedin' in session:
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            due_date = request.form['due_date']
            category = request.form['category']

            user_id = session['userid']
            cursor.execute('INSERT INTO tasks (user_id, title, description, due_date, category) VALUES (%s, %s, %s, %s, %s)',
            (user_id, title, description, due_date, category))
            connection.commit()

            return redirect(url_for('displaytasks'))

        return render_template('createtask.html')

    return redirect(url_for('login'))


@app.route('/updatetask/<int:task_id>', methods=['GET', 'POST'])
def updatetask(task_id):
    if 'loggedin' in session:
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            due_date = request.form['due_date']
            category = request.form['category']

            cursor.execute(
                'UPDATE tasks SET title=%s, description=%s, due_date=%s, category=%s WHERE id=%s',
                (title, description, due_date, category, task_id)
            )
            connection.commit()

            return redirect(url_for('displaytasks'))

        cursor.execute('SELECT * FROM tasks WHERE id=%s', (task_id,))
        task = cursor.fetchone()

        return render_template('updatetask.html', task=task)

    return redirect(url_for('login'))


@app.route('/organizetask')
def organizetask():
    if 'loggedin' in session:
        categories = get_tasks_by_category()
        return render_template('organizetask.html', categories=categories)

    return redirect(url_for('login'))
    


@app.route('/displaytasks')
def displaytasks():
    if 'loggedin' in session:
        tasks = get_tasks()
        return render_template('displaytasks.html', tasks=tasks)

    return redirect(url_for('login'))
@app.route('/mark_completed/<int:task_id>', methods=['POST'])
def mark_completed(task_id):
    if 'loggedin' in session:
        cursor = connection.cursor()

        
        cursor.execute('UPDATE tasks SET completed = NOT completed WHERE id=%s', (task_id,))
        connection.commit()

        return redirect(url_for('displaytasks'))

    return redirect(url_for('login'))
@app.route('/deletetask/<int:task_id>')
def deletetask(task_id):
    if 'loggedin' in session:
        cursor = connection.cursor(dictionary=True)


       
        cursor.execute('DELETE FROM tasks WHERE id=%s', (task_id,))
        connection.commit()

        return redirect(url_for('displaytasks'))

    return redirect(url_for('login'))

def get_tasks_by_category():
    user_id = session['userid']
    cursor.execute('SELECT category, GROUP_CONCAT(id) as task_ids FROM tasks WHERE user_id = %s GROUP BY category', (user_id,))
    tasks_by_category = cursor.fetchall()
    categories = []
    
    for row in tasks_by_category:
        category = {'name': row['category'], 'tasks': []}
        task_ids = row['task_ids'].split(',')
        
        for task_id in task_ids:
            cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
            task = cursor.fetchone()
            category['tasks'].append(task)
        
        categories.append(category)

    return categories


def get_pending_tasks():
    user_id = session['userid']
    cursor.execute('SELECT * FROM tasks WHERE user_id = %s AND completed = 0', (user_id,))
    pending_tasks = cursor.fetchall()
    return pending_tasks


if __name__ == "__main__":
    app.run(debug=True)
