#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port=3306,          
                       user='root',
                       password='',
                       db='FlightReservation',
                       charset='utf8',
                       cursorclass=pymysql.cursors.DictCursor)

cursor = conn.cursor()

#Define a route to hello function
@app.route('/')
def home():
    if not session.get('username'):
        return render_template('index.html', username=None, name=None)
    else:
        # check if user is customer or admin
        # render appropriate page

        return render_template('index.html', username=session.get('username'), name=session.get('name'))

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
        # check if user is a customer
        query = 'SELECT name FROM customers WHERE email = %s and password = %s'
        cursor.execute(query, (username, password))
        data = cursor.fetchone()
        error = None
        if(data): # if user is a customer
            session['username'] = username
            session['name'] = data['name'].split()[0]
            return redirect(url_for('home'))
        else:
            # check if user is an airline staff
            query = 'SELECT first_name FROM airlinestaff WHERE username = %s and password = %s'
            cursor.execute(query, (username, password))
            data = cursor.fetchone()
            if (data):
                session['username'] = username
                session['name'] = data['first_name']
                return redirect(url_for('home'))
            else: # user is not a customer or airline staff
                error = 'Invalid username or password. Please try again!'
                return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)