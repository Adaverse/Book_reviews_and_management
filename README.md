
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

Import data into the ```books``` table using ```sqlalchemy```
```
f = open("books.csv")
reader = csv.reader(f) 
next(reader)
for isbn, title, author, year in reader:
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                {"isbn": isbn, "title": title, "author": author, "year":year})
db.commit()
```
