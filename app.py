from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date,datetime,timedelta
from flask_mail import Mail, Message
import random
import os
from werkzeug.utils import secure_filename
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sqlalchemy import Column, DateTime

scheduler = BackgroundScheduler()
UPLOAD_FOLDER = 'static/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = 'secret123'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kerksiauer@gmail.com'  
app.config['MAIL_PASSWORD'] = 'rhss uwam sogx zzfg'  
app.config['MAIL_DEFAULT_SENDER'] = 'kerksiauer@gmail.com'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), unique=True, nullable=True)
    password = db.Column(db.String(200), nullable=False)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    birthday = db.Column(db.Date, nullable=True)  
    age = db.Column(db.Integer, nullable=True)  
    description = db.Column(db.String(500), nullable=True)
    avatar = db.Column(db.String(200), nullable=True)  

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    target_frequency = db.Column(db.Integer, nullable=True)  
    frequency_period = db.Column(db.String(10), nullable=True)
    reminder_time = db.Column(db.Time, nullable=True)
    user = db.relationship('User', backref='habits')
    last_reminder_sent = db.Column(DateTime, nullable=True)

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
        email = request.form['email']
        password = request.form['password']
        hashed = generate_password_hash(password)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered.")
            return redirect(url_for('register'))

        otp = random.randint(100000, 999999)

        msg = Message('Your OTP Code', recipients=[email])
        msg.body = f'Your OTP code is: {otp}'
        try:
            mail.send(msg)
            flash("OTP sent to your email.")
        except Exception as e:
            flash(f"Error sending OTP: {str(e)}")
            return redirect(url_for('register'))

        session['otp'] = otp

        new_user = User(email=email, password=hashed)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['email'] = new_user.email

        return redirect(url_for('verify_otp'))

    return render_template('register.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']

        if int(entered_otp) == session.get('otp'):
            flash("OTP verified successfully!")
            return redirect(url_for('index'))
        else:
            flash("Invalid OTP. Please try again.")
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['email'] = user.email
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            otp = random.randint(100000, 999999)
            session['reset_otp'] = otp
            session['reset_email'] = email

            msg = Message('Password Reset OTP', recipients=[email])
            msg.body = f'Your OTP to reset your password is: {otp}'
            try:
                mail.send(msg)
                flash('OTP sent to your email.')
                return redirect(url_for('reset_password_verify'))
            except Exception as e:
                flash(f"Failed to send OTP: {str(e)}")
        else:
            flash('No account with that email.')
    return render_template('forgot_password.html')

