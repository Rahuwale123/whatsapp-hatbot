"""
This module provides functionalities for interacting with the MySQL database.
It includes functions for establishing a database connection, creating necessary tables,
and performing operations related to customer data, such as checking for existing users
and inserting new user records.
"""

import mysql.connector
from mysql.connector import Error
from typing import Optional, Any

# Global database connection instance
_db_connection: Optional[mysql.connector.connection.MySQLConnection] = None

def initialize_mysql(host: str, user: str, password: str, database: str) -> None:
    """
    Initializes the MySQL database connection and creates the 'customers' table if it doesn't exist.

    Args:
        host: The database host.
        user: The database user.
        password: The database password.
        database: The name of the database to connect to.
    """
    global _db_connection
    try:
        _db_connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        if _db_connection.is_connected():
            db_Info = _db_connection.get_server_info()
            print(f"[MySQL] Connected to MySQL database. Server version: {db_Info}")
            _create_customers_table()
        else:
            print("[❌ ERROR] MySQL connection could not be established.")
    except Error as e:
        print(f"[❌ ERROR] Error connecting to MySQL: {e}")
        _db_connection = None # Ensure connection is None on failure

def _create_customers_table() -> None:
    """
    Creates the 'customers' table if it does not already exist.
    The table stores WhatsApp user IDs and their display names.
    """
    if not _db_connection:
        print("[❌ ERROR] MySQL connection not initialized. Cannot create table.")
        return

    cursor = _db_connection.cursor()
    create_table_query = """
    CREATE TABLE IF NOT EXISTS customers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        company_number VARCHAR(255) NOT NULL,
        wa_id VARCHAR(255) UNIQUE NOT NULL,
        display_name VARCHAR(255),
        intent VARCHAR(255),
        purpose TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    try:
        cursor.execute(create_table_query)
        _db_connection.commit()
        print("[MySQL] 'customers' table checked/created successfully.")
    except Error as e:
        print(f"[❌ ERROR] Error creating 'customers' table: {e}")
    finally:
        cursor.close()

def get_customer(wa_id: str) -> Optional[tuple]:
    """
    Retrieves customer information from the database based on their WhatsApp ID.

    Args:
        wa_id: The WhatsApp ID of the customer.

    Returns:
        A tuple containing customer data if found, otherwise None.
    """
    if not _db_connection or not _db_connection.is_connected():
        print("[❌ ERROR] MySQL connection not initialized or disconnected. Cannot get customer.")
        return None

    cursor = _db_connection.cursor(buffered=True)
    query = "SELECT id, wa_id, display_name FROM customers WHERE wa_id = %s"
    try:
        cursor.execute(query, (wa_id,))
        result = cursor.fetchone()
        return result
    except Error as e:
        print(f"[❌ ERROR] Error retrieving customer with WA ID {wa_id}: {e}")
        return None
    finally:
        cursor.close()

def add_new_customer(company_number: str, wa_id: str, display_name: str) -> bool:
    """
    Adds a new customer record to the database.

    Args:
        company_number: The WhatsApp phone number of the company.
        wa_id: The WhatsApp ID of the customer.
        display_name: The display name of the customer.

    Returns:
        True if the customer was added successfully, False otherwise.
    """
    if not _db_connection or not _db_connection.is_connected():
        print("[❌ ERROR] MySQL connection not initialized or disconnected. Cannot add new customer.")
        return False

    cursor = _db_connection.cursor()
    insert_query = "INSERT INTO customers (company_number, wa_id, display_name) VALUES (%s, %s, %s)"
    try:
        cursor.execute(insert_query, (company_number, wa_id, display_name))
        _db_connection.commit()
        print(f"[MySQL] Added new customer: Company={company_number}, WA ID={wa_id}, Display Name={display_name}")
        return True
    except Error as e:
        if e.errno == 1062: # Duplicate entry error code
            print(f"[MySQL] Customer with WA ID {wa_id} already exists (skipped insertion).")
        else:
            print(f"[❌ ERROR] Error adding new customer {wa_id}: {e}")
        return False
    finally:
        cursor.close()

def update_customer_chat_info(wa_id: str, intent: Optional[str] = None, purpose: Optional[str] = None) -> bool:
    """
    Updates the intent and purpose for an existing customer in the database.

    Args:
        wa_id: The WhatsApp ID of the customer.
        intent: The identified intent of the conversation.
        purpose: The identified purpose/summary of the conversation.

    Returns:
        True if the update was successful, False otherwise.
    """
    if not _db_connection or not _db_connection.is_connected():
        print("[❌ ERROR] MySQL connection not initialized or disconnected. Cannot update customer chat info.")
        return False

    cursor = _db_connection.cursor()
    update_query = "UPDATE customers SET intent = %s, purpose = %s WHERE wa_id = %s"
    try:
        cursor.execute(update_query, (intent, purpose, wa_id))
        _db_connection.commit()
        print(f"[MySQL] Updated chat info for customer {wa_id}: Intent='{intent}', Purpose='{purpose}'")
        return True
    except Error as e:
        print(f"[❌ ERROR] Error updating chat info for customer {wa_id}: {e}")
        return False
    finally:
        cursor.close()

def get_all_customers() -> list[dict[str, Any]]:
    """
    Retrieves all customer records from the 'customers' table.

    Returns:
        A list of dictionaries, where each dictionary represents a customer record.
        Returns an empty list if no customers are found or an error occurs.
    """
    if not _db_connection or not _db_connection.is_connected():
        print("[❌ ERROR] MySQL connection not initialized or disconnected. Cannot retrieve all customers.")
        return []

    customers_list: list[dict[str, Any]] = []
    cursor = _db_connection.cursor(dictionary=True) # Return results as dictionaries
    query = "SELECT id, company_number, wa_id, display_name, intent, purpose, created_at FROM customers"
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        customers_list = list(results)
    except Error as e:
        print(f"[❌ ERROR] Error retrieving all customers: {e}")
    finally:
        cursor.close()
    return customers_list 