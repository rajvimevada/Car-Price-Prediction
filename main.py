from flask import Flask, render_template, request, redirect, session, flash
# import mysql.connector 
from flask_mysqldb import MySQL
import os
from flask_cors import CORS, cross_origin
import pickle
import pandas as pd
import numpy as np
import re

app=Flask(__name__)
app.secret_key=os.urandom(24)

name_regex = r'\A[\w\-\.]{3,}\Z'
password_regex = r'[A-Za-z0-9@#$%^&+=]{6,}'
email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

cors = CORS(app)
model = pickle.load(open('LinearRegressionModel.pkl', 'rb'))
car = pd.read_csv('Cleaned_Car_data.csv')

# conn=mysql.connector.connect(host="localhost", username="root", password="", database="cpp")
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'cpp'

# cursor=conn.cursor()
mysql = MySQL(app)
with app.app_context():
    cursor = mysql.connection.cursor()


@app.route('/')
def login():
    return render_template('login.html')

@app.route('/register')
def about():
    return render_template('register.html')


@app.route('/home')
def home():
    if 'user_id' in session:
        companies = sorted(car['company'].unique())
        car_models = sorted(car['name'].unique())
        year = sorted(car['year'].unique(), reverse=True)
        fuel_type = car['fuel_type'].unique()

        companies.insert(0, 'Select Company')
        
        return render_template('home.html', companies=companies, car_models=car_models, years=year, fuel_types=fuel_type)

    else:
        return redirect('/')

@app.route('/login_validation', methods=['POST'])
def login_validation():
    error=None
    email=request.form.get('email')
    password=request.form.get('password')

    cursor = mysql.connection.cursor()
    cursor.execute("""SELECT * from `users` WHERE `email` LIKE '{}' AND `password` LIKE '{}'""" .format(email, password))
    mysql.connection.commit()
    users=cursor.fetchall()
    if(len(users)>0):
        session['user_id']=users[0][0]
        companies = sorted(car['company'].unique())
        car_models = sorted(car['name'].unique())
        year = sorted(car['year'].unique(), reverse=True)
        fuel_type = car['fuel_type'].unique()

        companies.insert(0, 'Select Company')
        
        return render_template('home.html', companies=companies, car_models=car_models, years=year, fuel_types=fuel_type)
    else:
        flash('Invalid Details')
        return render_template('login.html')
    return users
    # return "The Email is {} and the password is {}".format(email, password)


@app.route('/predict', methods=['POST'])
@cross_origin()
def predict():

    company = request.form.get('company')

    car_model = request.form.get('car_models')
    year = request.form.get('year')
    fuel_type = request.form.get('fuel_type')
    driven = request.form.get('kilo_driven')
    print(company, car_model, year, fuel_type, driven)

    prediction = model.predict(pd.DataFrame(columns=['name', 'company', 'year', 'kms_driven', 'fuel_type'],
                                            data=np.array([car_model, company, year, driven, fuel_type]).reshape(1, 5)))
    print(prediction)

    return str(np.round(prediction[0], 2))

@app.route('/add_user', methods=['POST'])
def add_user():
    error=None
    name=request.form.get('uname')
    email=request.form.get('uemail')
    password=request.form.get('upassword')
    if(re.fullmatch(name_regex, name) and re.fullmatch(email_regex, email) and re.fullmatch(password_regex, password)):
        cursor = mysql.connection.cursor()
        cursor.execute("""SELECT * from `users` WHERE `email` LIKE '{}'""" .format(email))
        mysql.connection.commit()
        users=cursor.fetchall()
        if(users):
            flash('Email address already exists')
            return render_template('register.html')
            
        else:
            cursor.execute("""INSERT INTO `users` (`user_id`, `name`, `email`, `password`) VALUES
            (NULL, '{}', '{}', '{}')""" .format(name, email, password))
            mysql.connection.commit()

            cursor.execute("""SELECT * FROM `users` WHERE `email` LIKE '{}'""".format(email))
            myuser=cursor.fetchall()
            session['user_id']=myuser[0][0]
            return redirect ('/home')
    
    else:
        error = "invalid Details and make sure that password is of minimum 6 length containg number, capital letter, small letter and one special character"
        return  render_template('register.html',error=error)


@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect('/')

if __name__=="__main__":
    app.run(debug=True)