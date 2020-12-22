# Standard imports, one new one is the stripe module.
# It can be installed easily with pip
# With the venv activated you simply run 'pip install stripe'

import stripe
from flask import Flask, request, Response
from flask_cors import CORS
import json
import mariadb
import dbcreds

app = Flask(__name__)
CORS(app)

# A new important variable in the dbcreds file used by stripe
# When you have your account set up, you can find your Secret Key here:
# https://dashboard.stripe.com/test/apikeys
stripe.api_key = dbcreds.stripe_key


# This function is used by the stripe web hook
# For those who want to capture and handle the data of purchases in their own DB
# Instead of just using the stripe dashboard.
# It runs a simple UPDATE command based on the stripe payment intent ID with the customers email


def update_customer_purchase(intent_id, email):
    cursor = None
    conn = None
    rows = None
    try:
        conn = mariadb.connect(
            user=dbcreds.user,
            password=dbcreds.password,
            host=dbcreds.host,
            port=dbcreds.port,
            database=dbcreds.database,
        )
        cursor = conn.cursor()
        # Obviously you will need to modify this to match your DB columns and tables
        cursor.execute(
            "UPDATE purchase SET success=1, email=? WHERE stripe_intent_id=?",
            [email, intent_id],
        )
        conn.commit()
        rows = cursor.rowcount
    except Exception as err:
        print(
            "Error updating customer in DB! Verify in Stripe if a payment has occured"
        )
        print(err)
    finally:
        if cursor != None:
            cursor.close()
        if conn != None:
            conn.close()
        if rows > 0:
            return Response(status=200)
        else:
            return Response(
                json.dumps("Something has gone wrong!", default=str),
                mimetype="application/json",
                status=500,
            )


# Very basic function that grabs the product information from the DB
# These are the cards that show up on the front end for the user to buy from


@app.route("/api/items", methods=["GET"])
def cute_animals():
    cursor = None
    conn = None
    items = None
    try:
        conn = mariadb.connect(
            user=dbcreds.user,
            password=dbcreds.password,
            host=dbcreds.host,
            port=dbcreds.port,
            database=dbcreds.database,
        )
        cursor = conn.cursor()
        # Obviously you will need to modify this to match your DB columns and tables
        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()
    except Exception as err:
        print(err)
    finally:
        if cursor != None:
            cursor.close()
        if conn != None:
            conn.close()
        if items != None:
            return Response(
                json.dumps(items, default=str), mimetype="application/json", status=200
            )
        else:
            return Response(
                json.dumps("Something has gone wrong!", default=str),
                mimetype="application/json",
                status=500,
            )


# The main monster function that will actually handle creating a purchase in our DB
# It will also create a Stripe session where the user can actually pay for things
# The function is filled with comments that explain each step


