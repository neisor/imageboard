# -*- coding: utf-8 -*-
from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify
import sqlite3
import random
import os
from datetime import datetime
from werkzeug.utils import secure_filename

#Flask configuration variables
UPLOAD_FOLDER = os.getcwd() + r'\static\images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

#Initiate Flask app
app = Flask(__name__, template_folder=os.getcwd(), static_folder=os.getcwd() + r'\static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Set secret key for sessions
app.secret_key = b'\xd8b-\xcc\xab\xb2K\x29j\xe7\x23S\xd4\xbd\x9e\x0cq\xd2\xcc\x8d'

#Initiate DB connection
conn = sqlite3.connect('imageboard.db')
c = conn.cursor()
#Create table for posts
c.execute('''CREATE TABLE IF NOT EXISTS posts
            (id integer primary key, time text, date text, user text, title text, posttext text, imagepath text)''')
#Create table for comments
c.execute('''CREATE TABLE IF NOT EXISTS comments
            (id integer primary key, time text, date text, user text, comment text)''')
conn.commit()

#Function for checking allowed extensions of file when uploaded
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
@app.route("/", methods=["GET", "POST"])
def main():
    #Define session for numberOfPosts to continuosly load content
    if session.get('numberOfPosts'):
        session.pop('numberOfPosts')
    session['numberOfPosts'] = 0
    numberOfPostsVariable = str(session.get('numberOfPosts'))
    
    #Initiate DB connection
    conn = sqlite3.connect('imageboard.db')
    c = conn.cursor()
    
    #Defines what to do when the request is GET
    if request.method == 'GET':
        if int(numberOfPostsVariable) == 0:
            allPosts = c.execute('SELECT * FROM posts ORDER BY date, time DESC LIMIT 10')
        else:
            allPosts = c.execute('SELECT * FROM posts ORDER BY date, time DESC LIMIT 10 {number}'.format(number=numberOfPostsVariable))
        return render_template('index.html', allPosts = allPosts)

    #Defines what to do when the request is POST
    if request.method == 'POST':
        pass

@app.route("/upload", methods=["GET", "POST"])
def upload():
    #Initiate DB connection
    conn = sqlite3.connect('imageboard.db')
    c = conn.cursor()
    #Define what to do if method is GET
    if request.method == 'GET':
        return render_template('upload.html')
    
    #Define what to do if method is POST
    if request.method == 'POST':
        #Get the data from the form
        username = request.form['username']
        title = request.form['nadpis']
        post = request.form['prispevok']
        
        #Get a random ID of post
        randomIdOfPost = random.randrange(99999999)
        
        #Get current timestamp
        actualTime = datetime.now()
        actualTimeForInsertingIntoDB = str(actualTime.hour) + ':' + str(actualTime.minute) + ':' + str(actualTime.second)
        actualDateForInsertingIntoDB = str(actualTime.day) + '.' + str(actualTime.month) + '.' + str(actualTime.year)
        
        if 'image' not in request.files:
            flash('No image part')
            return redirect('/upload', code=302)
        image = request.files['image']
        # if user does not select file, browser also
        # submit an empty part without filename
        if image.filename == '':
            flash('No selected image')
            return redirect('/upload', code=302)
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filename = str(randomIdOfPost) + '_' + filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imageName = filename
        
        
        #Save the post into DB
        data = [(randomIdOfPost, actualTimeForInsertingIntoDB, actualDateForInsertingIntoDB, username, title, post, imageName)]
        c.executemany('INSERT INTO posts VALUES (?,?,?,?,?,?,?)', data)
        conn.commit()
      
        return redirect('/', code=302)

@app.route("/load", methods=["POST"])
def load():
    #Initiate DB connection
    conn = sqlite3.connect('imageboard.db')
    c = conn.cursor()
    
    #Defines what to do when the request is POST
    if request.method == 'POST':
        session['numberOfPosts'] = int(session.get('numberOfPosts')) + 10
        numberOfPostsVariable = str(session.get('numberOfPosts'))
        c.execute('SELECT * FROM posts ORDER BY date, time DESC LIMIT 10 OFFSET ' + str(numberOfPostsVariable))
        loadedPosts = c.fetchall()
        return render_template('loadNewPosts.html', loadedPosts = loadedPosts)

#Run Flask instance
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, threaded=True)