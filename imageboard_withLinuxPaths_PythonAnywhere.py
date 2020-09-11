# -*- coding: utf-8 -*-
from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify
import sqlite3
import random
import os
from datetime import datetime
from werkzeug.utils import secure_filename

#Flask configuration variables
UPLOAD_FOLDER = os.getcwd() + r'/static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

#Initiate Flask app
app = Flask(__name__, template_folder=os.getcwd(), static_folder=os.getcwd() + r'/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

print(os.getcwd())

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
            (id integer primary key, idofpost integer, numberofcommentofpost int, user text, commenttext text)''')

conn.commit()
conn.close()

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
        #Load content from DB
        if int(numberOfPostsVariable) == 0:
            allPosts = c.execute('SELECT * FROM posts ORDER BY id DESC LIMIT 10')
        else:
            allPosts = c.execute('SELECT * FROM posts ORDER BY id DESC LIMIT 10 {number}'.format(number=numberOfPostsVariable))
            
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
        
        #Check if username is empty, if yes set username to anonym
        if username == "":
            username = "anonym"
        
        #Set ID of post (last post + 1)
        try:
            c.execute('SELECT id FROM posts ORDER BY id DESC LIMIT 1')
            idOfPost = c.fetchall()
            idOfPost = idOfPost[0]
            idOfPost = int(idOfPost[0]) + 1
        except:
            #If no post exists yet, give the first post the id of number 1
            idOfPost = 1
        
        #Get current timestamp
        actualTime = datetime.now()
        actualTimeForInsertingIntoDB = str(actualTime.hour) + ':' + str(actualTime.minute) + ':' + str(actualTime.second)
        actualDateForInsertingIntoDB = str(actualTime.day) + '.' + str(actualTime.month) + '.' + str(actualTime.year)

        #Check if images have the correct file extension
        if 'image' not in request.files:
            flash('No image part')
            return redirect('/upload', code=302)
        image = request.files['image']
        # if user does not select file, browser also submit an empty part without filename
        if image.filename == '':
            flash('No selected image')
            return redirect('/upload', code=302)
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filename = str(idOfPost) + '_' + filename
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imageName = filename
        else: 
            message= 'Nahratý neplatný súbor. Nahraj súbor .gif, .png, .jpg alebo .jpeg'
            return render_template('/upload-message.html', message=message)
        
        #Save the post into DB
        data = [(idOfPost, actualTimeForInsertingIntoDB, actualDateForInsertingIntoDB, username, title, post, imageName)]
        c.executemany('INSERT INTO posts VALUES (?,?,?,?,?,?,?)', data)
        conn.commit()
        conn.close()
      
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
        c.execute('SELECT * FROM posts ORDER BY id DESC LIMIT 10 OFFSET ' + str(numberOfPostsVariable))
        loadedPosts = c.fetchall()
        return render_template('loadNewPosts.html', loadedPosts = loadedPosts)

#Show post route and function
@app.route("/post", methods=["GET", "POST"])
def mainPost():
    return redirect('/', code=302)

#Show post route and function
@app.route("/post/<int:idofpost>", methods=["GET", "POST"])
def post(idofpost):
    #Initiate DB connection
    conn = sqlite3.connect('imageboard.db')
    c = conn.cursor()
    
    #Define what to do when request method is GET
    if request.method == 'GET':
        #Get post's details (image, text, headline, etc.)
        c.execute('SELECT * FROM posts WHERE id LIKE ' + str(idofpost))
        postDetails = c.fetchall()

        #Get post's comments
        c.execute('SELECT * FROM comments WHERE idofpost LIKE ' + str(idofpost) + ' ORDER BY id ASC')
        comments = c.fetchall()
        
        #Create a variable for post's id to create a URL or posting a comment on the webpage
        idOfPostForButtonURL = postDetails[0]
        idOfPostForButtonURL = idOfPostForButtonURL[0]
        
        return render_template('show_post.html', postDetails = postDetails, comments = comments, idOfPostForButtonURL = idOfPostForButtonURL)
    
    
#Post a comment route and function
@app.route("/post_comment/<int:idofpost>", methods=["GET", "POST"])
def post_comment(idofpost):
    #Initiate DB connection
    conn = sqlite3.connect('imageboard.db')
    c = conn.cursor()
    
    #Define what to do when request method is GET
    if request.method == 'GET':
        return render_template('post_comment.html')
    
    #Define what to do when request method is POST
    if request.method == 'POST':
        #Get data from HTML
        user = session['usernameForComment'] = request.form['username']
        commenttext = session['commentText'] = request.form['commentText']
        idofpost = int(idofpost)
        
        #Set ID of comment (last comment + 1)
        try:
            c.execute('SELECT id FROM comments ORDER BY id DESC LIMIT 1')
            idofcomment = c.fetchall()
            idofcomment = idofcomment[0]
            idofcomment = int(idofcomment[0]) + 1
        except:
            idofcomment = 1
        
        #Set number of comment of a post
        try:
            c.execute('SELECT numberofcommentofpost FROM comments WHERE idofpost LIKE ' + str(idofpost) + ' ORDER BY numberofcommentofpost DESC LIMIT 1')
            numberofcommentofpost = c.fetchall()
            numberofcommentofpost = numberofcommentofpost[0]
            numberofcommentofpost = int(numberofcommentofpost[0]) + 1
        except:
            numberofcommentofpost = 1

        #Check if username is empty, if yes set username to anonym
        if user == "":
            user = "anonym"
            
        #Save the comment into DB
        commentData = [(idofcomment, idofpost, numberofcommentofpost, user, commenttext)]
        c.executemany('INSERT INTO comments VALUES (?,?,?,?,?)', commentData)
        conn.commit()
        conn.close()
        
        
        #Redirect back to the post's URL
        return redirect('/post/' + str(idofpost), code=302)

#Define route and function for o nas (about us)
@app.route("/o-nas", methods=["GET"])
def onas():
    return render_template('o-nas.html')

@app.route('/<path:path>')
def catch_all(path):
    return redirect('/', code=404)

#Run Flask instance
if __name__ == "__main__":
    app.run()