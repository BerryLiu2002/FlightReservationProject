import os, dotenv
import pymysql.cursors

# load in environment variables
dotenv.load_dotenv()

# conn = pymysql.connect(host='localhost',
#                        port=3306,          
#                        user='root',
#                        password='',
#                        db='flight_reservation_prj',
#                        charset='utf8',
#                        cursorclass=pymysql.cursors.DictCursor)

conn = pymysql.connect(host=os.getenv('DB_HOST'),
                       port=int(os.getenv('DB_PORT')),          
                       user=os.getenv('DB_USER'),
                       password=os.getenv('DB_PASSWORD'),
                       db=os.getenv('DB_DATABASE'),
                       charset=os.getenv('DB_CHARSET'),
                       cursorclass=pymysql.cursors.DictCursor)



cursor = conn.cursor()

def auth_user(username, password):
    # authenticate user upon login (returns tuple (user firstname, user type) if successful, (None, None) otherwise)
    query = 'SELECT name FROM customers WHERE email = %s and password = %s'
    cursor.execute(query, (username, password))
    data = cursor.fetchone()
    if(data): # if user is a customer
        return (data['name'].split()[0], 'customer')
    else:
        # check if user is an airline staff
        query = 'SELECT first_name FROM airlinestaff WHERE username = %s and password = %s'
        cursor.execute(query, (username, password))
        data = cursor.fetchone()
        if (data):
            return (data['first_name'], 'airlinestaff')
        else: # user is not a customer or airline staff
            return (None,None)

def check_register_customer(data):
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
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
        cursor.execute(query, (name, email, password, building_num, street, city, state, phone, passport_num, passport_exp, passport_country, date_of_birth))
        conn.commit()
        return True
    except pymysql.err.IntegrityError as e:
        print('Error: ', e)
        return False
        
def check_register_airlinestaff(data):
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    username = data.get('username')
    password = data.get('password')
    date_of_birth = data.get('date_of_birth')
    airline_name = data.get('airline')
    query = 'INSERT INTO airlinestaff (first_name, last_name, username, password, date_of_birth, works_at) VALUES (%s, %s, %s, %s, %s, %s)'
    try:
        cursor.execute(query, (first_name, last_name, username, password, date_of_birth, airline_name))
        conn.commit()
    except pymysql.err.IntegrityError as e:
        print('Error: ', e)
        return False
    # insert phone numbers
    phone = data.get('phone')
    query = 'INSERT INTO PhoneNumbers (phone_num, username) VALUES (%s, %s)'
    try:
        cursor.execute(query, (phone, username))
        conn.commit()
        return True
    except pymysql.err.IntegrityError as e:
        print('Error: ', e)
        return False

def view_all_flights_staff(data):
    airline = data.get('airline')
    departure_time = data.get('departure_time')
    departure_airport = data.get('departure_airport')
    arrival_airport = data.get('arrival_airport')
    query = 'SELECT * FROM flights, airplanes \
WHERE airplanes.airline = %s \
AND flights.departure_time > %s AND flights.departure_time < %s \
AND flights.departure_airport = %s AND flights.arrival_airport = %s'
    cursor.execute(query, (airline, departure_time, departure_time, departure_airport, arrival_airport))
    data = cursor.fetchone() # fetchall
    return data # What will data be?

def view_all_customers_staff(data):
    flight_num = data.get('flight_num')
    query = 'SELECT name FROM customers INNER JOIN tickets ON customers.email = tickets.customer_email \
WHERE tickets.flight_num = %s;'
    cursor.execute(query, (flight_num))
    data = cursor.fetchone()
    return data

def view_ratings_comments(data): # How to fetch data from 2 queires
    flight_num = data.get('flight_num')
    query = "SELECT avg(rating) AS 'Average rating' FROM reviews \
WHERE flight_num = %s;"
    query = "SELECT rating, comment FROM reviews \
WHERE flight_num = %s;"
    cursor.execute(query, (flight_num))
    data = cursor.fetchone() # Gets all possible result
    return data

def view_freq_customer(data):
    query = "SELECT email FROM tickets \
WHERE COUNT(email) = \
(SELECT MAX(COUNT(email)) FROM tickets)"
    cursor.execute(query)
    data = cursor.fetchone()
    return data

def view_report(data):
    departure_time = data.get('departure_time')   
    query = "Select count(id) AS total_tickets_sold FROM Tickets WHERE id = \
(SELECT tickets.id FROM tickets JOIN fLights \
ON tickets.flight_num = flights.flight_num \
WHERE flights.departure_time > %s AND flights.departure_time < %s)"
    cursor.execute(query, (departure_time, departure_time))
    data = cursor.fetchone()
    return data

def view_revenue(data):
    departure_time = data.get('departure_time')
    query = "Select sum(sold_price) AS total_revenue FROM Tickets WHERE id = \
(SELECT tickets.id FROM tickets JOIN flights \
ON tickets.flight_num = flights.flight_num \
WHERE flights.departure_time > %s AND flights.departure_time < %s)"
    cursor.execute(query, (departure_time, departure_time))
    data = cursor.fetchone()
    return data