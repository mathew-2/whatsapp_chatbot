from langchain_core.tools import tool
from typing import List, Dict
from vector_store import FlowerShopVectorStore
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

vector_store = FlowerShopVectorStore()

customers_database = [
    {"name": "John Doe", "postcode": "SW1A 1AA", "dob": "1990-01-01", "customer_id": "CUST001", "first_line_address": "123 Main St", "phone_number": "07712345678", "email": "john.doe@example.com"},
    {"name": "Jane Smith", "postcode": "E1 6AN", "dob": "1985-05-15", "customer_id": "CUST002", "first_line_address": "456 High St", "phone_number": "07723456789", "email": "jane.smith@example.com"},
]

orders_database = [
    {"order_id": "ORD001", "customer_id": "CUST001", "status": "Processing", "items": ["Premium Liquid Hand Soap"], "quantity": [1]},
    {"order_id": "ORD002", "customer_id": "CUST002", "status": "Shipped", "items": ["Ultra Soft Toothbrush (Pack of 4)", "Premium Liquid Hand Soap"], "quantity": [1, 1]},
]

with open('inventory.json', 'r') as f:
    inventory_database = json.load(f)

data_protection_checks = []

@tool
def data_protection_check(name: str, postcode: str, year_of_birth: int, month_of_birth: int, day_of_birth: int) -> Dict:
    """
    Perform a data protection check against a customer to retrieve customer details.

    Args:
        name (str): Customer first and last name
        postcode (str): Customer registered address
        year_of_birth (int): The year the customer was born
        month_of_birth (int): The month the customer was born
        day_of_birth (int): The day the customer was born

    Returns:
        Dict: Customer details (name, postcode, dob, customer_id, first_line_address, email)
    """
    data_protection_checks.append(
        {
            'name': name,
            'postcode': postcode,
            'year_of_birth': year_of_birth,
            'month_of_birth': month_of_birth,
            'day_of_birth': day_of_birth
        }
    )
    for customer in customers_database:
        if (customer['name'].lower() == name.lower() and
            customer['postcode'].lower() == postcode.lower() and
            int(customer['dob'][0:4]) == year_of_birth and
            int(customer["dob"][5:7]) == month_of_birth and
            int(customer["dob"][8:10]) == day_of_birth):
            return f"DPA check passed - Retrieved customer details:\n{customer}"

    return "DPA check failed, no customer with these details found"

@tool
def create_new_customer(first_name: str, surname: str, year_of_birth: int, month_of_birth: int, day_of_birth: int, postcode: str, first_line_of_address: str, phone_number: str, email: str) -> str:
    """
    Creates a customer profile, so that they can place orders.

    Args:
        first_name (str): Customers first name
        surname (str): Customers surname
        year_of_birth (int): Year customer was born
        month_of_birth (int): Month customer was born
        day_of_birth (int): Day customer was born
        postcode (str): Customer's postcode
        first_line_address (str): Customer's first line of address
        phone_number (str): Customer's phone number
        email (str): Customer's email address

    Returns:
        str: Confirmation that the profile has been created or any issues with the inputs
    """
    if len(phone_number) != 11:
        return "Phone number must be 11 digits"
    customer_id = len(customers_database) + 1
    customers_database.append({
        'name': first_name + ' ' + surname,
        'dob': f'{year_of_birth}-{month_of_birth:02}-{day_of_birth:02}',
        'postcode': postcode,
        'first_line_address': first_line_of_address,
        'phone_number': phone_number,
        'email': email,
        'customer_id': f'CUST{customer_id}'
    })
    return f"Customer registered, with customer_id {f'CUST{customer_id}'}"
    

@tool
def query_knowledge_base(query: str) -> List[Dict[str, str]]:
    """
    Looks up information in a knowledge base to help with answering customer questions and getting information on business processes.

    Args:
        query (str): Question to ask the knowledge base

    Return:
        List[Dict[str, str]]: Potentially relevant question and answer pairs from the knowledge base
    """
    return vector_store.query_faqs(query=query)



@tool
def search_for_product_reccommendations(description: str):
    """
    You are a virtual shopping assistant for an e-commerce platform. Your role is to provide product recommendations 
    based on customer inquiries across different categories. When a customer describes what they are looking for, 
    you will search the inventory to find suitable products.
    "A cheap laptop for students."
    "Personal care products that are budget-friendly."
    "Multipurpose cleaning spray for home use."
    "Microfiber cleaning cloths (Pack of 6) for delicate surfaces."
    "Eco-friendly household items for everyday cleaning."
    Args:
        query (str): Description of product features

    Return:
        List[Dict[str, str]]: Potentially relevant products
    """
    return vector_store.query_inventories(query=description)

