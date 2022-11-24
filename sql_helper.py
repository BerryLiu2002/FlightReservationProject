import os, dotenv
import pymysql.cursors

# load in environment variables
dotenv.load_dotenv()

# conn = pymysql.connect(host='localhost',
#                        port=3306,          
#                        user='root',
#                        password='',
#                        db='FlightReservation',
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

def staff_default_view_flights():
    pass

def staff_filtered_view_flights(date_range, sorc, dest):
    pass



