# checking the conflict offline
# Checking the conflict 
import os, requests

from flask import Flask, session, render_template, request, url_for, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key = 'books'

goodread_api_key = 'MsjvDuXUtT84eRwUd5mfw'


# Check for environment variable
if not os.getenv("DATABASE_URL"):
	raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
# Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Function to get the data using api request
def goodread_data_getter(isbn):
	res = requests.get("https://www.goodreads.com/book/review_counts.json", 
		params={"key": goodread_api_key, "isbns": isbn})
	if res.status_code == 404:
		return ['None', "None"]
	else:
		return [res.json()['books'][0]['average_rating'], 
		res.json()['books'][0]['work_ratings_count']]

@app.route("/")
def index():
	if 'user_id' in session:
		user = db.execute('SELECT * FROM users WHERE id = :id', 
						{'id':session['user_id']}).fetchone()
		if user:
			return render_template('user_home.html', user = user)
	else:
		return render_template('login.html')

@app.route('/register_user')
def register_user():
	return render_template('register.html')

@app.route('/register', methods = ["POST"])
def register():
	'''Register user'''

	#get username
	username = request.form.get('username')
	password = request.form.get('password')
	verify_password = request.form.get('verify_password')

	if password != verify_password:
		return render_template('error.html', primary_message = 'Error :(', 
			message = 'Password did not match')
	elif db.execute('SELECT * FROM users WHERE username = :username', {'username':username}).rowcount != 0:
		return render_template('error.html', primary_message = 'Error :(', 
		 message = 'User ' + username + ' already exits')
	else:
		db.execute('INSERT INTO users (username, password) VALUES (:username, :password)',
			{'username':username, 'password':password})
		db.commit()
		return render_template('error.html', primary_message = 'Succesfull :)', 
			message = 'Succesfully registered')

@app.route('/login', methods=["POST", 'GET'])
def login():
	'''Login into to write reviews'''

	# get username and password
	if request.method == 'POST':
		username = request.form.get('username')
		password = request.form.get('password')

		user = db.execute('SELECT * FROM users WHERE username = :username',{'username':username}).fetchone()

		if user:
			if user.password == password:
				session['user_id'] = user.id
				return render_template('user_home.html', user = user)
			else:
				return render_template('error.html', primary_message = 'Error :(', 
					message = 'Woops wrong password or username')
		else:
			return render_template('error.html', primary_message = 'Error :(',
				message = "You have either put wrong username or password")
	else:
		if 'user_id' in session:
			user = db.execute('SELECT * FROM users WHERE id = :id', 
				{'id':session['user_id']}).fetchone()
			if user:
				return render_template('user_home.html', user = user)
	return render_template('login.html')

@app.route('/logout')
def logout():
	'''Logging out or ending a session'''

	session.pop('user_id', None)
	return render_template('login.html')

@app.route('/books', methods=['POST', 'GET'])
def books():
	'''Lists all the books and search if there is any query'''

	if 'user_id' not in session:
		return render_template('login.html')

	search_type = None
	search = None
	books = db.execute('SELECT * FROM books').fetchall()
	if request.method == 'POST':
		search_type = request.form.get('search_type')
		search = request.form.get('search')

	if( search_type or search) is None:
		return render_template('books.html',books = books, status = True)

	if search_type.lower() == 'isbn':
		search_result = db.execute("SELECT * FROM books WHERE isbn LIKE :search", 
			{'search':'%' + search + '%'}).fetchall()
	elif search_type.lower() == 'author':
		search_result = db.execute("SELECT * FROM books WHERE author LIKE :search", 
			{'search':'%' + search + '%'}).fetchall()
	else:
		search_result = db.execute("SELECT * FROM books WHERE title LIKE :search", 
			{'search':'%' + search + '%'}).fetchall()

	if search_result != None:
		if len(search_result)==0:
			search_result = None

	if search_result is not None:
		return render_template('books.html', books = search_result, status = True)

	else:
		return render_template('books.html', books = None, status = False)

	return render_template('books.html', books = books, status = True)


@app.route('/books/<int:book_id>', methods = ['POST', 'GET'])
def book_info(book_id):
	"""Details about a single book and review submission"""

	# Just making sure
	book_id = int(book_id)
	book_review = False
	user = None
	review = None
	review_conf = None
	rating_conf = None

	print(book_review)
	book = db.execute('SELECT * FROM books WHERE id = :id', {'id':book_id}).fetchone()
	if 'user_id' in session:

		# Getting logged in user and his/her review
		user = db.execute('SELECT * FROM users WHERE id = :id',{'id':session['user_id']}).fetchone()
		review = db.execute('SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id',
			{'book_id':book_id, 'user_id':session['user_id']}).fetchone()

		if review:
			book_review = True
			review_conf = review.review
			rating_conf = review.rating
			
		else:
			if request.method == 'POST':
				review_conf = request.form.get('Review')
				rating_conf = int(request.form.get('rating'))
				if review_conf and rating_conf:
					db.execute('INSERT INTO reviews (review, user_id, book_id, rating) VALUES (:review, :user_id, :book_id, :rating)',
						{'review':review_conf, 'user_id':user.id, 'book_id':book_id, 'rating':rating_conf})
					db.commit()
					book_review = True
				else:
					return render_template('error.html', primary_message= 'Error :(', 
						message= 'You didnt fill either rating or reivew')

	good_read = goodread_data_getter(isbn = book.isbn)
	return render_template('book_info.html', book = book, book_review = book_review, 
		review = review_conf,rating = rating_conf, good_read_review = good_read, user = user)

@app.route('/api/<string:isbn>')
def book_api(isbn):
	'''API that returns data in json format once requested'''

	book = db.execute('SELECT * FROM books WHERE isbn = :isbn', {'isbn':isbn}).fetchone()

	if book is None:
		return jsonify({'error':'invalid ISBN'}), 404
	good_read = goodread_data_getter(isbn)
	return jsonify({
		'title':book.title,
		'author':book.author,
		'year':book.year,
		'isbn':isbn,
		'review_count':good_read[1],
		'average_score':good_read[0]
		})
