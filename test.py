import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    users = db.execute("SELECT username, password FROM users").fetchall()
    for user in users:
        print(f"{user.username} and {user.password}")

    username = input('What is you name')
    password = input('what is you password')

    user = db.execute('SELECT * FROM users WHERE username = :username',{'username':username}).fetchall()

    if user[0]:
        if password == user[0].password:
            print(user[0].id)
            return ("Welcome you are logged in")
    else:
        return ('You go either password or username wrong. please try again')

if __name__ == "__main__":
    main()