from flask import Flask, render_template, request, session, url_for, redirect, jsonify, flash
from sql_helper import *
import _json
from encrypt import encrypt_string
from datetime import date
from dateutil.relativedelta import relativedelta
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
                return render_template('register_customer.html', error='There was an error in registering, please try again!')
        else: # request.form.get('reg_type') == 'airlinestaff'
            status = check_register_airlinestaff(request.form)
            if status:
                return render_template('register_airline_staff.html', success='You have successfully registered!')
            else:
                return render_template('register_airline_staff.html', error='There was an error in registering, please try again!')

@app.route('/purchased', methods=['GET', 'POST'])
def purchased_flights():
    if request.method == 'GET':
        data = get_future_flights(session.get('username'))
        data2 = get_past_flights(session.get('username'))
        airports = get_airports()
        return render_template('purchased.html', future_flights=data, airports = airports, session=session, past_flights = data2, default = False)

@app.route('/filtered-flights', methods = ['GET'])
def get_filtered():
    if request.method == 'GET':
        past_flights = []
        future_flights = []
        airports = get_airports()
        data = get_filtered_flights(session.get('username'),request.args.to_dict())
        for flight in data:
            if check_past(flight):
                past_flights.append(flight)
            else:
                future_flights.append(flight)
        return render_template('purchased.html', airports = airports, future_flights = future_flights, past_flights = past_flights, session=session, default = False)

@app.route('/spending', methods=['GET', 'POST'])
def spending():
    if request.method=='GET':
        data = get_spending(session.get('username'), request.args.to_dict())
        return render_template('spending.html', session=session, data=data)
    if request.method=='POST':
        data = get_spending(session.get('username'), request.args.to_dict())
        return render_template('spending.html', session=session, data=data)

@app.route('/cancel', methods=['POST'])
def cancel_trip():
    id = request.form.get('id')
    if cancel_flight(id):
        data = get_past_flights(session.get('username'))
        print(data)
        return redirect('/purchased')

@app.route('/ratings', methods = ['GET', 'POST'])
def rate():
    if request.method == 'GET':
        data = get_ratable_flights(session.get('username'))
        return render_template('ratings.html', data=data, session=session)

@app.route('/rating-form/<flight_num>', methods = ['GET', 'POST'])
def form(flight_num):
    if request.method == 'GET':
        return render_template('rating-form.html', data = flight_num , session=session)
    if request.method == 'POST':
        rating = request.form.get('stars')
        comment = request.form.get('comment')
        email = session.get('username')
        print(rating, comment, email, flight_num)
        if make_review(rating, comment, email, flight_num):
            return render_template('rating-form.html',session=session)
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

@app.route('/book/<flight_num>/<departure_time>/<airline>', methods=['GET', 'POST'])
def book_flight(flight_num, departure_time, airline):
    flight = get_flight_details(airline, flight_num, departure_time)
    if request.method == 'GET':
        return render_template('book_flight.html', session=session, flight=flight, flight_num=flight_num, departure_time=departure_time, airline=airline)
    if request.method == 'POST':
        if not session.get('username', None):
            return render_template('book_flight.html', session=session, flight=flight, flight_num=flight_num, departure_time=departure_time, airline=airline, error="You must be logged in as a customer to book a flight")
        print(request.form)
        success, message = book_flight_ticket(session.get('username'), flight_num, departure_time, airline, request.form)
        if success:
            return render_template('book_flight.html', session=session, flight=flight, flight_num=flight_num, departure_time=departure_time, airline=airline, success=message)
        else:
            return render_template('book_flight.html', session=session, flight=flight, flight_num=flight_num, departure_time=departure_time, airline=airline, error=message)