@app.route('/reset_password_verify', methods=['GET', 'POST'])
def reset_password_verify():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if int(entered_otp) == session.get('reset_otp'):
            flash("OTP verified. Please set your new password.")
            return redirect(url_for('reset_password'))
        else:
            flash("Invalid OTP.")
    return render_template('reset_password_verify.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash("Passwords do not match. Please try again.")
            return redirect(url_for('reset_password'))
    
        hashed = generate_password_hash(new_password)
        email = session.get('reset_email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            user.password = hashed
            db.session.commit()
            flash("Password reset successful. You can now log in.")
            session.pop('reset_email', None)
            session.pop('reset_otp', None)
            return redirect(url_for('login'))
        else:
            flash("Error resetting password.")

    return render_template('reset_password.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/habits')
def habits():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    name = session.get('name')
    user = User.query.get(user_id)

    xp_needed = 100 + (user.level - 1) * 50
    progress_percent = int((user.xp / xp_needed) * 100) if xp_needed > 0 else 0
    progress_class = f"w-[{progress_percent}%]"

    user_habits = Habit.query.filter_by(user_id=user_id).all()

    habits_with_data = []
    
    for habit in user_habits:
        completions_query = HabitCompletion.query.filter_by(habit_id=habit.id, user_id=user_id)

        if habit.frequency_period == 'day':
            start_date = date.today()
        elif habit.frequency_period == 'week':
            start_date = date.today() - timedelta(days=date.today().weekday())  
        elif habit.frequency_period == 'month':
            start_date = date.today().replace(day=1)

        completions = completions_query.filter(HabitCompletion.date >= start_date).count()

        habits_with_data.append({
            'id': habit.id,
            'name': habit.name,
            'streak': completions,
            'goal': habit.target_frequency,
            'period': habit.frequency_period,
            'on_track': completions >= habit.target_frequency
        })

    return render_template('habit.html',
                           habits=habits_with_data,
                           name=name,
                           user=user,
                           xp_needed=xp_needed,
                           progress_class=progress_class)

@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today()

    total_habits = Habit.query.filter_by(user_id=user_id).count()
    completed_today = HabitCompletion.query.filter_by(user_id=user_id, date=today).count()

    chart_data = {
        'labels': ['Completed Today', 'Remaining'],
        'data': [completed_today, max(total_habits - completed_today, 0)]
    }

    stats = {
        'total_habits': total_habits,
        'completed_habits': completed_today,
        'completion_rate': round((completed_today / total_habits) * 100, 1) if total_habits else 0
    }

    return render_template('stats.html', stats=stats, chart_data=chart_data)

@app.route('/weekly_report')
def weekly_report():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())  
    
    daily_completions = {}
    total_habits = Habit.query.filter_by(user_id=user_id).count()

    for i in range(7):
        day = start_of_week + timedelta(days=i)
        count = HabitCompletion.query.filter_by(user_id=user_id, date=day).count()
        daily_completions[day.strftime('%a %d')] = count  

    total_completed = sum(daily_completions.values())
    avg_completion_rate = (total_completed / (total_habits * 7) * 100) if total_habits > 0 else 0

    zipped_data = list(zip(daily_completions.keys(), daily_completions.values()))

    report_data = {
        'daily_data': zipped_data,
        'total_habits': total_habits,
        'total_completed': total_completed,
        'avg_completion_rate': round(avg_completion_rate, 1)
    }

    return render_template('weekly_report.html', report=report_data)


@app.route('/add_habit', methods=['GET', 'POST'])
def add_habit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        habit_name = request.form['habit_name']
        target_frequency = int(request.form['target_frequency'])
        frequency_period = request.form['frequency_period']
        reminder_time_str = request.form.get('reminder_time')  
        user_id = session['user_id']

        reminder_time = None
        if reminder_time_str:
            reminder_time = datetime.strptime(reminder_time_str, '%H:%M').time()

        new_habit = Habit(
            name=habit_name,
            user_id=user_id,
            target_frequency=target_frequency,
            frequency_period=frequency_period,
            reminder_time=reminder_time  
        )

        db.session.add(new_habit)
        db.session.commit()
        flash('Habit added successfully with reminder!')
        return redirect(url_for('habits'))

    return render_template('add_habit.html')

@app.route('/complete_habit/<int:habit_id>', methods=['POST'])
def complete_habit(habit_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    today = date.today()

    existing_completion = HabitCompletion.query.filter_by(
        habit_id=habit_id,
        user_id=user_id,
        date=today
    ).first()

    if existing_completion:
        flash('✅ You already completed this habit today!')
    else:
        completion = HabitCompletion(habit_id=habit_id, user_id=user_id, date=today)
        db.session.add(completion)

        user = User.query.get(user_id)
        xp_earned = 30
        leveled_up = add_xp_and_check_level(user, xp_earned)

        db.session.commit()

        flash(f'🎉 Habit completed! +{xp_earned} XP earned.')
        if leveled_up:
            flash(f'🚀 You leveled up to Level {user.level}!')

    return redirect(url_for('habits'))

@app.route('/delete_habit/<int:habit_id>', methods=['POST'])
def delete_habit(habit_id):
    if 'user_id' not in session:
        return redirect(url_for('login')) 
    
    user_id = session['user_id']
    habit = Habit.query.filter_by(id=habit_id, user_id=user_id).first()
    
    if habit:
        db.session.delete(habit)  
        db.session.commit()  
        flash('Habit deleted successfully!')  
    else:
        flash('Habit not found or unauthorized action.')  
    
    return redirect(url_for('habits')) 

def xp_for_next_level(level):
    return 100 + (level - 1) * 50

def add_xp_and_check_level(user, amount):
    user.xp += amount
    leveled_up = False

    while user.xp >= xp_for_next_level(user.level):
        user.xp -= xp_for_next_level(user.level)
        user.level += 1
        leveled_up = True

    return leveled_up

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if user:
        total_habits = Habit.query.filter_by(user_id=user_id).count()

        habit_completions = HabitCompletion.query.filter_by(user_id=user_id).all()
        streaks = {}  
        for completion in habit_completions:
            habit_id = completion.habit_id
            if habit_id not in streaks:
                streaks[habit_id] = 1 
            else:
                streaks[habit_id] += 1

        max_streak = max(streaks.values(), default=0)

        badges = ['Habit Master', 'Streak King', 'Goal Crusher'] 

        return render_template('profile.html', user=user, total_habits=total_habits, max_streak=max_streak, badges=badges)
    else:
        flash("User not found.")
        return redirect(url_for('index'))


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if request.method == 'POST':
        name = request.form['name']
        birthday_str = request.form['birthday']
        age = request.form['age']
        description = request.form['description']

        try:
            birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
            age = int(age)

            if name != user.name:
                if User.query.filter_by(name=name).first():
                    flash("Name already taken.")
                    return redirect(url_for('edit_profile'))

            user.name = name
            user.birthday = birthday
            user.age = age
            user.description = description

            if 'avatar' in request.files:
                avatar_file = request.files['avatar']
                if avatar_file and avatar_file.filename != '' and '.' in avatar_file.filename:
                    ext = avatar_file.filename.rsplit('.', 1)[1].lower()
                    if ext in ['png', 'jpg', 'jpeg', 'gif']:
                        filename = f"user_{user.id}_avatar.{ext}"
                        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        avatar_file.save(avatar_path)
                        user.avatar = filename

            db.session.commit()
            flash("Profile updated successfully!")
            return redirect(url_for('profile'))

        except ValueError:
            flash("Invalid input. Please make sure all fields are correct.")
            return redirect(url_for('edit_profile'))

    return render_template('edit_profile.html', user=user)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_reminder_email(user_email, habit_name):
    try:
        msg = Message(
            subject='⏰ Habit Reminder!',
            recipients=[user_email]
        )
        msg.body = (
            f"Hello!\n\n"
            f"This is a friendly reminder to come Habit Traveler and check in your habit: \"{habit_name}\".\n"
            f"Keep up the great work and stay consistent!\n\n"
            f"See you in the app!"
        )
        mail.send(msg)
        print(f"Reminder sent to {user_email} for habit {habit_name}")
    except Exception as e:
        print(f"Error sending reminder email: {e}")

def check_and_send_reminders():
    with app.app_context():
        now = datetime.now()
        now_time = now.time().replace(second=0, microsecond=0)

        one_min_ago = (now - timedelta(minutes=1)).time()

        habits_due = Habit.query.filter(
            Habit.reminder_time >= one_min_ago,
            Habit.reminder_time <= now_time
        ).all()

        for habit in habits_due:
            if habit.last_reminder_sent and habit.last_reminder_sent.date() == now.date():
                continue

            user_email = habit.user.email
            send_reminder_email(user_email, habit.name)

            habit.last_reminder_sent = now
            db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(check_and_send_reminders, 'interval', minutes=1)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        scheduler.start()
    app.run(debug=True)