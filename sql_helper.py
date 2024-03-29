import os
import dotenv
import dotenv
import pymysql.cursors
from datetime import datetime
from encrypt import encrypt_string
from itertools import chain

# load in environment variables
dotenv.load_dotenv()


conn = pymysql.connect(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT')),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    db=os.getenv('DB_DATABASE'),
    charset=os.getenv('DB_CHARSET'),
    cursorclass=pymysql.cursors.DictCursor)


cursor = conn.cursor()


def auth_user(username, password):
    password = encrypt_string(password)
    # authenticate user upon login (returns tuple (user firstname, user type) if successful, (None, None) otherwise)
    query = 'SELECT name FROM customers WHERE email = %s and password = %s'
    cursor.execute(query, (username, password))
    data = cursor.fetchone()
    if (data):  # if user is a customer
        return (data['name'].split()[0], 'customer')
    else:
        # check if user is an airline staff
        query = 'SELECT first_name FROM airlinestaff WHERE username = %s and password = %s'
        cursor.execute(query, (username, password))
        data = cursor.fetchone()
        if (data):
            return (data['first_name'], 'airlinestaff')
        else:  # user is not a customer or airline staff
            return (None, None)


def check_register_customer(data):
    name = data.get('name')
    email = data.get('email')
    password = encrypt_string(data.get('password'))
    building_num = data.get('building_num')
    street = data.get('street')
    city = data.get('city')
    state = data.get('state')
    phone = data.get('phone')
    passport_num = data.get('passport_num')
    passport_exp = data.get('passport_exp')
    passport_country = data.get('passport_country')
    date_of_birth = data.get('date_of_birth')
    query = 'INSERT INTO customers (name, email, password, building_num, street, city, state, phone_num, passport_num, passport_exp, passport_country, date_of_birth) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    try:
        cursor.execute(query, (name, email, password, building_num, street, city,
                       state, phone, passport_num, passport_exp, passport_country, date_of_birth))
        conn.commit()
        return True
    except pymysql.err.IntegrityError as e:
        # print('Error: ', e)
        return False


def check_register_airlinestaff(data):
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    username = data.get('username')
    password = encrypt_string(data.get('password'))
    date_of_birth = data.get('date_of_birth')
    airline_name = data.get('airline')
    query = 'INSERT INTO airlinestaff (first_name, last_name, username, password, date_of_birth, works_at) VALUES (%s, %s, %s, %s, %s, %s)'
    try:
        cursor.execute(query, (first_name, last_name, username,
                       password, date_of_birth, airline_name))
        conn.commit()
    except pymysql.err.IntegrityError as e:
        # print('Error: ', e)
        return False
    # insert phone numbers
    phone = data.get('phone')
    numbers = phone.split(',')
    numbers = [x.strip() for x in numbers]
    num_count = len(numbers)
    inserts = ", ".join(["(%s, %s)"]*num_count)
    query = 'INSERT INTO PhoneNumbers (username, phone_num) VALUES ' + inserts
    inputs = tuple(chain.from_iterable(zip([username]*num_count, numbers)))
    try:
        cursor.execute(query, inputs)
        conn.commit()
        return True
    except pymysql.err.IntegrityError as e:
        # print('Error: ', e)
        return False


def get_future_flights(email):
    query = "SELECT * FROM Flights NATURAL JOIN Tickets as F WHERE F.customer_email = %s and F.departure_time >= now() + INTERVAL 1 DAY;"
    cursor.execute(query, email)
    data = cursor.fetchall()
    return data


def get_past_flights(email):
    query = "SELECT * FROM Flights NATURAL JOIN Tickets as F WHERE F.customer_email = %s and F.departure_time < now() + INTERVAL 1 DAY;"
    cursor.execute(query, email)
    data = cursor.fetchall()
    return data


def get_ratable_flights(email):
    query = "SELECT * FROM (SELECT * FROM Tickets NATURAL join Flights WHERE Tickets.customer_email = %s) as X where CURRENT_TIMESTAMP > X.departure_time;"
    cursor.execute(query, email)
    data = cursor.fetchall()
    return data


def make_review(rating, comment, email, flight_num):
    query = "INSERT INTO REVIEWS (rating,comment,customer_email,flight_num) VALUES (%s,%s,%s,%s);"
    try:
        cursor.execute(query, (rating, comment, email, flight_num))
        conn.commit()
        return True
    except pymysql.err.IntegrityError as e:
        # print('Error: ', e)
        return False


def cancel_flight(id, departure_time, airline):
    query = "DELETE FROM TICKETS WHERE id = %s AND departure_time = %s AND airline = %s"
    try:
        cursor.execute(query, (id, departure_time, airline))
        conn.commit()
        # print('number of rows deleted', cursor.rowcount, id)
        return True
    except pymysql.err.IntegrityError as e:
        # print('Error: ', e)
        return False


