import graphlib
import os
import string
from turtle import color
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")
from datetime import datetime
from flask import redirect
from flask import Flask, flash, render_template, url_for, session, request
from flask import current_app as app
from flask import make_response
from flask_login import login_user, LoginManager, login_required, logout_user, current_user, UserMixin
from sqlalchemy import UniqueConstraint
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Tej002'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///grocstore.sqlite3"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#_________________models_________________________________________________________________________________________

class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    adm_name = db.Column(db.String(50), unique=True, nullable=False)
    pw = db.Column(db.String(255), nullable=False)

class Category(db.Model, UserMixin):
    __tablename__ = 'category'
    id = db.Column(db.Integer, autoincrement = True ,primary_key=True)
    c_name = db.Column(db.String(100), nullable=False)

class Product(db.Model, UserMixin):
    __tablename__ = 'product'
    id = db.Column(db.Integer, autoincrement = True ,primary_key=True)
    p_name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    mfd = db.Column(db.DateTime)
    exp = db.Column(db.DateTime)
    c_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='CASCADE'))
    category = db.relationship('Category', backref=db.backref('product', lazy=True))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement = True ,primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    email_id = db.Column(db.String(100), unique=True, nullable=False)
    
class Cart(db.Model, UserMixin):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, autoincrement = True ,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    c_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    c_name = db.Column(db.String(100))
    p_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    p_name = db.Column(db.String(100))
    unit = db.Column(db.String(100))
    price = db.Column(db.Integer)
    quantity = db.Column(db.Integer, nullable=False)

class History(db.Model, UserMixin):
    __tablename__ = 'history'
    id = db.Column(db.Integer, autoincrement = True ,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    c_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    c_name = db.Column(db.String(100))
    p_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    p_name = db.Column(db.String(100))
    unit = db.Column(db.String(100))
    price = db.Column(db.Integer)
    quantity = db.Column(db.Integer, nullable=False)


# __________________Admin-Routes_____________________________________________________________________________________

@app.route("/",methods=["GET","POST"])
def welcome():
    return render_template('welcome.html', state=True)

@app.route("/adminlogin",methods=["GET","POST"])
def adminlogin():
    return render_template('adminlogin.html')

@app.route("/admin",methods=["GET","POST"])
def adminsignup():
    if request.method == "POST":
        name = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(adm_name=name, pw=password).first()
        if admin:
            return redirect('/admindash')
        else:
            return 'Incorrect username or password'
    return redirect(url_for('admindash'))    
    
@app.route("/admindash", methods=["GET","POST"])  
def admindash():
    c = Category.query.all()
    return render_template('admindash.html', cards = c)

@app.route('/add_category', methods = ["GET","POST"])
def add_category():
    if request.method == 'GET':
        return render_template('add_category.html')
    if request.method == 'POST':
        category_name = request.form['category_name']
        cat = Category(c_name=category_name)
        db.session.add(cat)
        db.session.commit()
        return redirect(url_for('admindash'))
    
@app.route('/edit_category/<category_id>', methods = ["GET","POST"])
def edit_category(category_id):
    category = Category.query.filter_by(id = category_id).first()
    if request.method == "GET":
        return render_template('edit_category.html', category = category)
    if request.method == "POST":
        category.c_name = request.form['category_name']
        db.session.commit()
        return redirect(url_for("admindash"))


@app.route('/delete_category/<category_id>', methods = ["GET","POST"])
def delete_category(category_id):
    if request.method == "GET":
        caty = Category.query.filter_by(id = category_id).first()
        prod = Product.query.filter_by(c_id = category_id).all()
        for p in prod:
            db.session.delete(p)
        db.session.delete(caty)
        db.session.commit()
        flash('Category and its products are sucessfully deleted')
        return redirect(url_for('admindash'))    
    
@app.route("/product/<cat_id>", methods=["GET","POST"])
def product(cat_id):
    p = Product.query.filter_by(c_id = cat_id).all()
    d={}
    d['cards']=p
    d['cat_id']=cat_id
    d['n']= True if len(p)>0 else False
    if request.method=="GET":
        return render_template('product.html', cards = d)

@app.route('/add_product/<cat_id>', methods=['GET', 'POST'])
def add_product(cat_id):
    c_id = Category.query.filter_by(id = cat_id).first()
    if not c_id:
        return "No such category"
    if request.method == 'GET':
        return render_template('add_product.html', cat = c_id)
    if request.method == 'POST':
        product_name = request.form['product_name']
        price = request.form['price']
        unit = request.form['unit']
        stock = request.form['stock']
        manufacturing_date = request.form['manufacturing_date']
        expiry_date = request.form['expiry_date']
        mfd1 = datetime.strptime(manufacturing_date, '%Y-%m-%d')
        exp1 = datetime.strptime(expiry_date, '%Y-%m-%d')
        product = Product(p_name =product_name,
                        price = price,
                        unit = unit,
                        quantity = stock,
                        mfd = mfd1,
                        exp = exp1,
                        c_id = c_id.id)
        db.session.add(product)
        db.session.commit()
        return redirect(f'/product/{c_id.id}')
    
@app.route('/edit_product/<product_id>', methods = ["GET","POST"])
def edit_product(product_id):
    product = Product.query.filter_by(id = product_id).first()
    if request.method == "GET":
        return render_template('edit_product.html', product = product)
    if request.method == "POST":
        product.p_name = request.form['product_name']
        product.price = request.form['price']
        product.unit = request.form['unit']
        product.quantity = request.form['stock']
        manufacturing_date = request.form['manufacturing_date']
        expiry_date = request.form['expiry_date']
        product.mfd = datetime.strptime(manufacturing_date, '%Y-%m-%d')
        product.exp = datetime.strptime(expiry_date, '%Y-%m-%d')
        db.session.commit()
        return redirect(url_for('product', cat_id = product.c_id))


@app.route('/delete_product/<product_id>', methods = ["GET","POST"])
def delete_product(product_id):
    if request.method == "GET":
        product = Product.query.filter_by(id = product_id).first()
        cat_id1 = product.c_id 
        c = Cart.query.all()
        for c1 in c:
            if c1.p_id == product.id:
                db.session.delete(c1)
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for('product', cat_id = cat_id1))   

