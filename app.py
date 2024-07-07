from flask import Flask, render_template, json, request, jsonify, session, redirect
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = 'mykey'

app.config['MYSQL_USER'] = 'psak'
app.config['MYSQL_PASSWORD'] = 'psak'
app.config['MYSQL_DB'] = 'BucketList'
app.config['MYSQL_HOST'] = 'localhost'

mysql = MySQL(app)

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/api/signUp', methods=['POST'])
def SignUp():
    try:
        # Get user details from request
        _name = request.form['name']
        _email = request.form['email']
        _password = request.form['password']

        # Validate the received values
        if _name and _email and _password:
            # Create a MySQL connection
            conn = mysql.connection
            cursor = conn.cursor()

            # Hash the password
            _hashed_password = generate_password_hash(_password)

            # Call the stored procedure to create a new user
            cursor.callproc('sp_createUser', (_name, _email, _hashed_password))
            data = cursor.fetchall()

            # Check if the procedure executed successfully
            if len(data) == 0:
                conn.commit()
                return jsonify({'message': 'User created successfully!'})
            else:
                return jsonify({'error': str(data[0])})
        else:
            return jsonify({'error': 'Enter the required fields'})

    except Exception as e:
        return jsonify({'error': str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/signin')
def showSignin():
    return render_template('signin.html')

@app.route('/api/validateLogin',methods=['POST'])
def validateLogin():
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']
        # connect to mysql 
        con = mysql.connect()
        cursor = con.cursor()
        cursor.callproc('sp_validateLogin',(_username,))
        data = cursor.fetchall()
        if len(data) > 0:
            if check_password_hash(str(data[0][3]),_password):
                session['user'] = data[0][0]
                return redirect('/userHome')
            else:
                return render_template('error.html',error = 'Wrong Email address or Password')
        else:
            return render_template('error.html',error = 'Wrong Email address or Password')
    except Exception as e:
        return render_template('error.html',error = str(e))
    finally:
        cursor.close()
        con.close()

@app.route('/userhome')
def userHome():
    if session.get('user'):
        return render_template('userhome.html')
    else:
        return render_template('error.html', error='Unauthorized Access')
    
@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')

@app.route('/showAddWish')
def showAddWish():
    return render_template('addWish.html')

@app.route('/addWish',methods=['POST'])
def addWish():
    try:
        if session.get('user'):
            _title = request.form['inputTitle']
            _description = request.form['inputDescription']
            _user = session.get('user')
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_addWish',(_title,_description,_user))
            data = cursor.fetchall()
            if len(data) is 0:
                conn.commit()
                return redirect('/userHome')
            else:
                return render_template('error.html',error = 'An error occurred!')
        else:
            return render_template('error.html',error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html',error = str(e))
    finally:
        cursor.close()
        conn.close()

@app.route('/getWish')
def getWish():
    try:
        if session.get('user'):
            _user = session.get('user')
            con = mysql.connect()
            cursor = con.cursor()
            cursor.callproc('sp_GetWishByUser',(_user,))
            wishes = cursor.fetchall()
            wishes_dict = []
            for wish in wishes:
                wish_dict = {
                        'Id': wish[0],
                        'Title': wish[1],
                        'Description': wish[2],
                        'Date': wish[4]}
                wishes_dict.append(wish_dict)
            return json.dumps(wishes_dict)
        else:
            return render_template('error.html', error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error = str(e))    

@app.route('/get_wishes')
def get_wishes():
    if session.get('user'):
        # Example JSON data to simulate data from the database
        wishes = [
            {"title": "Travel to Japan", "description": "Explore Tokyo, Kyoto, and Osaka."},
            {"title": "Learn Guitar", "description": "Take guitar lessons and practice daily."},
            {"title": "Skydiving", "description": "Experience the thrill of skydiving."}
        ]
        return jsonify(wishes)
    else:
        return jsonify({"error": "Unauthorized Access"}), 401
    
@app.route('/getWishById',methods=['POST'])
def getWishById():
    try:
        if session.get('user'):
            _id = request.form['id']
            _user = session.get('user')
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_GetWishById',(_id,_user))
            result = cursor.fetchall()
            wish = []
            wish.append({'Id':result[0][0],'Title':result[0][1],'Description':result[0][2]})
            return json.dumps(wish)
        else:
            return render_template('error.html', error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html',error = str(e))@app.route('/updateWish', methods=['POST'])
def updateWish():
    try:
        if session.get('user'):
            _user = session.get('user')
            _title = request.form['title']
            _description = request.form['description']
            _wish_id = request.form['id']
            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_updateWish',(_title,_description,_wish_id,_user))
            data = cursor.fetchall()
            if len(data) is 0:
                conn.commit()
                return json.dumps({'status':'OK'})
            else:
                return json.dumps({'status':'ERROR'})
    except Exception as e:
        return json.dumps({'status':'Unauthorized access'})
    finally:
        cursor.close()
        conn.close()
    
    

if __name__ == "__main__":
    app.run(debug=True, port=5002)
