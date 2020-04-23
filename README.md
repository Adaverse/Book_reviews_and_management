
## Website walkthrough
At this URL ```/``` or ```/login```
\
![GitHub Logo](/images/pic_1_login.png)
<br/>

If you do not have account then you can Signup (register)
![GitHub Logo](/images/register.png)
<br/>


Once you login, you will to redirected to home page which looks like 
![GitHub Logo](/images/pic_1_userhome.png)
<br/>


From home page, you can check the books available in the database.
On this page, you can search for your book of interest either using ISBN, author or title.
![GitHub Logo](/images/pic_1_booklist.png)
<br/>


Once you click on the book, you will be taken to this page where you can see the book details and also review from Goodreads. Here you can also write your own review and give rating from 1-5.
![GitHub Logo](/images/pic_1_bookinfo.png)
<br/>


You can only write review once and you can see it by going to that book's info.
![GitHub Logo](/images/pic_1_review.png)


## Database and Table creation
Create PostegreSQL database and then create table (its in ```create_table.sql```)
```
CREATE TABLE books ( id SERIAL PRIMARY KEY,
    isbn TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    year INTEGER NOT NULL
);
```

Import data into the ```books``` table using ```sqlalchemy``` (its in ```import.py```). For ```sqlalchemy``` to work, you need to export ```DATABASE_URL``` using ```export DATABASE_URL="<actual_url>"```
```
f = open("books.csv")
reader = csv.reader(f) 
next(reader)
for isbn, title, author, year in reader:
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                {"isbn": isbn, "title": title, "author": author, "year":year})
db.commit()
```
## Flask
In the ```application.py```, you can see that every ```app.route()``` followed by a function which will run under appropriate ```POST``` or ```GET``` request. For example at ```/``` URL
```
@app.route("/")
def index():
	if 'user_id' in session:
		user = db.execute('SELECT * FROM users WHERE id = :id', 
						{'id':session['user_id']}).fetchone()
		if user:
			return render_template('user_home.html', user = user)
	else:
		return render_template('login.html')
```
#### Session (Login and Logout)
Once a user logs in, his ```id``` is appended into ```session``` dictionary
```
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
```
Now we can check from anywhere, whether a user has logged in or not. For example, in ```layout.html``` in ```templates``` folder which is the base html from which every other pages inherit from, uses this ```session``` dict.
```
<div class = 'sidenav'>
    {% if 'user_id' in session %}
        <a href="{{ url_for('logout') }}">Logout</a>
    {% else %}
        <a href="{{ url_for('login') }}">Login</a>
    {% endif %}
    <a href="{{ url_for('books')}}">Books</a>
</div>
```
For logging out, we have to simply remove this key from the dictionary
```
@app.route('/logout')
def logout():
	'''Logging out or ending a session'''

	session.pop('user_id', None)
	return render_template('login.html')
```
#### Register
If user does not have an account then he/she has to register and the data provided is inserted into the table. Here only post request method is allowed.
```
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
```
## API
You can get the data in the following json format once you request at url: ```/api/<string:isbn>```
```
jsonify({
  'title':book.title,
  'author':book.author,
  'year':book.year,
  'isbn':isbn,
  'review_count':good_read[1],
  'average_score':good_read[0]
}
```
And the following fucntion returns the data that is requested from the above url
```
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
```
We are using api provided by Goodreads to get ```work_ratings_count``` and ```average_rating``` and the function that is getting this data is in ```application.py```
```
# Function to get the data using api request
def goodread_data_getter(isbn):
	res = requests.get("https://www.goodreads.com/book/review_counts.json", 
		params={"key": goodread_api_key, "isbns": isbn})
	if res.status_code == 404:
		return ['None', "None"]
	else:
		return [res.json()['books'][0]['average_rating'], 
		res.json()['books'][0]['work_ratings_count']]
```
## Search
You can search from the library using ```isbn```, ```author``` or ```title```. The following snippet extracts the query from ```POST``` request and then searches for it in the database using ```SELECT``` and ```LIKE```
```
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
```