def get_spending(email, args):
    query = """SELECT YEAR(f.departure_time) as Year, MONTHNAME(f.departure_time) as Month,
     CAST(SUM(f.sold_price) AS SIGNED) as Spent  FROM `Flights` NATURAL JOIN TICKETS as f """
    condition_list = []
    inputs = ()
    if email:
        condition_list.append('f.customer_email = %s')
        inputs += (email,)
    if args.get('start_date'):
        condition_list.append('Date(f.departure_time) >= %s')
        inputs += (args.get('start_date'),)
    if args.get('end_date'):
        condition_list.append('Date(f.departure_time) <= %s')
        inputs += (args.get('end_date'),)
    query += " WHERE " + " AND ".join(condition_list)
    query += "GROUP by f.departure_time"
    # print(args)
    # print(query)
    cursor.execute(query, inputs)
    data = cursor.fetchall()
    return data


def check_past(data):
    query = "SELECT Date(now())  > %s ;"
    cursor.execute(query, data.get('departure_time'))
    data = cursor.fetchall()
    return data


def get_filtered_flights(email, args):
    inputs = ()
    query = """SELECT flights.flight_num, Flights.airplane_id, Tickets.airline, Flights.departure_airport, Flights.arrival_airport,
                Flights.departure_time, Flights.arrival_time
                FROM Flights join Tickets on Flights.flight_num = Tickets.flight_num
            """
    condition_list = []

    if email:
        condition_list.append('Tickets.customer_email = %s')
    inputs += (email,)
    if args.get('start_date'):
        condition_list.append('Date(Tickets.departure_time) >= %s')
        inputs += (args.get('start_date'),)
    if args.get('end_date'):
        condition_list.append('Date(Tickets.departure_time) <= %s')
        inputs += (args.get('end_date'),)
    if args.get('departure'):
        condition_list.append('Flights.departure_airport = %s')
        inputs += (args.get('departure'),)
    if args.get('arrival'):
        condition_list.append('Flights.arrival_airport = %s')
        inputs += (args.get('arrival'),)
    # print("the args",args)
    if condition_list:
        query += " WHERE " + " AND ".join(condition_list)
    # print(query)
    cursor.execute(query, inputs)
    data = cursor.fetchall()
    # print(args)
    return data


def get_airports():
    query = 'SELECT DISTINCT name FROM airports'
    cursor.execute(query)
    data = cursor.fetchall()
    return data


def get_airport_cities():
    query = 'SELECT DISTINCT city FROM airports'
    cursor.execute(query)
    data = cursor.fetchall()
    # print(data)
    return data


def filter_future_flights(args):
    inputs = ()
    sql = """SELECT flights.flight_num, departure_airport, arrival_airport, departure_time, base_price, flights.airline, 
            num_seats - (SELECT COUNT(*) FROM tickets WHERE tickets.flight_num = flights.flight_num AND tickets.departure_time = flights.departure_time AND tickets.airline = flights.airline) 
            AS seats_left
            FROM Flights 
            LEFT JOIN Airplanes 
	        ON Flights.airplane_id = Airplanes.id"""
    condition_list = ["departure_time > NOW()"]
    if args.get('departure'):
        condition_list.append("departure_airport = %s")
        inputs += (args.get('departure'),)
    if args.get('arrival'):
        condition_list.append("arrival_airport = %s")
        inputs += (args.get('arrival'),)
    if args.get('departure_city'):
        condition_list.append(
            "departure_airport IN (SELECT name FROM airports WHERE city = %s)")
        inputs += (args.get('departure_city'),)
    if args.get('arrival_city'):
        condition_list.append(
            "arrival_airport IN (SELECT name FROM airports WHERE city = %s)")
        inputs += (args.get('arrival_city'),)
    if args.get('departure_date'):
        condition_list.append("DATE(departure_time) = %s")
        inputs += (args.get('departure_date'),)
    if condition_list:
        sql += " WHERE " + " AND ".join(condition_list)
    cursor.execute(sql, inputs)
    data = cursor.fetchall()
    # for each in data:
    #     each['departure_time'] = each['departure_time'].strftime("%m/%d/%Y %I:%M %p")
    # print(data)
    return data


def get_airlines():
    query = 'SELECT DISTINCT name FROM airlines'
    cursor.execute(query)
    data = cursor.fetchall()
    return data


def get_staff_airline(username):
    query = 'SELECT works_at FROM airlinestaff WHERE username = %s'
    cursor.execute(query, username)
    data = cursor.fetchone()
    return data['works_at']


def filter_status_flights(args):
    inputs = ()
    sql = "SELECT * FROM Flights WHERE airline = %s AND flight_num = %s AND departure_time = %s"
    departure_time = datetime.strptime(
        args.get('departure_time'), '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(sql, (args.get('airline'),
                   args.get('flight_num'), departure_time))
    data = cursor.fetchone()
    return data