@app.route("/api/stripeSession", methods=["POST"])
def checkout():
    # The front end will send an array of numbers
    # These numbers will correspond to product id's in my DB
    items_ids = request.json.get("item_ids")
    # Setting up all the variables to be used in the try section
    selected_items = []
    cursor = None
    conn = None
    purchases = None
    purchase_rows = 0
    errored = False
    checkout_session = None
    # Check to see if the length of the items sent is 0
    # If there are 0 items, simply return the function right here.
    if len(items_ids) == 0:
        return Response(
            json.dumps("You must send some items!", default=str),
            mimetype="application/json",
            status=400,
        )
    try:
        # Connect to the DB
        conn = mariadb.connect(
            user=dbcreds.user,
            password=dbcreds.password,
            host=dbcreds.host,
            port=dbcreds.port,
            database=dbcreds.database,
        )
        cursor = conn.cursor()
        # For each item in the items sent to me by the front end run a SELECT
        # We could make this more efficient with OR statements, but this is more clear
        for item_id in items_ids:
            # Execute the SELECT for that particular item
            # Obviously you will need to modify this to match your DB columns and tables
            cursor.execute(
                "SELECT * FROM items where id=?",
                [
                    item_id,
                ],
            )
            # Fetch the one item from the DB that matches the id
            item = cursor.fetchone()
            # Start adding to our selected_items array we created at the top as []
            selected_items.append(
                # Create a dictionary in the form that stripe expects to see with the DB data
                {
                    "price_data": {
                        # This item is CAD currentcy
                        "currency": "cad",
                        # The unit_amount is the price in cents gotten from the DB
                        "unit_amount": item[3],
                        # Extra product data like the name and images for stripe to show
                        "product_data": {"name": item[2], "images": [item[4]]},
                    },
                    # The quantity of the items being purchased
                    "quantity": 1,
                }
            )
        # Finally we can create the Stripe session that will be used by the customer
        # We use our checkout_session variable and use the stripe library to create a session
        # If you want to see the docs for a session, go here and select Python as the language:
        # https://stripe.com/docs/api/checkout/sessions/create
        checkout_session = stripe.checkout.Session.create(
            # Accepted payment methods, simple card for me only
            payment_method_types=["card"],
            # Telling stripe to collect billing info like address
            billing_address_collection="required",
            # Restrict to CA and US addresses only
            shipping_address_collection={
                "allowed_countries": ["US", "CA"],
            },
            # The actual items being bought
            # We use the items we SELECT from the DB above
            line_items=selected_items,
            # We are in payment mode (as opposed to things like refund)
            mode="payment",
            # Where to send the user when the call works or doesn't
            # Make sure you set this to your actual domain name when you release!
            success_url="http://localhost:8080/#/success",
            cancel_url="http://localhost:8080/#/failure",
        )
        # For those of you who are storing the payment info in their DB and not just using stripe
        # We store each item as a purchase with the unique payment_intent stripe generates for us
        stripe_intent_id = checkout_session.payment_intent
        # For each item the customer is purchases, we create a row in our DB
        # Again can be made more efficient but this is more clear
        # This stripe_intent_id is used by the webhook later to identify a particular customer.
        for item_id in items_ids:
            # Obviously you will need to modify this to match your DB columns and tables
            cursor.execute(
                "INSERT INTO purchase (item_id, stripe_intent_id) VALUES (?,?)",
                [item_id, stripe_intent_id],
            )
            conn.commit()
            # Add up the rows for each insert so we can check at the end that each purchase was inserted
            purchase_rows += cursor.rowcount
        # Update our purcahses variable to be the length of them item ids sent by the front end
        # This is what we will compare our purchase_rows to.
        purchases = len(items_ids)
    except Exception as e:
        print(e)
        # If an error occurs, set the errored variable to true
        errored = True
    finally:
        # Standard checks to close our DB resources
        if cursor != None:
            cursor.close()
        if conn != None:
            conn.rollback()
            conn.close()
        # If errored is True, we send an error message to the user
        if errored:
            return Response(
                json.dumps({"message": "Stripe session error!"}),
                mimetype="application/json",
                status=403,
            )
        # If the amount of id's sent by the user is the same as the amount INSERT in the DB
        # We can send back a success
        if purchase_rows == purchases:
            return Response(
                # VERY IMPORTANT
                # We need to send back the checkout_session.id back to the user so they know what stripe page to redirect to
                json.dumps({"id": checkout_session.id}),
                mimetype="application/json",
                status=200,
            )
        # If they are not equal something went wrong
        # Chances are here you want to check the DB and DELETE anything related to this request
        else:
            return Response(
                json.dumps({"message": "Database error!"}),
                mimetype="application/json",
                status=403,
            )


# For the advanced users who want to track their own payments on top of Stripe
# We register a web hook that Stripe will use every time a payment occurs
# Essentially any time someone interacts with your Stripe payment this web hook will be called
# This webhook will send customer information to your backend when payments occur

# https://stripe.com/docs/webhooks
# https://stripe.com/docs/webhooks/integration-builder
@app.route("/api/stripeHook", methods=["POST"])
def stripeHook():
    # This is how Stripe wants you to collect the data of the request
    event = None
    payload = request.data
    try:
        event = json.loads(payload)
    except:
        print("There was a webhook error!")
        return Response(status=200)
    # We check the event type to see if it is a charge.succeeded
    # There are tons of different events most of which we don't care about
    # https://stripe.com/docs/api/events/types
    if event and event["type"] == "charge.succeeded":
        # Nice print statement for debugging
        print("Payment Success! Time to fufill the order and put things in the DB")
        # PRO TIP if you want to print JSON in a nice readable way, this is how
        print(json.dumps(event, indent=3, sort_keys=True))
        # Collect the payment_intent generated before and stored in the DB
        stripe_payment_id = event["data"]["object"]["payment_intent"]
        # Collect the email or whatever else you want to collect from the customer info
        customer_email = event["data"]["object"]["billing_details"]["email"]
        # Call the update_customer_purchase function defined at the top to UPDATE the purchase records
        update_customer_purchase(stripe_payment_id, customer_email)
    # For all other events, we just do some simple debug prints
    # Thes aren't really our errors, it just means the payment failed
    elif event and event["type"] == "charge.failed":
        # If the charge has failed, you might want to go DELETE the purchase based on the payment_intent
        # Unless you want to keep failed payments as well
        print("Payment Fail!")
        print(json.dumps(event, indent=3, sort_keys=True))
    else:
        print("No Logic for this one, might want to create some!")
        print(json.dumps(event, indent=3, sort_keys=True))
    # Tell stripe thanks all good here
    return Response(status=200)
