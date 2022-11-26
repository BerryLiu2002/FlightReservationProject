from flask import Flask, render_template, request, session, url_for, redirect
from sql_helper import *

#Initialize the app from Flask
app = Flask(__name__)

#Define a route to hello function
@app.route('/')
def home():
    return render_template('index.html', username=session.get('username'), name=session.get('name'), usertype = session.get('usertype'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('username', None): # check if the user is already logged in
            return redirect(url_for('home'))
        else:
            return render_template('login.html')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        f_name, user_type = auth_user(username, password)
        if f_name or user_type:
            session['username'] = username
            session['name'] = f_name
            session['user_type'] = user_type
            # different homepage for customer
            if user_type == 'customer':
                return redirect(url_for('customer_home'))
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials, please try again!')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('name', None)
    session.pop('user_type', None)
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if request.args.get('reg_type') == 'customer':
            return render_template('register_customer.html')
        else: # request.args.get('reg_type') == 'airlinestaff'
            return render_template('register_airline_staff.html')
    if request.method == 'POST':
        if request.form.get('reg_type') == 'customer':
            status = check_register_customer(request.form)
            if status:
                return render_template('register_customer.html', success='You have successfully registered!')
            else:
                return render_template('register_customer.html', error='There was an error in registering, please try again!')
        else: # request.form.get('reg_type') == 'airlinestaff'
            status = check_register_airlinestaff(request.form)
            if status:
                return render_template('register_airline_staff.html', success='You have successfully registered!')
            else:
                return render_template('register_airline_staff.html', error='There was an error in registering, please try again!')

@app.route('/customer')
def customer_home():
    return render_template('customer_homepage.html', username=session.get('username'), name=session.get('name'), usertype = session.get('usertype'))

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 4000, debug = True)