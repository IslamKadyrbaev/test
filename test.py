import sqlite3

class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None

    def open_connection(self):
        if not self.connection:
            self.connection = sqlite3.connect(self.db_name)
            self.connection.row_factory = sqlite3.Row

    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query, params=None):
        self.open_connection()
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        self.connection.commit()
        return cursor

    def fetch_one(self, query, params=None):
        cursor = self.execute_query(query, params)
        return cursor.fetchone()

    def fetch_all(self, query, params=None):
        cursor = self.execute_query(query, params)
        return cursor.fetchall()

    def transactional_operation(self, operations):
        self.open_connection()
        try:
            for query, params in operations:
                self.execute_query(query, params)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e


class User:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        );
        """
        self.db_manager.execute_query(query)

    def add_user(self, name, role):
        query = "INSERT INTO users (name, role) VALUES (?, ?);"
        self.db_manager.execute_query(query, (name, role))

    def get_user_by_id(self, user_id):
        query = "SELECT * FROM users WHERE id = ?;"
        return self.db_manager.fetch_one(query, (user_id,))

    def delete_user(self, user_id):
        query = "DELETE FROM users WHERE id = ?;"
        self.db_manager.execute_query(query, (user_id,))


class Admin(User):
    def create_admin_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            permissions TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
        self.db_manager.execute_query(query)

    def add_admin(self, user_id, permissions):
        query = "INSERT INTO admins (user_id, permissions) VALUES (?, ?);"
        self.db_manager.execute_query(query, (user_id, permissions))


class Customer(User):
    def create_customer_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            address TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
        self.db_manager.execute_query(query)

    def add_customer(self, user_id, address):
        query = "INSERT INTO customers (user_id, address) VALUES (?, ?);"
        self.db_manager.execute_query(query, (user_id, address))


if __name__ == "__main__":
    db_manager = DatabaseManager("app.db")

    user = User(db_manager)
    user.create_table()

    admin = Admin(db_manager)
    admin.create_admin_table()

    customer = Customer(db_manager)
    customer.create_customer_table()

    user.add_user("Айбек", "admin")
    user.add_user("Бексултан", "customer")

    user_data = user.get_user_by_id(1)
    print("User:", dict(user_data))

    admin.add_admin(1, "full_access")
    customer.add_customer(2, "123 Main St")

    try:
        db_manager.transactional_operation([
            ("INSERT INTO users (name, role) VALUES (?, ?);", ("Алина", "customer")),
            ("INSERT INTO customers (user_id, address) VALUES (?, ?);", (3, "456 Elm St")),
        ])
    except Exception as e:
        print("Transaction failed:", e)

    db_manager.close_connection()