# @tool
# def retrieve_existing_customer_orders(customer_id: str) -> List[Dict]:
#     """
#     Retrieves the orders associated with the customer, including their status, items and ids

#     Args:
#         customer_id (str): Customer unique id associated with the order

#     Returns:
#         List[Dict]: All the orders associated with the customer_id passed in
#     """
#     customer_orders = [order for order in orders_database if order['customer_id'] == customer_id]
#     if not customer_orders:
#         return f"No orders associated with this customer id: {customer_id}"
#     return customer_orders

# @tool
# def place_order(items: Dict[str, int], customer_id: str) -> str:
#     """
#     Places an order for the requested items, and for the required quantities.

#     Args:
#         items (Dict[str, int]): Dictionary of items to order, with item id as the key and the quantity of that item as the value.
#         customer_id (str): The customer to place the order for

#     Returns:
#         str: Message indicating that the order has been placed, 
#     """
#     # Check that the item ids are valid 
#     # Check that the quantities of items are valid
#     availability_messages = []
#     valid_item_ids = [
#         item['id'] for item in inventory_database
#     ]
#     for item_id, quantity in items.items():
#         if item_id not in valid_item_ids:
#             availability_messages.append(f'Item with id {item_id} is not found in the inventory')
#         else:
#             inventory_item = [item for item in inventory_database if item['id'] == item_id][0]
#             if quantity > inventory_item['quantity']:
#                 availability_messages.append(f'There is insufficient quantity in the inventory for this item {inventory_item["name"]}\nAvailable: {inventory_item["quantity"]}\nRequested: {quantity}')
#     if availability_messages:
#         return "Order cannot be placed due to the following issues: \n" + '\n'.join(availability_messages)

#     # Place the order (in pretend database)
#     order_id = len(orders_database) + 1
#     orders_database.append(
#         {
#             'order_id': order_id,
#             'customer_id': customer_id,
#             'status': 'Waiting for payment',
#             'items': list(items.keys()),
#             'quantity': list(items.values())
#         }
#     )
#     # Update the inventory
#     for item_id, quantity in items.items():
#         inventory_item = [item for item in inventory_database if item['id'] == item_id][0]
#         inventory_item['quantity'] -= quantity

#     # Send order confirmation email
#     email_result = send_order_confirmation_email(order_id, customer_id, items)

#     return f"Order with id {order_id} has been placed successfully. {email_result}"

@tool
def send_order_confirmation_email(order_id: str, customer_id: str, items: Dict[str, int]) -> str:
    """
    Sends an order confirmation email to the customer.

    Args:
        order_id (str): The ID of the order
        customer_id (str): The ID of the customer
        items (Dict[str, int]): Dictionary of items ordered, with item id as the key and quantity as the value

    Returns:
        str: Message indicating whether the email was sent successfully
    """
    # Find the customer's email
    customer = next((c for c in customers_database if c['customer_id'] == customer_id), None)
    if not customer:
        return f"Error: Customer with ID {customer_id} not found"

    customer_email = customer['email']

    # Compose the email
    subject = f"Order Confirmation - Order #{order_id}"
    body = f"Dear {customer['name']},\n\nThank you for your order. Your order details are as follows:\n\n"
    for item_id, quantity in items.items():
        item = next((i for i in inventory_database if i['id'] == item_id), None)
        if item:
            body += f"- {item['name']}: {quantity}\n"
    body += "\nWe will process your order shortly.\n\nBest regards,\nYour Flower Shop Team"

    # Create the email message
    message = MIMEMultipart()
    message['From'] = "akshaykumarbedre.bm@gmail.com"
    message['To'] = "akshaykumarbedre.bm@gmail.com"
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # Send the email (Note: This is a placeholder. In a real application, you'd use actual SMTP settings)
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)
        return f"Order confirmation email sent to {customer_email}"
    except smtplib.SMTPAuthenticationError:
        return "Failed to send email: Authentication error. Please check the email credentials."
    except smtplib.SMTPException as e:
        return f"Failed to send email: SMTP error occurred: {str(e)}"
    except Exception as e:
        return f"Failed to send email: An unexpected error occurred: {str(e)}"
