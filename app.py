import time

from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user

UPLOAD_FOLDER = 'static/pics/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///able.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = os.urandom(12)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


class Shop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    photo = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(300), nullable = False)
    price = db.Column(db.Integer, nullable = False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Shop %r>' % self.id


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    post = db.Column(db.String(50), nullable=False)
    pas = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    shopcart = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        return '<Users %r>' % self.id


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    text = db.Column(db.String(300), nullable = False)
    prodid = db.Column(db.Integer, nullable=False)
    feedname = db.Column(db.String(300), nullable = False)
    time = db.Column(db.DateTime, default=datetime.utcnow)
    recom = db.Column(db.Boolean, nullable = False)
    feedpost = db.Column(db.String(300), nullable = False)

    def __repr__(self):
        return '<Feedback %r>' % self.id


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect('/login')


@app.route('/buy')
def buy():
    return render_template('buy.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route("/redact/<int:id>", methods=['POST', 'GET'])
@login_required
def redact(id):
    if current_user.post != Shop.query.get(id).author:
        return redirect('/')
    if request.method == 'POST':
        name = request.form.get('name', False)
        desk = request.form.get('deskription', False)
        price = request.form.get('price', False)
        Shop.query.get(id).name = name
        Shop.query.get(id).description = desk
        Shop.query.get(id).price = price
        db.session.commit()
        return redirect('/')
    return render_template('redact.html', prod = Shop.query.get(id))


@app.route('/')
@app.route('/home')
def index():
    posts = Shop.query.order_by(Shop.date).all()
    return render_template("templates/index.html", posts=posts)


@app.route('/register', methods=['POST', 'GET'])
def reg():
    if request.method == 'POST':
        username = request.form.get('username', False)
        post = request.form.get('post', False)
        password1 = request.form.get('pas', False)
        password2 = request.form.get('pas2', False)
        shopcart=''
        if password1 == password2:
            user = Users(username = username, pas = password1, post = post, shopcart=shopcart)
            db.session.add(user)
            db.session.commit()
            return redirect('/')
        else:
            return redirect('/register')
    else:
        return render_template("register.html")


@app.route('/create-pos', methods=['POST', 'GET'])
@login_required
def pos():
    if request.method == 'POST':
        name = request.form.get('name', False)
        description = request.form.get('deskription', False)
        price = request.form.get('price', False)

        file = request.files.get('filename', False)
        if file.filename == '':
            flash('Нет выбранного файла')
            return redirect('home')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if description == '':
                description = "Описание не добавлено"
            shop = Shop(name = name, description = description, photo = 'static/pics/'+file.filename, author = current_user.post, price = int(price))
            db.session.add(shop)
            db.session.commit()
            return redirect('/')

    else:
        return render_template("create-pos.html")


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(user_id)


@app.route('/cart', methods=['POST', 'GET'])
@login_required
def cart():
    prods = ((current_user.shopcart).split('.'))[0:-1]
    finalprice = 0
    for i in prods:
        finalprice = finalprice + Shop.query.get(i).price
    return render_template('cart.html', prods=prods, Shop = Shop, finalprice = finalprice)


@app.route('/addtocart/<int:id>')
@login_required
def addtocart(id):
    current_user.shopcart = current_user.shopcart + str(id) + '.'
    db.session.commit()
    return redirect('/')


@app.route('/remove/<int:id>')
@login_required
def remove(id):
    mas = ((current_user.shopcart).split('.'))[0:-1]
    indx = mas.index(str(id))
    mas.pop(indx)
    current_user.shopcart = '.'.join(mas)
    if len(current_user.shopcart) != 0:
        current_user.shopcart = '.'.join(mas) + '.'
    else:
        current_user.shopcart = '.'.join(mas)
    db.session.commit()
    return redirect('/cart')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:
            if int(request.form.get('pas')) == Users.query.filter_by(post = request.form.get('post', False)).first().pas:
                login_user(Users.query.filter_by(post = request.form.get('post', False)).first())
                return redirect('home')
        except:
            return redirect('login')
    return render_template("login.html")


@app.route('/My_Profile', methods=['POST', 'GET'])
@login_required
def profile():
    return render_template("profile.html")


@app.route('/delete', methods=['POST', 'GET'])
@login_required
def dele():
    if request.method == 'POST':
        if request.form.get('password', False) == '12345':
            Shop.query.filter_by(id=int(request.form.get('ids', False))).delete()
            db.session.commit()
            return redirect('/')
    return render_template('delete.html')


@app.route('/changepas', methods=['POST', 'GET'])
def changepas():
    if request.method == 'POST':
        if str(current_user.pas) == request.form.get('userpas', False):
            if request.form.get('newpas', False) == request.form.get('newpas2', False):
                current_user.pas = request.form.get('newpas', False)
                db.session.commit()
                logout_user()
                return redirect('/login')
            return redirect('/')
        return redirect('/')
    return render_template('changepas.html')


@app.route('/delcom/<int:id1>/<int:id2>')
def delcom(id1, id2):
    if current_user.post == Feedback.query.get(id2).feedpost:
        Feedback.query.filter_by(id = id2).delete()
        db.session.commit()
        return redirect('/product/'+str(id1))
    else:
        return redirect('/home')

@app.route('/deleteacc')
@login_required
def delacc():
    Users.query.filter_by(id = current_user.get_id()).delete()
    db.session.commit()
    return redirect('/')


@app.route('/product/<int:id>', methods=["POST", "GET"])
@login_required
def prod(id):
    if request.method == "POST":
        title = request.form.get('revname', False)
        text = request.form.get('revtext', False)
        prodid = id
        feedname = current_user.username
        recom = 'recom' in request.form
        feedpost = current_user.post
        feed = Feedback(title = title, text = text, prodid = prodid, feedname = feedname, recom = recom, feedpost = feedpost)
        db.session.add(feed)
        db.session.commit()
        return redirect('/product/'+str(id))
    feedbacks = Feedback.query.order_by(Feedback.time).all()
    products = Shop.query.get(id)
    return render_template('product.html', products=products, feeds=feedbacks)


if __name__ == "__main__":
    app.run(debug=True)
