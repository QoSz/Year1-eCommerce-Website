import hashlib
import os
import sqlite3

from flask import *
from werkzeug.utils import secure_filename

application = Flask(__name__)
application.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'jpeg', 'jpg', 'png', 'gif'}
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Reference Material to get python setup with sqlite33: (Hule 2021)

def getLoginDetails():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        if 'email' in session:
            loggedIn = True
            cur.execute("SELECT userId, firstName FROM users WHERE email = ?", (session['email'],))
            userId, firstName = cur.fetchone()
            cur.execute("SELECT count(productId) FROM kart WHERE userId = ?", (userId,))
            noOfItems = cur.fetchone()[0]
        else:
            loggedIn = False
            firstName = ''
            noOfItems = 0
    conn.close()
    return loggedIn, firstName, noOfItems


@application.route("/")
def root():
    loggedIn, firstName, noOfItems = getLoginDetails()
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock FROM products')
        itemData = cur.fetchall()
        cur.execute('SELECT categoryId, name FROM categories')
        categoryData = cur.fetchall()
    itemData = parse(itemData)
    return render_template('home.html', itemData=itemData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems,
                           categoryData=categoryData)


@application.route("/add")
def admin():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT categoryId, name FROM categories")
        categories = cur.fetchall()
    conn.close()
    return render_template('add.html', categories=categories)


# noinspection PyBroadException
@application.route("/addItem", methods=["GET", "POST"])
def addItem():
    global filename
    if request.method == "POST":
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        categoryId = int(request.form['category'])

        # Uploading image procedure
        image = request.files['image']
        if image:
            if allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(application.config['UPLOAD_FOLDER'], filename))
        imagename = filename
        with sqlite3.connect('database.db') as conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    '''INSERT INTO products (name, price, description, image, stock, categoryId) VALUES (?, ?, ?, ?, 
                    ?, ?)''',
                    (name, price, description, imagename, stock, categoryId))
                conn.commit()
                msg = "added successfully"
            except:
                msg = "error occurred"
                conn.rollback()
        conn.close()
        print(msg)
        return redirect(url_for('root'))


@application.route("/remove")
def remove():
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock FROM products')
        data = cur.fetchall()
    conn.close()
    return render_template('remove.html', data=data)


@application.route("/removeItem")
def removeItem():
    productId = request.args.get('productId')
    with sqlite3.connect('database.db') as conn:
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM products WHERE productID = ?', (productId,))
            conn.commit()
            msg = "Deleted successfully"
        except:
            conn.rollback()
            msg = "Error occurred"
    conn.close()
    print(msg)
    return redirect(url_for('root'))


@application.route("/displayCategory")
def displayCategory():
    loggedIn, firstName, noOfItems = getLoginDetails()
    categoryId = request.args.get("categoryId")
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT products.productId, products.name, products.price, products.image, categories.name FROM products, "
            "categories WHERE products.categoryId = categories.categoryId AND categories.categoryId = ?",
            (categoryId,))
        data = cur.fetchall()
    conn.close()
    categoryName = data[0][4]
    data = parse(data)
    return render_template('displayCategory.html', data=data, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems, categoryName=categoryName)


# Reference Material to hash passwords that have been entered: (Kinsley 2021)
# Reference Material to enter data into database: (SQLite Python: Inserting Data. 2021)
@application.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Parse form data
        password = request.form['password']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']

        with sqlite3.connect('database.db') as con:
            try:
                cur = con.cursor()
                cur.execute(
                    'INSERT INTO users (password, email, firstName, lastName, address1, address2, zipcode, city, '
                    'state, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (
                        hashlib.md5(password.encode()).hexdigest(), email, firstName, lastName, address1, address2,
                        zipcode,
                        city, state, country, phone))

                con.commit()

                msg = "Registered Successfully"
            except:
                con.rollback()
                msg = "Error occurred"
        con.close()
        return render_template("login.html", error=msg)


@application.route("/registerationForm")
def registrationForm():
    return render_template("register.html")


@application.route("/loginForm")
def loginForm():
    if 'email' not in session:
        return render_template('login.html', error='')
    else:
        return redirect(url_for('root'))


@application.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid Email / Password has been entered please try again'
            return render_template('login.html', error=error)


@application.route("/account/profile")
def profileHome():
    if 'email' in session:
        loggedIn, firstName, noOfItems = getLoginDetails()
        return render_template("profileHome.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)
    return redirect(url_for('root'))


@application.route("/account/profile/edit")
def editProfile():
    if 'email' in session:
        loggedIn, firstName, noOfItems = getLoginDetails()
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, "
                "phone FROM "
                "users WHERE email = ?",
                (session['email'],))
            profileData = cur.fetchone()
        conn.close()
        return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName,
                               noOfItems=noOfItems)
    return redirect(url_for('root'))


# Reference Material to hash passwords that have been entered: (Kinsley 2021)
@application.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' in session:
        if request.method == "POST":
            oldPassword = request.form['oldpassword']
            oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
            newPassword = request.form['newpassword']
            newPassword = hashlib.md5(newPassword.encode()).hexdigest()
            with sqlite3.connect('database.db') as conn:
                cur = conn.cursor()
                cur.execute("SELECT userId, password FROM users WHERE email = ?", (session['email'],))
                userId, password = cur.fetchone()
                if password == oldPassword:
                    try:
                        cur.execute("UPDATE users SET password = ? WHERE userId = ?", (newPassword, userId))
                        conn.commit()
                        msg = "Changed successfully"
                    except:
                        conn.rollback()
                        msg = "Failed"
                    return render_template("changePassword.html", msg=msg)
                else:
                    msg = "Wrong password"
            conn.close()
            return render_template("changePassword.html", msg=msg)
        else:
            return render_template("changePassword.html")
    return redirect(url_for('loginForm'))