@app.route('/summary', methods = ["GET","POST"])
def summary():
    cart = History.query.all()
    category = []
    price = []
    d = {}
    for c in cart:
        d[c.c_name] = 0
    for c in cart:
        d[c.c_name] += (c.price * c.quantity)
    for d1 in d:
        category.append(d1)
        price.append(d[d1])
    plt.figure(figsize=(10,6)) 
    plt.clf()
    plt.bar(category, price, width= 0.3, align='center', color = '#6ab04c')
    font = {'family': 'sans-serif', 'size': 8}
    plt.rc('font', **font)
    plt.xlabel("Category")
    plt.ylabel("Revenue generated")
    plt.xticks(rotation='horizontal', fontsize = 8)
    plt.savefig('static/summary_graph.png')
    return render_template('summary.html')

#________________________User-Routes_______________________________________________________________________________

@app.route("/userlogin", methods=["GET","POST"])
def userlogin():
    if request.method == 'GET':
        return render_template('userlogin.html')
    if request.method == "POST":
        name = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=name, password=password).first()
        if user:
            login_user(user, remember=True)
            return redirect(url_for('userfeed')) 
        else:
            flash('Incorrect username or password')
            return render_template('userlogin.html')
    

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("useregister.html")
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        first_name=request.form['first_name'] 
        last_name=request.form['last_name']
        email_id=request.form['email_id']
        user = User(username=username,
                    password=password, 
                    first_name=first_name, 
                    last_name=last_name,
                    email_id=email_id)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('userlogin'))

@app.route('/userfeed', methods = ['GET','POST'])
def userfeed():
    user_id = current_user.id
    category = Category.query.all()
    return render_template('userfeed.html', cards = category, user_id = user_id)