@app.route('/view_flight_staff', methods=['GET', 'POST'])
def view_flight_staff():
    if request.method == 'GET':
        if session.get('user_type') != 'airlinestaff':
            error = "Only an airline staff can access this page"
            return render_template('base.html', session=session, error=error)        
        airline = get_staff_airline(session.get('username'))
        airports= get_airports()
        cities = get_airport_cities()
        flights_to = view_all_flights_staff(request.args, airline) if request.args else []
        error = 'No flights found with your specifications' if 'departure_date' in request.args and not flights_to else None
        return render_template('view_flight_staff.html', session=session, airline = airline, airports=airports, cities=cities, flights_to=flights_to, error=error)
    if request.method == 'POST':
        airline = get_staff_airline(session.get('username'))
        airports= get_airports()
        cities = get_airport_cities()
        update_status = change_flight_status(request.form)
        flights_to = view_all_flights_staff(request.form, airline)
        if update_status[0]:
            return render_template('view_flight_staff.html', session = session, update_success = update_status[1], flights_to = flights_to, 
            airline = airline, airports = airports, cities = cities)
        else:
            return render_template('view_flight_staff.html', session = session, update_error = "There's a problem with changing flight status", 
            flights_to = flights_to, airline = airline, airports = airports, cities = cities)


@app.route('/view_flight_staff/flight_insights/<airline>/<flight_num>/<departure_time>', methods=['GET'])
def flight_insights(airline, flight_num, departure_time):
    if request.method == 'GET':
        if session.get('user_type') != 'airlinestaff':
            error = "Only an airline staff can access this page"
            return render_template('base.html', session=session, error=error)       
        flight_customers = view_all_customers_staff(airline, flight_num, departure_time)
        all_reviews = view_ratings_comments(airline, flight_num, departure_time)
        avg_rating = view_avg_rating(airline, flight_num, departure_time)
        return render_template('flight_insights.html', session = session, flight_customers = flight_customers, all_reviews = all_reviews, avg_rating = avg_rating['Average rating'])
    
@app.route('/view_reports', methods=['GET'])
def view_reports():
    if request.method == 'GET':
        if session.get('user_type') != 'airlinestaff':
            error = "Only an airline staff can access this page"
            return render_template('base.html', session=session, error=error) 
        airline = get_staff_airline(session.get('username'))
        most_freq_email, most_freq_name = view_freq_customer(airline)
        if request.args.get('sold_from_date'):
            total_tickets, year_month = tickets_sold(request.args, airline)
            to_iter = len(year_month)
            return render_template('view_reports.html', session = session, most_freq_email=most_freq_email['customer_email'], most_freq_name=most_freq_name, 
            airline = airline, total_tickets = total_tickets, year_month = year_month, to_iter=to_iter)
        elif request.args.get('revenue_from_date'):
            total_revenue, year_month = revenue(request.args, airline)
            to_iter = len(year_month)
            return render_template('view_reports.html', session = session, most_freq_email=most_freq_email['customer_email'], most_freq_name=most_freq_name, 
            airline = airline, total_revenue = total_revenue, year_month = year_month, to_iter=to_iter) 
        return render_template('view_reports.html', session = session, most_freq_email=most_freq_email['customer_email'], most_freq_name=most_freq_name, 
        airline = airline)

def tickets_sold(data, airline):
    from_date = data.get('sold_from_date')
    to_date = data.get('sold_to_date')
    from_date_lst = from_date.split('-')
    to_date_lst = to_date.split('-')
    date_dif = (int(to_date_lst[0])-int(from_date_lst[0]), int(to_date_lst[1])-int(from_date_lst[1]))
    month_iter = date_dif[0]*12 + date_dif[1]
    date_res = []
    res = []
    if month_iter > 0:
        for i in range(month_iter+1):
            date_res.append(from_date)
            datetime_object = datetime.strptime(from_date, '%Y-%m')
            date_next_month = datetime_object + relativedelta(months=1)
            sql_from = datetime_object.strftime('%Y-%m-%d %H:%M:%S')
            sql_to = date_next_month.strftime('%Y-%m-%d %H:%M:%S')
            res.append(view_tickets_sold(sql_from, sql_to, airline))
            from_date = date_next_month.strftime('%Y-%m')
    else:
        date_res.append(from_date)
        datetime_object = datetime.strptime(from_date, '%Y-%m')
        date_next_month = datetime_object + relativedelta(months=1)
        sql_from = datetime_object.strftime('%Y-%m-%d %H:%M:%S')
        sql_to = date_next_month.strftime('%Y-%m-%d %H:%M:%S')
        res.append(view_tickets_sold(sql_from, sql_to, airline))
        from_date = date_next_month.strftime('%Y-%m')
    res.append(sum(res))

    return res, date_res

