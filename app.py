from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import date

app = Flask(__name__)
app.secret_key = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)

class HabitCompletion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habit.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=date.today)

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/stats')
def stats():
    user_id = 1

    total_habits = Habit.query.filter_by(user_id=user_id).count()
    completed = HabitCompletion.query.filter_by(user_id=user_id).count()

    completion_rate = round((completed / total_habits) * 100, 1) if total_habits > 0 else 0

    stats = {
        'total_habits': total_habits,
        'completed_habits': completed,
        'completion_rate': completion_rate
    }

    return render_template('stats.html', stats=stats)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)