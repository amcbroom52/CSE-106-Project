from flask import Flask, render_template_string, render_template, request, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin 
from flask_admin.contrib.sqla import ModelView
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime


app = Flask(__name__)
CORS(app)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
admin = Admin(app, name='microblog', template_mode='bootstrap3') 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.secret_key = 'super secret key'
db = SQLAlchemy(app)
db.init_app(app)

class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String, unique=True, nullable=False)
  displayName = db.Column(db.String, unique=True, nullable=False)
  password = db.Column(db.String, unique=True, nullable=False)
  posts = db.relationship('Post', backref="User")
  comments = db.relationship('Comment', backref="User")

class Post(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  text = db.Column(db.String, nullable=False)
  author = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  timePosted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
  comments = db.relationship('Comment', backref='Post')

class Comment(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  text = db.Column(db.String, nullable=False)
  author = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  timePosted = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
  post = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

@app.route('/login')
def loginPage():
  return render_template('login.html')

@app.route('/registration')
def registrationPage():
  return render_template('registration.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
  username = request.form['username']
  if User.query.filter_by(username = username).first() is not None:
    return redirect(url_for('registrationPage'))
  if request.form['password1'] != request.form['password2']:
    return redirect(url_for('registrationPage'))
  password = request.form['password1']
  displayName = request.form['displayname']
  user = User(username = username, password = password, displayName = displayName)
  db.session.add(user)
  db.session.commit()
  return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
  username = request.form['username']
  user = User.query.filter_by(username = username).first()
  if user is None or user.password != request.form['password']:
    return redirect(url_for('loginPage'))
  else:
    login_user(user)
    return redirect(url_for('home'))

@app.route('/')
@login_required
def home():
  posts = Post.query.order_by(Post.timePosted.desc()).all()
  return render_template('feed.html', posts = posts)

@app.route('/post/<int:postID>')
@login_required
def post(postID):
  post = Post.query.filter_by(id = postID).first()
  return render_template('post.html', post=post, comments = post.comments)

@app.route('/makeComment/<int:postID>', methods=['GET', 'POST'])
@login_required
def makeComment(postID):
  comment = Comment(text = request.form['text'], author=current_user.id, post = postID)
  db.session.add(comment)
  db.session.commit()
  return redirect(url_for('post', postID=postID))

@app.route('/makePost')
@login_required
def makePostPage():
  return render_template('makePost.html')

@app.route('/makePost', methods=['GET', 'POST'])
@login_required
def makePost():
  post = Post(text = request.form['text'], author = current_user.id)
  db.session.add(post)
  db.session.commit()
  return redirect(url_for('home'))

@app.route('/messages', methods=['GET'])
@login_required
def render_messages():
  return render_template('messages.html')

@app.route('/profile', methods=['GET'])
@login_required
def render_profile():
  return render_template('profile.html')

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Comment, db.session))
admin.add_view(ModelView(Post, db.session))

if __name__ == '__main__':
    app.run(debug=True)

