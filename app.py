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
        print(data[0]['id'])
        return render_template('purchased.html', data=data, session=session)

@app.route('/cancel', methods=['POST'])
def cancel_trip():
    id = request.form.get('id')
    if cancel_flight(id):
        data = get_flights(session.get('username'))
        print(data)
        return redirect('/purchased')
        
@app.route('/future_flights', methods=['GET'])
def future_flights():
    if request.method == 'GET':
        airports= get_airports()
        cities = get_airport_cities()
        flights_to = filter_future_flights(request.args) if request.args else []
        if request.args.get('return_date'): # if return date is specified swap origin and destination, change departure date and run query again
            ret_args = request.args.to_dict()
            print(ret_args)
            ret_args['departure_date'] = ret_args['return_date']
            ret_args['arrival'], ret_args['departure'] = ret_args['departure'], ret_args['arrival']
        flights_back = filter_future_flights(ret_args) if request.args.get('return_date') else []
        error = 'No flights found with your specifications' if 'departure_date' in request.args and not flights_to else None
        return render_template('future_flights.html', session=session, airports=airports, cities=cities, flights_to=flights_to, flights_back=flights_back, error=error)

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
                return redirect(url_for('flight_details', airline=flight['airline'], flight_num=flight['flight_num'], departure_time=flight['departure_time'], arrival_time=flight['arrival_time']))

@app.route('/flight_details/<airline>/<flight_num>/<departure_time>', methods=['GET'])
def flight_details(airline, flight_num, departure_time):
    if request.method == 'GET':
        flight = get_flight_details(airline, flight_num, departure_time)
        print(flight)
        return render_template('flight_details.html', session=session, flight=flight)

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run(debug = True)