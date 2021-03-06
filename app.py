import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from models import db, Library # type: ignore

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///library.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False 
    db.init_app(app)
    return app

app = create_app()
CORS(app)
db.init_app(app)

@app.route("/")
def intro():
    return "Hello World"


@app.route("/status/<string:name>")
def status(name):
    book = Library.query.filter(Library.name.contains(name)).all()
    data = []
    for dats in book:
        atom = {
            "ISBN" : dats.ISBN,
            "name" : dats.name,
            "author" : dats.author,
            "copies" : dats.copies,
            "booked_by" : dats.booked_by,
            "booked_on" : dats.booked_on,
            "lend_by" : dats.lend_by,
            "book_picked" : dats.book_picked,
            "return_date" : dats.return_date
        }
        data.append(atom)

    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route("/<string:name>")
def get_book(name):
    book = Library.query.filter(Library.name.contains(name)).all()
    data = []
    for dats in book:
        atom = {
            "ISBN" : dats.ISBN,
            "name" : dats.name,
            "author" : dats.author,
            "copies" : dats.copies,
            "booked_by" : dats.booked_by
        }
        data.append(atom)

    response = jsonify(data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route("/delete/<ISBN>")
def delete_book(ISBN):
    book = Library.query.filter(Library.ISBN == ISBN).first()
    try:
        db.session.delete(book)
        db.session.commit()
        response = jsonify({"message" : "deleted"})
        response.status = 201
        response.headers.add('Access-Control-Allow-Origin', '*')
    except:
        response = jsonify({"message" : "error"})
        response.status = 400 
        response.headers.add('Access-Control-Allow-Origin', '*')

    return response


@app.route("/add/", methods=["POST"])
def add_book():
    data_dict = request.get_json()
    ISBN = data_dict["ISBN"]             #type: ignore
    name = data_dict["name"]             #type: ignore
    author = data_dict["author"]         #type: ignore
    copies = data_dict["copies"]         #type: ignore

    tb = Library.query.filter(Library.ISBN == ISBN).first()
    
    if tb is None:
        book = Library(ISBN = ISBN, name=name, author=author, copies=copies)
        db.session.add(book)
        db.session.commit()
        response = jsonify({"message" : "success"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.status_code = 201
        return response

    else:
        response = jsonify({"message" : "failed"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.status_code = 401
        return response


@app.route("/removebooked/", methods=['POST'])
def remove_booked():
    data_dict = request.get_json()
    ISBN = data_dict["ISBN"]             #type: ignore

    book = Library.query.filter(Library.ISBN == ISBN).first()
    if book is not None:
        book.booked_by = None 
        response = jsonify({"message" : "success"})
        response.status_code = 201
        db.session.commit()
    else:
        response = jsonify({"message" : "Failed. Book not found. Check ISBN"})
        response.status_code = 400
        response.headers.add('Access-Control-Allow-Origin', '*')

    return response


@app.route("/book/", methods=["POST"])
def book_book():
    data_dict = request.get_json()
    ISBN = data_dict["ISBN"]             #type: ignore
    booked_by = data_dict["booked_by"]   #type: ignore
    booked_on = data_dict["booked_on"]   #type: ignore
    return_date = data_dict["return_date"] #type: ignore
    book = Library.query.filter(Library.ISBN == ISBN).first()

    if book is not None:
        if book.booked_by is None:
            book.booked_by = booked_by
            book.booked_on = booked_on
            book.return_date = return_date
            response = jsonify({"message" : "success", "booked" : booked_by})
            response.status_code = 201
            db.session.commit()
        else:
            response = jsonify({"message" : "Already Booked"})
            response.status_code = 406
        response.headers.add('Access-Control-Allow-Origin', '*')
    else:
        response = jsonify({"message" : "failed. Check ISBN"})
        response.status_code = 400
        response.headers.add('Access-Control-Allow-Origin', '*')

    return response


@app.route("/lend/", methods=["POST"])
def lend_book():
    data_dict = request.get_json()
    ISBN = data_dict["ISBN"]    #type: ignore
    wanted_by = data_dict["wanted_by"]   #type: ignore

    book = Library.query.filter(Library.ISBN == ISBN).first()

    if book is not None:
        if book.booked_by == wanted_by:
            if int(book.copies) > 1:
                book.lend_by = book.booked_by
                book.booked_by = None
                book.copies -= 1
                response = jsonify({"message" : "successfully lent"})
                response.status = 201
            else:
                response = jsonify({"message" : "failed. Someone already booked it"})
                response.status = 400

        

        elif book.booked_by == None:
            book.lend_by = wanted_by
            book.copies -= 1
            response = jsonify({"message" : "no prev booking. successfully lent"})
            response.status = 200
        else:
            response = jsonify({"message" : "failed. Booked by someone else"})
            response.status = 400
    else:
        response = jsonify({"message" : "failed. No book of such ISBN"})
        response.status = 400

    db.session.commit()
    return response



@app.route("/return/", methods=["POST"])
def return_book():
    data_dict = request.get_json()
    ISBN = data_dict["ISBN"]    #type: ignore

    book = Library.query.filter(Library.ISBN == ISBN).first()

    if book is not None:
        book.lend_by = None 
        book.copies += 1
        response = jsonify({"message" : "successfully returned"})
        response.status = 201

    else:
        response = jsonify({"message" : "failed. check isbn"})
        response.status = 400
        
    db.session.commit()
    return response

if __name__ == "__main__":
    if "createdb" in sys.argv:
        with app.app_context():
            db.create_all()
        print("Database created")
    elif "seeddb" in sys.argv:
        with app.app_context():
            book = Library(ISBN = "1000", name="Sherlock Holmes: The Further Adventures", author = "MacBird", copies=3)
            db.session.add(book)
            db.session.commit()
        print("Database seeded with 1 entry")
    else:
        app.run(debug=True)
