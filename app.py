from flask import Flask, render_template, request, session, url_for, redirect, jsonify, flash
from sql_helper import *
import _json
#Initialize the app from Flask
app = Flask(__name__)

#Define a route to hello function
@app.route('/')
def home():
    print(session)
    return render_template('index.html', session=session)

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
                return render_template('register_customer.html', error='    ')
        else: # request.form.get('reg_type') == 'airlinestaff'
            status = check_register_airlinestaff(request.form)
            if status:
                return render_template('register_airline_staff.html', success='You have successfully registered!')
            else:
                return render_template('register_airline_staff.html', error='There was an error in registering, please try again!')

@app.route('/purchased', methods=['GET', 'POST'])
def purchased_flights():
    if request.method == 'GET':
        data = get_flights(session.get('username'))
        # print(data[0]['id'])
        return render_template('purchased.html', data=data, session=session)

@app.route('/cancel', methods=['POST'])
def cancel_trip():
    id = request.form.get('id')
    if cancel_flight(id):
        data = get_flights(session.get('username'))
        print(data)
        return redirect('/purchased')

@app.route('/ratings', methods = ['GET', 'POST'])
def rate():
    if request.method == 'GET':
        data = get_ratable_flights(session.get('username'))
        return render_template('ratings.html', data=data, session=session)
    

@app.route('/rating-form', methods = ['GET', 'POST'])
def form():
    if request.method == 'GET':
        print(request.form.get('flight_num'))
        return render_template('rating-form.html', session=session)
    if request.method == 'POST':
        rating = request.form.get('stars')
        comment = request.form.get('comment')
        email = session.get('username')
        flight_num = request.form.get('flight_num')
        print(rating, comment, email, flight_num)
        if make_review(rating, comment, email, flight_num):
            return render_template('ratings.html',session=session)
        return redirect('/purchased')

@app.route('/future_flights', methods=['GET'])
def future_flights():
    if request.method == 'GET':
        airports= get_airports()
        cities = get_airport_cities()
        flights = filter_future_flights(request.args) if request.args else []
        error = 'No flights found with your specifications' if 'departure_date' in request.args and not flights else None
        return render_template('future_flights.html', session=session, airports=airports, cities=cities, flights=flights, error=error)

@app.route('/flight_status', methods=['GET'])
def flight_status():
    if request.method == 'GET':
        airlines = get_airlines()
        if not request.args:
            return render_template('flight_status.html', session=session, airlines=airlines)
        else:
            flight = filter_status_flights(request.args)
            error = 'No flights found with your specifications' if not flight else None
            if error:
                return render_template('flight_status.html', session=session, airlines=airlines, error=error)
            else:
                return redirect(url_for('flight_details', flight=flight))

@app.route('/flight_details/<flight>', methods=['GET'])
def flight_details(flight):
    if request.method == 'GET':
        # flight = get_flight_details(request.args.get('flight_id'))
        return render_template('flight_details.html', session=session, flight=flight)

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run(debug = True)