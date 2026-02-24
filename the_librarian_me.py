library = [
    {"title": "Things Fall Apart", "author": "Chinua Achebe", "year_of_publication": 1976, "isbn": "987-678-233-889", "available": True},
    {"title": "1984", "author": "George Orwell", "year_of_publication": 1949, "isbn": "978-045-152-4935", "available": True},
    {"title": "The Alchemist", "author": "Paulo Coelho", "year_of_publication": 1988, "isbn": "978-006-112-2415", "available": False},
    {"title": "Purple Hibiscus", "author": "Chimamanda Ngozi Adichie", "year_of_publication": 2003, "isbn": "978-140-003-3416", "available": True},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "year_of_publication": 1937, "isbn": "978-054-792-8227", "available": False},
]


def add_book():
    title = input("Enter the title of the book: ")
    author = input("Enter the author of the book: ")
    year_of_publication = int(input("Enter the year of publication: "))
    isbn = input("Enter the ISBN: ")


    book = {
        "title": title,
        "author": author,
        "year_of_publication": year_of_publication,
        "isbn": isbn,
        "available": True
    }

    library.append(book)

    print("Book added successfully")


def view_books():
    for i, book in enumerate(library, start=1):
        availability = "Yes" if book["available"] else "No"
        print(f"{i}. {book["title"]} by {book["author"]} published in {book["year_of_publication"]} with ISBN {book["isbn"]}. Availabile? {availability}")


def update_book(isbn):
    for book in library:
        if isbn == book["isbn"]:
            title = input("Enter the title of the updated book: ")
            author = input("Enter the author of the updated book: ")
            year_of_publication = int(input("Enter the year of publication: "))
            book["title"] = title  
            book["author"] = author  
            book["year_of_publication"] = year_of_publication  
            book["available"] = True
        

def delete_book(isbn):
    for i, book in enumerate(library):
        if isbn == book["isbn"]:
            library.pop(i)


def search_book(title):
    for book in library:
        if title == book["title"]:
            availability = "Yes" if book["available"] else "No"
            print(f"{book["title"]} by {book["author"]} published in {book["year_of_publication"]} with ISBN {book["isbn"]}. Availabile? {availability}")


def borrow_book(isbn):
    for book in library:
        if isbn == book["isbn"]:
            book["available"] = False
            print("Book successfully borrowed")


def return_book(isbn):
    for book in library:
        if isbn == book["isbn"]:
            book["available"] = True

    

menu = """
1. Add Book
2. View Books
3. Update Book
4. Delete Book
5. Search Book
6. Borrow Book
7. Return Book
8. Quit
"""



while True:
    print(menu)

    choice = input("Enter a choice from 1 to 8: ").strip()

    if choice == "1":
        add_book()
    elif choice == "2":
        view_books()
    elif choice == "3":
        isbn = input("Enter the isbn of the book: ")
        update_book(isbn)
    elif choice == "4":
        isbn = input("Enter the isbn of the book: ")
        delete_book(isbn)
    elif choice == "5":
        title = input("Enter the title of the book: ")
        search_book(title)
    elif choice == "6":   
        isbn = input("Enter the isbn of the book: ")
        borrow_book(isbn)
    elif choice == "7":   
        isbn = input("Enter the isbn of the book: ")
        return_book(isbn)
    elif choice == "8":
        print("Goodbye 👋")
        break
    else:
        print("Enter from 1-8")
        continue