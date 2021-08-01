from flask.globals import request
from flask.helpers import flash, url_for
from flask_login.utils import login_required, logout_user
from app import app, db
from flask import render_template, redirect, url_for
from app.forms import LikeForm, RegisterForm, LoginForm, WritePostForm, ReplyForm, EditProfileForm, FollowForm, MessageForm
from flask_login import current_user, login_user
from app.models import Post, User, Replies, Message
from datetime import datetime

@app.route('/')
@app.route('/index')
def index():
    login_form = LoginForm()
    posts = Post.query.order_by(Post.timestamp.desc()).all()

    return render_template('index.html', posts=posts, title="Home", login_form=login_form)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user is None or not user.check_password(login_form.password.data):
            flash('username or password invalid')
            return redirect(url_for('login'))
        login_user(user)
        return redirect(url_for('user_index'))
    return render_template('login.html', title="Login", login_form=login_form)

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('user_index'))
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You have been registered successfully')
        login_user(user)
        return redirect(url_for('user_index'))
    return render_template('register.html', title="Register", form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/user_index', methods=['GET', 'POST'])
@login_required
def user_index():
    form = WritePostForm()
    reply_form = ReplyForm()
    login_form = LoginForm()
    like_form = LikeForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post added')
        return redirect(url_for('user_index'))
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    #get the post_id from the replies
    replies = Replies.query.all()
    return render_template('user_index.html', form=form, posts=posts,
                 reply_form=reply_form, replies=replies, login_form=login_form, like_form=like_form)

@app.route('/user/<username>')
def user(username):
    follow_form = FollowForm()
    user = User.query.filter_by(username=username).first_or_404()

    posts = Post.query.all()
    return render_template('user.html', user=user, posts=posts, follow_form=follow_form)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    edit_form = EditProfileForm()
    if edit_form.validate_on_submit():
        current_user.username = edit_form.username.data
        current_user.about_me = edit_form.about_me.data
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('edit_profile'))
    elif request.method ==  'GET':
        edit_form.username.data = current_user.username
        edit_form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', edit_form=edit_form, title="Edit Profile")

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    follow_form = FollowForm()
    if follow_form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('user_index'))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    follow_form = FollowForm()
    if follow_form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('user_index'))

@app.route('/like/<int:post_id>', methods=['GET', 'POST'])
def like(post_id):
    like_form = LikeForm()
    if like_form.validate_on_submit():
        post = Post.query.filter_by(id=post_id).first()
        if post.likes is None:
            post.likes = 'a'
            db.session.commit()
            return redirect(url_for('user_index'))
        else:
            post.likes = post.likes + 'a'
            db.session.commit()
            return redirect(url_for('user_index'))
            
    return redirect(url_for('user_index'))

@app.route('/reply/<int:post_id>', methods=['GET', 'POST'])
def reply(post_id):
    form = WritePostForm()
    reply_form = ReplyForm()
    if reply_form.validate_on_submit():
        reply = Replies(body=reply_form.body.data, author=current_user)
        reply.post_id = post_id
        db.session.add(reply)
        db.session.commit()
        return redirect(url_for('user_index'))
    replies = Replies.query.filter_by(post_id=post_id).all()
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('user_index.html', reply_form=reply_form, replies=replies, posts=posts, form=form)

@app.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('messages'))
    return render_template('send_message.html', title='Send Message',
                           form=form, recipient=recipient)

@app.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    messages = current_user.messages_received.order_by(Message.timestamp.desc()).all()
    return render_template('messages.html', messages=messages)

@app.route('/for_you')
def for_you():
    posts = current_user.followed_posts()
    replies = Replies.query.all()

    return render_template('for_you.html', posts=posts, replies=replies)