def revenue(data, airline):
    from_date = data.get('revenue_from_date')
    to_date = data.get('revenue_to_date')
    from_date_lst = from_date.split('-')
    to_date_lst = to_date.split('-')
    date_dif = (int(to_date_lst[0])-int(from_date_lst[0]), int(to_date_lst[1])-int(from_date_lst[1]))
    month_iter = date_dif[0]*12 + date_dif[1]
    date_res = []
    res = []
    if month_iter > 0:
        for i in range(month_iter+1):
            date_res.append(from_date)
            datetime_object = datetime.strptime(from_date, '%Y-%m')
            date_next_month = datetime_object + relativedelta(months=1)
            sql_from = datetime_object.strftime('%Y-%m-%d %H:%M:%S')
            sql_to = date_next_month.strftime('%Y-%m-%d %H:%M:%S')
            res.append(view_revenue(sql_from, sql_to, airline))
            from_date = date_next_month.strftime('%Y-%m')
    else:
        date_res.append(from_date)
        datetime_object = datetime.strptime(from_date, '%Y-%m')
        date_next_month = datetime_object + relativedelta(months=1)
        sql_from = datetime_object.strftime('%Y-%m-%d %H:%M:%S')
        sql_to = date_next_month.strftime('%Y-%m-%d %H:%M:%S')
        res.append(view_revenue(sql_from, sql_to, airline))
        from_date = date_next_month.strftime('%Y-%m')      
    res.append(sum(res))

    return res, date_res


@app.route('/view_reports/freq_customer_flights/<most_freq_email>', methods=['GET'])
def freq_customer_flights(most_freq_email):
    if request.method == 'GET':
        if session.get('user_type') != 'airlinestaff':
            error = "Only an airline staff can access this page"
            return render_template('base.html', session=session, error=error)
        airline = get_staff_airline(session.get('username'))
        all_flights = all_customer_flights(most_freq_email, airline)
    return render_template('freq_customer_flights.html', session=session, all_flights = all_flights, airline = airline)


@app.route('/update_system', methods=['GET','POST'])
def update_system():
    airports= get_airports()
    airline = get_staff_airline(session.get('username')) 
    if request.method == 'GET':
        if session.get('user_type') != 'airlinestaff':
            error = "Only an airline staff can access this page"
            return render_template('base.html', session=session, error=error)
        return render_template('update_system.html', session=session, airports = airports, airline = airline)
    if request.method == 'POST': 
        if len(request.form) == 7:
            status = create_new_flights(request.form, airline)
            if status[0]:
                return render_template('update_system.html', session = session, success = status[1], airports = airports, airline = airline)
            else:
                return render_template('update_system.html', session = session, error = "There's a problem with creating the flight", airports = airports, airline = airline)
        elif len(request.form) == 3:
            status = add_airplane(request.form, airline)
            if status[0]:
                return render_template('update_system.html', session = session, success = status[1], airports = airports, airline = airline)
            else:
                return render_template('update_system.html', session = session, error = "There's a problem with adding the plane", airports = airports, airline = airline)
        elif len(request.form) == 4:
            status = add_airport(request.form)
            if status[0]:
                return render_template('update_system.html', session = session, success = status[1], airports = airports, airline = airline)
            else:
                return render_template('update_system.html', session = session, error = "There's a problem with adding the airport", airports = airports, airline = airline)


@app.route('/update_system/view_airplanes', methods=['GET'])
def view_airplanes():
    if request.method == 'GET':
        if session.get('user_type') != 'airlinestaff':
            error = "Only an airline staff can access this page"
            return render_template('base.html', session=session, error=error)
        airline = get_staff_airline(session.get('username'))
        all_airplanes = staff_view_airplane(airline)
    return render_template('view_airplanes.html', session=session, all_airplanes = all_airplanes, airline=airline)


app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run(debug = True)