@app.route("/user_prod_display/<cat_id>", methods=["GET","POST"])
def user_prod_display(cat_id):
    p = Product.query.filter_by(c_id = cat_id).all()
    d={}
    d['cards']=p
    d['cat_id']=cat_id
    d['n']= True if len(p)>0 else False
    if request.method=="GET":
        return render_template('user_prod_display.html', cards = d)
    
@app.route("/buy_product/<prod_id>", methods = ['GET','POST'])
def buy_product(prod_id):
    p_id = Product.query.filter_by(id = prod_id).first()
    if not p_id:
        return "No such products."
    if request.method == 'GET':
        return render_template('buy.html', prod_id = prod_id)
    if request.method == 'POST':
        quantity = request.form['quantity']
        if int(quantity)>int(p_id.quantity):
            return ("<h1>YOU CAN'T BUY PRODUCTS MORE THAN THAT ARE IN THE STOCK.</h1>"
                    "<br>"
                    "<h2>Please check the catalog for the available stock </h2>")
        else:
            if int(p_id.quantity) > 0 and int(quantity) > 0:
                c_name = Category.query.filter_by(id = p_id.c_id).first()
                cart = Cart(user_id = current_user.id, quantity=quantity, c_id = p_id.c_id, c_name = c_name.c_name,
                             p_id = p_id.id, p_name = p_id.p_name, unit = p_id.unit ,price = p_id.price)
                db.session.add(cart)
                db.session.commit()
                return redirect(url_for("user_prod_display", cat_id = p_id.c_id))


@app.route('/cart', methods = ['GET','POST'])
def cart():
    user_id = current_user.id
    cart = Cart.query.filter_by(user_id = user_id).all()
    total = 0
    for c in cart:
        total += c.quantity * c.price
    if request.method == 'GET':
        return render_template('cart.html', items = cart, t = total, user_id = user_id )   
    
@app.route('/edit_cart/<user_id>/<cart_id>/<prod_id>', methods=["GET","POST"])
def cart_qty(user_id, cart_id, prod_id):
    c = Cart.query.filter_by(id = cart_id).first()
    u = current_user.id 
    p = Product.query.filter_by(id = prod_id).first()
    if request.method == "GET":
        return render_template('edit_qty.html', user_id = u, cart_id = c.id, prod_id = p.id)
    if request.method == "POST":
        temp = request.form['quantity']
        if int(temp) > p.quantity:
            return ("The available stock is" + str(p.quantity))
        else:
            c.quantity = temp
            db.session.commit()
            return redirect(url_for('cart'))

@app.route('/buy_products', methods = ["GET","POST"])
def buy():
    cart = Cart.query.all()
    user_id = current_user.id
    if request.method == "GET":
        for c in cart:
            p_id = Product.query.filter_by(id = c.p_id).first()
            if int(p_id.quantity) > 0 and int(c.quantity)<=int(p_id.quantity):
                    p_id.quantity -= int(c.quantity)
                    # c_name = Category.query.filter_by(id = p_id.c_id).first()
                    history = History(user_id = current_user.id, quantity=c.quantity, c_id = c.c_id, c_name = c.c_name,
                                p_id = c.p_id, p_name = c.p_name, unit = c.unit ,price = c.price)
                    db.session.add(history)
                    db.session.delete(c)
        db.session.commit()
        return render_template('bike.html')   
    else:
        return render_template('history.html', items = cart)

@app.route('/history/<user_id>', methods = ["GET","POST"])
def history(user_id):
    u_id = current_user.id
    hist = History.query.filter_by(user_id = u_id).all()
    print(hist)
    return render_template('history.html', user_id = u_id , items = hist)
    
@app.route('/search', methods=['GET'])
def search():
    search = request.args.get('search')
    string1 = f'%{search}%'
    product = Product.query.filter(( Product.p_name.ilike(string1))).all()
    return render_template('search.html', searches = product, search = search)


@app.route('/logout')
def logout():
    if "user" in session:
        session.pop("user")
        session.pop("cart")
    return redirect("/")


#________________________________________________________________________________________________________________    
if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)