def get_flight_details(airline, flight_num, departure_time):
    sql = """SELECT *
            FROM Flights f
            INNER JOIN Airports da
                ON f.departure_airport = da.name
            INNER JOIN Airports aa
                ON f.arrival_airport = aa.name
            WHERE airline = %s AND flight_num = %s AND departure_time = %s"""
    cursor.execute(sql, (airline, flight_num, departure_time))
    data = cursor.fetchone()
    data['departure_time'] = data['departure_time'].strftime(
        "%m/%d/%Y %I:%M %p")
    data['arrival_time'] = data['arrival_time'].strftime("%m/%d/%Y %I:%M %p")
    return data


def view_all_flights_staff(args, airline):
    inputs = (airline,)
    sql = "SELECT * FROM Flights WHERE airline = %s "
    condition_list = []
    if args.get('departure'):
        condition_list.append("flights.departure_airport = %s")
        inputs += (args.get('departure'),)
    if args.get('arrival'):
        condition_list.append("flights.arrival_airport = %s")
        inputs += (args.get('arrival'),)
    if args.get('departure_city'):
        condition_list.append("flights.departure_airport IN (SELECT departure_airport FROM Flights \
        INNER JOIN airports ON Flights.departure_airport = airports.name WHERE airports.city = %s)")
        inputs += (args.get('departure_city'),)
    if args.get('arrival_city'):
        condition_list.append("flights.arrival_airport IN (SELECT arrival_airport FROM Flights \
        INNER JOIN airports ON Flights.arrival_airport = airports.name WHERE airports.city = %s)")
        inputs += (args.get('arrival_city'),)
    if args.get('from_date'):
        condition_list.append("DATE(flights.departure_time) > %s")
        inputs += (args.get('from_date'),)
    if args.get('to_date'):
        condition_list.append("DATE(flights.departure_time) < %s")
        inputs += (args.get('to_date'),)
    if args.get('flight_num'):
        condition_list.append("flights.flight_num = %s")
        inputs += (args.get('flight_num'),)
    if not condition_list:
        condition_list.append("DATE(flights.departure_time) > CURDATE()")
        condition_list.append(
            "DATE(flights.departure_time) < (CURDATE() + INTERVAL 30 DAY)")
    sql += " AND " + " AND ".join(condition_list)
    # print(sql)
    cursor.execute(sql, inputs)
    data = cursor.fetchall()
    return data


def view_all_customers_staff(airline, flight_num, departure_time):
    query = """SELECT name, email, phone_num FROM customers INNER JOIN tickets ON customers.email = tickets.customer_email 
            WHERE tickets.airline = %s
            AND tickets.flight_num = %s
            AND tickets.departure_time = %s
    """
    cursor.execute(query, (airline, flight_num, departure_time))
    data = cursor.fetchall()
    return data


def view_ratings_comments(airline, flight_num, departure_time):
    query = """SELECT reviews.customer_email, reviews.rating, reviews.comment 
            FROM reviews INNER JOIN flights ON reviews.flight_num = flights.flight_num
            WHERE flights.airline = %s
            AND flights.flight_num = %s
            AND flights.departure_time = %s"""
    cursor.execute(query, (airline, flight_num, departure_time))
    data = cursor.fetchall()
    return data


def view_avg_rating(airline, flight_num, departure_time):
    query = """SELECT avg(reviews.rating) AS 'Average rating'
            FROM reviews INNER JOIN flights ON reviews.flight_num = flights.flight_num
            WHERE flights.airline = %s
            AND flights.flight_num = %s
            AND flights.departure_time = %s"""
    cursor.execute(query, (airline, flight_num, departure_time))
    data = cursor.fetchone()
    return data


def view_freq_customer(airline):
    create_view = "CREATE VIEW only_airline AS (SELECT customer_email FROM tickets WHERE airline = %s)"
    cursor.execute(create_view, airline)
    query = """SELECT customer_email, COUNT(*) AS frequency 
            FROM only_airline 
            GROUP BY customer_email 
            ORDER BY frequency DESC
            LIMIT 1"""
    cursor.execute(query)
    email = cursor.fetchone()
    drop_view = "DROP VIEW `only_airline`"
    cursor.execute(drop_view)
    query = """SELECT name FROM customers
            WHERE email = %s"""
    cursor.execute(query, email['customer_email'])
    name = cursor.fetchone()
    return email, name['name']


def view_tickets_sold(from_time, to_time, airline):
    query = """Select count(id) AS total_tickets_sold FROM tickets WHERE airline = %s
            AND departure_time >= %s AND departure_time < %s"""
    cursor.execute(query, (airline, from_time, to_time))
    data = cursor.fetchone()
    return data['total_tickets_sold']