@application.route("/updateProfile", methods=["GET", "POST"])
def updateProfile():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        with sqlite3.connect('database.db') as con:
            try:
                cur = con.cursor()
                cur.execute(
                    'UPDATE users SET firstName = ?, lastName = ?, address1 = ?, address2 = ?, zipcode = ?, city = ?, '
                    'state = ?, country = ?, phone = ? WHERE email = ?',
                    (firstName, lastName, address1, address2, zipcode, city, state, country, phone, email))

                con.commit()
                msg = "Saved Successfully"
            except:
                con.rollback()
                msg = "Error occurred"
        con.close()
        return redirect(url_for('editProfile'))


@application.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    productId = request.args.get('productId')
    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('SELECT productId, name, price, description, image, stock FROM products WHERE productId = ?',
                    (productId,))
        productData = cur.fetchone()
    conn.close()
    return render_template("productDescription.html", data=productData, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems)


@application.route("/addToCart")
def addToCart():
    if 'email' in session:
        productId = int(request.args.get('productId'))
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (session['email'],))
            userId = cur.fetchone()[0]
            try:
                cur.execute("INSERT INTO kart (userId, productId) VALUES (?, ?)", (userId, productId))
                conn.commit()
                msg = "Added successfully"
            except:
                conn.rollback()
                msg = "Error occurred"
        conn.close()
        return redirect(url_for('root'))
    else:
        return redirect(url_for('loginForm'))


@application.route("/addToWishlist")
def addToWishlist():
    if 'email' in session:
        productId = int(request.args.get('productId'))
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (session['email'],))
            userId = cur.fetchone()[0]
            try:
                cur.execute("INSERT INTO wishlists (userId, productId) VALUES (?, ?)", (userId, productId))
                conn.commit()
                msg = "Added successfully"
            except:
                conn.rollback()
                msg = "Error occurred"
        conn.close()
        return redirect(url_for('root'))
    else:
        return redirect(url_for('loginForm'))


@application.route("/cart")
def cart():
    if 'email' in session:
        loggedIn, firstName, noOfItems = getLoginDetails()
        email = session['email']
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
            userId = cur.fetchone()[0]
            cur.execute(
                "SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE "
                "products.productId = kart.productId AND kart.userId = ?",
                (userId,))
            products = cur.fetchall()
        totalPrice = 0
        for row in products:
            totalPrice += row[2]
        return render_template("cart.html", products=products, totalPrice=totalPrice, loggedIn=loggedIn,
                               firstName=firstName, noOfItems=noOfItems)
    return redirect(url_for('loginForm'))


@application.route("/wishlist")
def wishlist():
    if 'email' in session:
        loggedIn, firstName, noOfItems = getLoginDetails()
        email = session['email']
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
            userId = cur.fetchone()[0]
            cur.execute(
                "SELECT products.productId, products.name, products.price, products.image FROM products, wishlists "
                "WHERE "
                "products.productId = wishlists.productId AND wishlists.userId = ?",
                (userId,))
            products = cur.fetchall()
        totalPrice = 0
        for row in products:
            totalPrice += row[2]
        return render_template("wishlist.html", products=products, totalPrice=totalPrice, loggedIn=loggedIn,
                               firstName=firstName, noOfItems=noOfItems)
    return redirect(url_for('loginForm'))


@application.route("/payment")
def payment():
    return render_template("payment.html")


@application.route("/success")
def success():
    return render_template("success.html")


@application.route("/removeFromCart")
def removeFromCart():
    if 'email' in session:
        email = session['email']
        productId = int(request.args.get('productId'))
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
            userId = cur.fetchone()[0]
            try:
                cur.execute("DELETE FROM kart WHERE userId = ? AND productId = ?", (userId, productId))
                conn.commit()
                msg = "removed successfully"
            except:
                conn.rollback()
                msg = "error occurred"
        conn.close()
        return redirect(url_for('cart'))
        # return redirect(url_for('root'))
    return redirect(url_for('loginForm'))


@application.route("/removeFromWishlist")
def removeFromWishlist():
    if 'email' in session:
        email = session['email']
        productId = int(request.args.get('productId'))
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT userId FROM users WHERE email = ?", (email,))
            userId = cur.fetchone()[0]
            try:
                cur.execute("DELETE FROM wishlists WHERE userId = ? AND productId = ?", (userId, productId))
                conn.commit()
                msg = "removed successfully"
            except:
                conn.rollback()
                msg = "error occurred"
        conn.close()
        return redirect(url_for('wishlist'))
        # return redirect(url_for('root'))
    return redirect(url_for('loginForm'))


@application.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))


def is_valid(email, password):
    con = sqlite3.connect('database.db')
    cur = con.cursor()
    cur.execute('SELECT email, password FROM users')
    data = cur.fetchall()
    for row in data:
        if row[0] == email:
            if row[1] == hashlib.md5(password.encode()).hexdigest():
                return True
    return False


def allowed_file(filename):
    return not (not ('.' in filename) or not (filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS))


def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i < len(data):
                curr.append(data[i])
                i += 1
                continue
            break
        ans.append(curr)
    return ans


if __name__ == '__main__':
    application.run(debug=False)

# Reference Material

# Hule, V. 2021. Available at: https://pynative.com/python-sqlite/ [Accessed: 17 May 2021]. Kinsley, H. 2021. Python
# Programming Tutorials. Available at: https://pythonprogramming.net/password-hashing-flask-tutorial/ [Accessed: 17
# May 2021]. SQLite Python: Inserting Data. 2021. Available at: https://www.sqlitetutorial.net/sqlite-python/insert/
# [Accessed: 17 May 2021].
