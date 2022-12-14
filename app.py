from flask import Flask, render_template_string, render_template, request, redirect, url_for, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink 
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime

from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import uuid
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)
CORS(app)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
app.secret_key = 'super secret key'
db = SQLAlchemy(app)
db.init_app(app)

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


#function to restricts access to admin "home" page to anyone other than "Admin"
class MyAdminIndexView(AdminIndexView):
  def is_accessible(self):
    if(current_user.is_authenticated and current_user.username == "Admin"):
      return current_user.is_authenticated

  def inaccessible_callback(self, name, **kwargs):
    return redirect(url_for('home'))

#function to restricts access to admin model view pages page to anyone other than "Admin"
class MyModelView(ModelView):
  def is_accessible(self):
    if(current_user.is_authenticated and current_user.username == "Admin"):
      return current_user.is_authenticated

  def inaccessible_callback(self, name, **kwargs):
    return redirect(url_for('home'))

admin = Admin(app, name='microblog', template_mode='bootstrap3', index_view=MyAdminIndexView())
admin.add_link(MenuLink(name='Logout', category='', url="/logout")) 


class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String, unique=True, nullable=False)
  displayName = db.Column(db.String, unique=True, nullable=False)
  password = db.Column(db.String, unique=True, nullable=False)
  profile_pic = db.Column(db.String(150), nullable=True)
  bio = db.Column(db.String(), nullable=True)
  posts = db.relationship('Post', backref="User")
  comments = db.relationship('Comment', backref="User")
  followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

  def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

  def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

  def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

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
  #genrates a hashed password using bcrypt
  hashed_password = bcrypt.generate_password_hash(request.form['password1'])
  displayName = request.form['displayname']
  
  # Grab image file name
  filename = secure_filename(request.files['profile_picture'].filename)
  pfp_filename = str(uuid.uuid1()) + "_" + filename

  # Save image
  request.files['profile_picture'].save(os.path.join(app.config['UPLOAD_FOLDER'],  pfp_filename))

  user = User(username = username, password = hashed_password, displayName = displayName, profile_pic=pfp_filename)
  db.session.add(user)
  db.session.commit()

  return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
  username = request.form['username']
  password = request.form['password']
  user = User.query.filter_by(username = username).first()
  #if this user exists 
  if user:
  #checks for encrypted password, if not match then back to login
    if bcrypt.check_password_hash(user.password, password):
      login_user(user)
      if username == "Admin":
        return redirect(url_for('admin.index'))
      else:
        return redirect(url_for('home'))
  return redirect(url_for('loginPage'))

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
  pfp = current_user.profile_pic
  name = current_user.displayName
  bio = current_user.bio

  if bio == None:
    bio = "Click me to edit bio!"

  posts = Post.query.filter_by(author=current_user.id).all()

  return render_template('profile.html', pfp=pfp, name = name, bio = bio, posts=posts)

@app.route('/update_bio', methods=['POST'])
@login_required
def update_bio():

  current_user.bio = (request.json['new_bio'])
  db.session.commit()

  return redirect(url_for('render_profile'))


#simple logout url/function
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('loginPage'))

@app.route('/follow/<int:UserID>', methods=['GET', 'POST'])
@login_required
def follow(UserID):
  current_user.follow(UserID)
  return redirect(render_profile)

@app.route('/unfollow/<int:UserID>', methods=['GET', 'POST'])
@login_required
def unfollow(UserID):
  current_user.unfollow(UserID)
  return redirect(render_profile)


admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Comment, db.session))
admin.add_view(ModelView(Post, db.session))

if __name__ == '__main__':
    app.run(debug=True)