def view_revenue(from_time, to_time, airline):
    query = """SELECT SUM(sold_price) as total_revenue FROM tickets WHERE airline = %s
            AND departure_time > %s AND departure_time < %s"""
    cursor.execute(query, (airline, from_time, to_time))
    data = cursor.fetchone()
    res = data['total_revenue']
    if res == None:
        res = 0
    return res


def all_customer_flights(email, airline):
    query = """SELECT flights.flight_num, flights.departure_time FROM flights 
    INNER JOIN tickets ON flights.flight_num = tickets.flight_num AND flights.departure_time = tickets.departure_time AND flights.airline = tickets.airline
    INNER JOIN customers ON customers.email = tickets.customer_email 
    WHERE customers.email = %s AND flights.airline = %s"""
    cursor.execute(query, (email, airline))
    data = cursor.fetchall()
    return data


def create_new_flights(data, airline):
    airplane_id = data.get('airplane_id')
    base_price = data.get('base_price')
    status = data.get('status')
    departure_airport = data.get('departure_airport')
    arrival_airport = data.get('arrival_airport')
    departure_time = data.get('departure_time')
    arrival_time = data.get('arrival_time')
    query = 'INSERT INTO Flights (airplane_id, base_price, status, departure_airport, arrival_airport, departure_time, arrival_time, airline) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'
    try:
        cursor.execute(query, (airplane_id, base_price, status, departure_airport,
                       arrival_airport, departure_time, arrival_time, airline))
        conn.commit()
    except pymysql.err.IntegrityError as e:
        # print('Error: ', e)
        return False
    return True, "Sucessfully added flight."


def add_airplane(data, airline):
    id = data.get('id')
    num_seats = data.get('num_seats')
    manufacturing_company = data.get('manufacturing_company')
    age = data.get('age')
    query = 'INSERT INTO airplanes (num_seats, manufacturing_company, age, airline) VALUES (%s, %s, %s, %s)'
    try:
        cursor.execute(query, (num_seats, manufacturing_company, age, airline))
        conn.commit()
    except pymysql.err.IntegrityError as e:
        # print('Error: ', e)
        return False
    return True, "Sucessfully added plane."


def staff_view_airplane(airline):
    query = 'SELECT * FROM airplanes WHERE airline = %s'
    cursor.execute(query, airline)
    data = cursor.fetchall()
    return data


def add_airport(data):
    name = data.get('name')
    city = data.get('city')
    country = data.get('country')
    type = data.get('type')
    query = 'INSERT INTO airports(name, city, country, type) VALUES (%s, %s, %s, %s)'
    try:
        cursor.execute(query, (name, city, country, type))
        conn.commit()
    except pymysql.err.IntegrityError as e:
        # print('Error: ', e)
        return False
    return True, "Sucessfully added airport."


def change_flight_status(data):
    status = data.get('status')
    airline = data.get('airline')
    flight_num = data.get('flight_num')
    departure_time = data.get('departure_time')
    query = 'UPDATE flights SET status = %s WHERE airline = %s AND flight_num = %s AND DATE(departure_time) = %s'
    try:
        cursor.execute(query, (status, airline, flight_num, departure_time))
        conn.commit()
    except pymysql.err.IntegrityError as e:
        # print('Error: ', e)
        return False
    return True, "Sucessfully updated status"


def book_flight_ticket(email, flight_num, departure_time, airline, form):
    # make sure email is a customer
    query = 'SELECT * FROM customers WHERE email = %s'
    cursor.execute(query, (email))
    data = cursor.fetchone()
    if data is None:
        return False, 'Only customers can book flights. Please login as a customer.'
    # make sure flight still has seats remaining
    query = 'SELECT base_price, num_seats> (SELECT COUNT(*) FROM tickets AS seats_left WHERE flight_num = %s AND departure_time = %s AND airline = %s) AS is_seating FROM flights INNER JOIN airplanes ON flights.airplane_id = airplanes.id WHERE flight_num = %s AND departure_time = %s AND flights.airline = %s'
    cursor.execute(query, (flight_num, departure_time, airline,
                   flight_num, departure_time, airline))
    data = cursor.fetchone()
    # print(data)
    sold_price = data.get('base_price')
    is_seating = data.get('is_seating')
    if not is_seating:
        return False, 'No seats remaining on this flight.'
    else:
        query = 'INSERT INTO tickets (sold_price, card_type, card_num, name_on_card, exp_date,customer_email, flight_num, departure_time, airline) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        try:
            cursor.execute(query, (sold_price, form['card_type'], form['card_num'],
                           form['name_on_card'], form['exp_date'], email, flight_num, departure_time, airline))
            conn.commit()
            return True, 'Flight booked successfully.'
        except pymysql.err.IntegrityError as e:
            print('Error: ', e)
            return False, 'Error booking flight.'
