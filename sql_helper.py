import os, dotenv
import dotenv
import pymysql.cursors

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

def get_flights(email):
    query = "SELECT * FROM TICKETS WHERE customer_email = %s"
    cursor.execute(query, email)
    data = cursor.fetchall()
    return data
    

def cancel_flight(id):
    query = "DELETE FROM TICKETS WHERE id = %s"
    try:
        cursor.execute(query, id)
        conn.commit()
        print('number of rows deleted', cursor.rowcount, id)
        return True
    except pymysql.err.IntegrityError as e:
        print('Error: ', e)
        return False

def staff_default_view_flights():
    pass

def staff_filtered_view_flights(date_range, sorc, dest):
    pass

def get_airports():
    query = 'SELECT DISTINCT name FROM airports'
    cursor.execute(query)
    data = cursor.fetchall()
    return data

def get_airport_cities():
    query = 'SELECT DISTINCT city FROM airports'
    cursor.execute(query)
    data = cursor.fetchall()
    print(data)
    return data

def get_filtered_flights(args):
    inputs = ()
    sql = "SELECT * FROM flights"
    condition_list = []
    if args.get('departure'):
        condition_list.append("departure_airport = %s")
        inputs += (args.get('departure'),)
    if args.get('arrival'):
        condition_list.append("arrival_airport = %s")
        inputs += (args.get('arrival'),)
    if args.get('departure_city'):
        condition_list.append("departure_airport IN (SELECT name FROM airports WHERE city = %s)")
        inputs += (args.get('departure_city'),)
    if args.get('arrival_city'):
        condition_list.append("arrival_airport IN (SELECT name FROM airports WHERE city = %s)")
        inputs += (args.get('arrival_city'),)
    if args.get('departure_date'):
        condition_list.append("departure_time = %s")
        inputs += (args.get('departure_date'),)
    if condition_list:
        sql += " WHERE " + " AND ".join(condition_list)
    cursor.execute(sql, inputs)
    data = cursor.fetchall()
    for each in data:
        each['departure_time'] = each['departure_time'].strftime("%Y-%m-%d")
        each['arrival_time'] = each['arrival_time'].strftime("%Y-%m-%d")
    print(data)
    return data
