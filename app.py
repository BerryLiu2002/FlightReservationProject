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




#Define a route to hello function
@app.route('/')
def home():
	return render_template('index.html')



app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
	app.run('127.0.0.1', 5000, debug = True)