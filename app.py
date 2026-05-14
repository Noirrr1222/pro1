from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_it_in_production'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/portfolio')
def portfolio():
    all_projects = Project.query.all()
    return render_template('portfolio.html', projects=all_projects)


@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if request.method == 'POST':
        new_feedback = Feedback(
            name=request.form.get('username'),
            email=request.form.get('user_email'),
            message=request.form.get('user_message')
        )
        db.session.add(new_feedback)
        db.session.commit()
        return redirect(url_for('contacts'))
    return render_template('contacts.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            error = 'Неверный логин или пароль'

    return f"""
    <html>
    <head>
        <title>Вход в панель управления</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .login-box {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }}
            input {{ width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
            button {{ width: 100%; background: hsl(231, 65%, 54%); color: white; padding: 12px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 16px; }}
            .error {{ color: #dc3545; margin-bottom: 15px; font-weight: bold; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>🔑 Вход в админку</h2>
            {f'<p class="error">{error}</p>' if error else ''}
            <form method="POST">
                <input type="text" name="username" placeholder="Логин" required>
                <input type="password" name="password" placeholder="Пароль" required>
                <button type="submit">Войти</button>
            </form>
        </div>
    </body>
    </html>
    """


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    # Защита маршрута: если сессия не активна, перенаправляем на авторизацию
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_project':
            new_project = Project(
                title=request.form.get('title'),
                description=request.form.get('description')
            )
            db.session.add(new_project)
            db.session.commit()

        elif action == 'delete_project':
            project_id = request.form.get('project_id')
            project_to_delete = Project.query.get(project_id)
            if project_to_delete:
                db.session.delete(project_to_delete)
                db.session.commit()

        return redirect(url_for('admin_panel'))

    all_messages = Feedback.query.all()
    all_projects = Project.query.all()

    # В HTML-код добавлена шапка со стилизованной кнопкой "Выйти"
    html_output = """
    <html>
    <head>
        <title>Панель управления</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f4f4f9; color: #333; }
            .header-container { display: flex; justify-content: space-between; align-items: center; }
            .section { background: white; padding: 25px; margin-bottom: 30px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            .card { background: #fafafa; padding: 15px; margin-top: 15px; border-left: 5px solid hsl(231, 65%, 54%); border-radius: 4px; position: relative; }
            input, textarea { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            button { background: hsl(231, 65%, 54%); color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
            .del-btn { background: #dc3545; position: absolute; right: 15px; top: 15px; padding: 5px 10px; font-size: 12px; }
            .logout-btn { background: #6c757d; text-decoration: none; color: white; padding: 10px 20px; border-radius: 4px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header-container">
            <h1>Панель администратора</h1>
            <a href="/logout" class="logout-btn">🚪 Выйти</a>
        </div>
        <hr><br>

        <!-- Форма добавления проектов -->
        <div class="section">
            <h2>➕ Добавить новый проект в Портфолио</h2>
            <form method="POST">
                <input type="hidden" name="action" value="add_project">
                <input type="text" name="title" placeholder="Название проекта" required>
                <textarea name="description" placeholder="Описание проекта (какие технологии использовались)" rows="3" required></textarea>
                <button type="submit">Сохранить проект</button>
            </form>
        </div>

        <!-- Список текущих проектов -->
        <div class="section">
            <h2>💼 Текущие проекты в базе данных</h2>
            """
    if not all_projects:
        html_output += "<p>Проектов пока нет.</p>"
    for proj in all_projects:
        html_output += f"""
        <div class="card">
            <h3>{proj.title}</h3>
            <p>{proj.description}</p>
            <form method="POST" style="margin:0;">
                <input type="hidden" name="action" value="delete_project">
                <input type="hidden" name="project_id" value="{proj.id}">
                <button type="submit" class="del-btn">Удалить</button>
            </form>
        </div>
        """
    html_output += """
        </div>

        <div class="section">
            <h2>📧 Сообщения от пользователей (Форма контактов)</h2>
    """
    if not all_messages:
        html_output += "<p>Сообщений пока нет.</p>"
    for msg in all_messages:
        html_output += f"""
        <div class="card" style="border-left-color: #28a745;">
            <h3>👤 Имя: {msg.name} (Email: {msg.email})</h3>
            <p>💬 {msg.message}</p>
        </div>
        """
    html_output += "</div></body></html>"
    return html_output


if __name__ == '__main__':
    app.run(debug=True)
