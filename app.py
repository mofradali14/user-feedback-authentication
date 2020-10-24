from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, DeleteForm
from sqlalchemy.exc import IntegrityError



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres:///authenticate_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'kfjgga'
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)

@app.route('/')
def index():
    return redirect(f'/users')

@app.route('/users')
def users_list():

    users = User.query.order_by(User.username).all()
    if 'username' in session:
        return render_template('user_list.html', users=users)
    else:
        return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)
        
        db.session.add(new_user)

        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken. Please pick another')
            return render_template('register.html', form=form)

        session['username'] = new_user.username
        flash('Welcome! Successfully Created Your Account!', 'success')
        return redirect(f'/users/{new_user.username}')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        
        if user:
            flash(f'Welcome back, {user.username}!', 'primary')
            session['username'] = user.username
            return redirect(f'/users/{user.username}')
        else:
            form.username.errors = ['Incorrect Username or Password.']
    return render_template('login.html', form=form)

@app.route(f'/users/<username>')
def user_page(username):
    if 'username' not in session:
        flash(f"You're going to need to login first!", 'danger')
        return redirect('/login')

    user = User.query.get(username)
    form = DeleteForm()
    return render_template('user.html', user=user, form=form)

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    if session['username'] == user.username:
        db.session.delete(user)
        db.session.commit()
        session.pop('username')
        flash('You have deleted your account.', 'danger')
        return redirect('/')
    else:
        flash("Nice try, you can't delete this account.", 'danger')
        return redirect(f'/users/{user.username}')

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    form = FeedbackForm()
    
    if "username" not in session:
        flash('You are not authorized to do this', 'danger')
        return redirect(f'/users/{username}')

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        feedback = Feedback(title=title, content=content, username=username)
        db.session.add(feedback)
        db.session.commit()
        return redirect(f'/users/{username}')
    else:
        return render_template('feedback_form.html', form=form)


@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):

    feedback = Feedback.query.get(feedback_id)
    form = FeedbackForm(obj=feedback)
    if "username" not in session or feedback.username != session['username']:
        flash('You are not authorized to do this', 'danger')
        return redirect(f'/users/{feedback.username}')
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        return redirect(f'/users/{feedback.username}')
    return render_template('feedback_edit.html', form=form, feedback=feedback)

@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    feedback = Feedback.query.get(feedback_id)

    if 'username' not in session or feedback.username != session['username']:
        flash("You're not authorized to do this", 'danger')
        return redirect(f'/users')
    form = DeleteForm()
    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()
    return redirect(f'/users')


@app.route('/logout')
def logout():
    session.pop('username')
    flash("You have logged out successfully", 'info')
    return redirect('/login')