# Dependencies
import sys
import datetime as dt
import pandas as pd
import numpy as np
from library.authorize.config import api_id, api_key
from library.authorize.api import UnleashedApi


def file_input():
    file_import = True
    while file_import:
        # User input to get excel file name
        global excel_file_name
        excel_file_name = input("Please enter in the excel file name: ")

        # Enter to exit program
        exit_strat = ["quit", "cancel", "exit"]
        if excel_file_name in exit_strat:
            sys.exit(1)

        # Excel file path
        excel_path = f"product_list_import/{excel_file_name}.xlsx"

        try:
            # Read excel file as df
            # Keep blank rows for easy copy and paste
            global product_df
            product_df = pd.read_excel(excel_path, skip_blank_lines=False)

            # Stop file_import loop
            file_import = False

        except FileNotFoundError:
            print("Sorry, there is no such file in directory. Please try again.\n")

    # Run pick_enquiry function to choose which enquiry to run
    pick_enquiry()

    return excel_file_name, product_df


def pick_enquiry():
    # Potential user response lists
    bom_responses = ["bom", "boms", "billofmaterials", "bill", "bills"]
    soh_responses = ["soh", "stockonhand", "stock", "stocks", "quantity"]

    choice = True

    while choice:
        # User input to choose what enquiry to run
        enquiry = input("Which enquiry do you want to run, Bill of Materials or Stock On Hand? ")

        # Canonicalize enquiry
        enquiry = enquiry.replace(" ", "").lower()

        if enquiry in bom_responses:
            # Run Bill Of Materials Program
            print("\nAwesome! Now sifting through Unleashed. This may take a minute.")
            get_bom(product_df)
            break
        elif enquiry in soh_responses:
            # Run Stock On Hand Program
            print("\nAwesome! Now sifting through Unleashed. This may take a minute.")
            get_soh(product_df)
            break
        # elif enquiry in des_responses:
            # Run Product Description Program
            # print("\nAwesome! Now sifting through Unleashed. This may take a minute.")
            # get_des(product_df)
            # break
        else:
            print("Uh oh. There was probably a misspelling. Please try again.\n")


def run_order(product_df):
    # Potential user response lists
    yes_list = ["yes", "y", "yep", "yeah", "yea", "sure",
                "ya", "yah", "ye", "affirmative", "absolutely"]
    no_list = ["no", "n", "na", "nah", "nope", "never", "no way", "nein"]
    so_responses = ["so", "sale", "sales", "salesorders", "saleorder", "salesorder"]
    po_responses = ["po", "purchase", "purchases", "purchaseorders", "purch", "pos"]
    both = ["both", "all", "two", "everything"]

    ask_order = True

    while ask_order:
        # Ask to get order quantities
        response = input("\nDo you want to get quantities on orders? (yes/no): ")

        if response in yes_list:

            choice = True

            while choice:
                # User input to choose what enquiry to run
                enquiry = input(
                    "Which enquiry do you want to run: Sales Orders, Purchase Orders, or Both? ")

                # Canonicalize enquiry
                enquiry = enquiry.replace(" ", "").lower()

                if enquiry in so_responses:
                    # Run Bill Of Materials Program
                    # print("\nAwesome! Now sifting through Unleashed. This may take a minute.")
                    get_sales(product_df)
                    choice = False
                    ask_order = False
                elif enquiry in po_responses:
                    # Run Stock On Hand Program
                    # print("\nAwesome! Now sifting through Unleashed. This may take a minute.")
                    get_purchases(product_df)
                    choice = False
                    ask_order = False
                # elif enquiry in both:
                #     # Run Product Description Program
                #     # print("\nAwesome! Now sifting through Unleashed. This may take a minute.")
                #     get_des(product_df)
                #     choice = False
                #     ask_order = False
                else:
                    print("Uh oh. There was probably a misspelling. Please try again.\n")

        elif response in no_list:
            # Run export_to_excel function to grab final file
            export_to_excel(product_df)

        elif (response not in no_list) and (response not in yes_list):
            print("It was a yes or no question. Try again.\n")

        else:
            print("Umm. Something went wrong. Imma dip, peace out.")
            break


'''
Below exports completed dataframe to an excel file.
'''


def export_to_excel(dataframe):
    # Grab datetime
    today = dt.datetime.now().strftime(format="%Y%m%d")

    try:
        # Save as csv
        dataframe.to_excel(f"unl_enquiry/{today}_unl_{excel_file_name}.xlsx", index=False)
    except PermissionError:
        print("Oh no. You already have the file open! Close it and try again.")
    except:
        raise

    # Print to console
    print("\nCompleted! Here are the top few rows:")
    print("-" * 40)
    print(dataframe.head().to_string(index=False))
    print("-" * 40 + "\n")


'''
Below grabs product descriptions and returns a dataframe.
'''


def get_des(product_df):

    # Run get_des_response function
    print("\nGrabbing product descriptions...")

    # Unleashed api base url
    api_url = "https://api.unleashedsoftware.com"

    # Authorize and connect to api
    auth = UnleashedApi(api_url, api_id, api_key)

    # Keep track of number of items
    item_count = 0

    # Paginate through arbitrary large number
    for x in range(100):

        # Get response
        products = auth.get_request(method=f"Products/{x+1}?").json()

        # Add number of orders to item count
        item_count += len(products["Items"])

        for item in products["Items"]:

            for i, product in enumerate(product_df["Product Code"]):

                if item["ProductCode"] == product:

                    # product_df.iat[i, 1] = item["ProductDescription"]
                    product_df.at[product_df.index[i], "Description"] = item["ProductDescription"]

        # Break loop if item_count hits max number of orders
        if item_count == products["Pagination"]["NumberOfItems"]:
            break

    # Return product_df
    return product_df


'''
Below contains bill of materials program.
'''


def get_bom_response():
    # Unleashed api base url
    api_url = "https://api.unleashedsoftware.com"

    # Authorize and connect to api
    auth = UnleashedApi(api_url, api_id, api_key)

    # Get response
    bills_of_materials = auth.get_request(method="BillOfMaterials?").json()

    return bills_of_materials


def get_bom(product_df):

    # Run get_bom_response function
    print("\nExtracting bills of materials...")
    bills_of_materials = get_bom_response()

    # Create dictionary to hold list of line items for each product in product_df
    bom_dict = {}

    # Append each product in product_df to bom_list as dictionaries
    for product in product_df["Product Code"]:
        # Add product as key with the value as a list
        bom_dict[product] = []

    # First run to grab bom line items of final product
    for product, line_list in bom_dict.items():
        for bill in bills_of_materials["Items"]:
            if bill["Product"]["ProductCode"] == product:
                for line in bill["BillOfMaterialsLines"]:
                    line_item = line["Product"]["ProductCode"]
                    if line_item != 'LBR':
                        line_list.append(line_item)

    # Find bill of materials for those line items
    for product, line_list in bom_dict.items():
        # For each line item in line item list
        for i, item in enumerate(line_list):
            # Loop through products bills in response
            for bill in bills_of_materials["Items"]:
                # If product code in response matches line item name
                if bill["Product"]["ProductCode"] == item:
                    # For each line item in the bom lines, reversed
                    for line in reversed(bill["BillOfMaterialsLines"]):
                        # Assign line item as variable
                        line_item = line["Product"]["ProductCode"]
                        # Don't want labor SKU
                        if line_item != 'LBR':
                            # Insert line item into line item list in bom_dict
                            line_list.insert(i + 1, line_item)

    # See if we can append bom_list after each product in original excel file
    product_list = [product for product in product_df["Product Code"]]

    # Create a final bom list
    full_bom_list = []

    # Separate final products by an em-dash
    for i, final_prod in enumerate(product_list):
        for key, value in bom_dict.items():
            if final_prod == key:
                full_bom_list.append(key)
                for line in value:
                    full_bom_list.append(line)
                full_bom_list.append("—")

    # Create bom dataframe
    bom_df = pd.DataFrame({"Product Code": full_bom_list})

    # Run get_soh function to grab descriptions and stock counts
    get_soh(bom_df)


'''
Below contains stock on hand program.
'''


def get_soh(product_df):
    # Grab product descriptions
    get_des(product_df)

    # Unleashed api base url
    api_url = "https://api.unleashedsoftware.com"

    # Authorize and connect to api
    auth = UnleashedApi(api_url, api_id, api_key)

    # Add new blank column
    product_df["Quantity On Hand"] = ""

    print("\nNow sending someone to count the stock by hand...lol jk")

    # Keep track of number of items
    item_count = 0

    # Paginate through arbitrary large number
    for x in range(100):

        # Get response
        stock_on_hand = auth.get_request(method=f"StockOnHand/{x+1}?").json()

        # Add number of orders to item count
        item_count += len(stock_on_hand["Items"])

        # Grab list of product to enquire
        product_list = product_df["Product Code"]

        # Grab quantity on hand from api response
        for i, product in enumerate(product_list):
            for item in stock_on_hand["Items"]:
                if product == item["ProductCode"]:
                    try:
                        # df.set_value() is deprecated
                        # product_df.set_value(i, "Quantity On Hand", item["QtyOnHand"])
                        # product_df.iat[i, 1] = item["QtyOnHand"]
                        product_df.at[product_df.index[i], "Quantity On Hand"] = item["QtyOnHand"]
                    except Exception as e:
                        print(e)
                        continue

        # Break loop if item_count hits max number of orders
        if item_count == stock_on_hand["Pagination"]["NumberOfItems"]:
            break

    # Reorder columns
    product_df = product_df[["Product Code", "Description", "Quantity On Hand"]]

    # Run export_to_excel function to grab final file
    # export_to_excel(product_df)

    # Return product_df
    # return product_df

    # Run run_order function
    run_order(product_df)


'''
Below contains get sales program.
'''


def get_sales(product_df):

    # Run get_des_response function
    print("\nGrabbing order quantities on sales...")

    # Unleashed api base url
    api_url = "https://api.unleashedsoftware.com"

    # Authorize and connect to api
    auth = UnleashedApi(api_url, api_id, api_key)

    # Create dictionary to hold order quantities for each product
    order_quantity_dict = {}

    # Append each product in product_df to order_quantity_dict as dictionaries
    for product in product_df["Product Code"]:
        # Add product as key with the value as a list
        order_quantity_dict[product] = []

    # Debug statement
    # print(order_quantity_dict)

    # Create order status variable for query
    order_status = "Parked,Placed,Backordered"

    # Keep track of number of items
    item_count = 0

    # Paginate through arbitrary large number
    for x in range(100):

        # Get response
        sales_orders = auth.get_request(
            method=f"SalesOrders/{x+1}?orderStatus={order_status}&pageSize=200").json()

        # Add number of orders to item count
        item_count += len(sales_orders["Items"])

        # Debug statements
        # print("Length of page: {}".format(len(purchase_orders["Items"])))
        # print(f"Total item count: {item_count}")

        for product, order_quantity_list in order_quantity_dict.items():

            for order in sales_orders["Items"]:

                if order["OrderStatus"] != "Complete":

                    for line in order["SalesOrderLines"]:

                        if line["Product"]["ProductCode"] == product:

                            # Append order quantity to list in order quantity dictionary
                            order_quantity_list.append(line["OrderQuantity"])

        # Break loop if item_count hits max number of orders
        if item_count == sales_orders["Pagination"]["NumberOfItems"]:
            break

    # Debug statement
    # print(order_quantity_dict)

    # Add new blank column
    product_df["Quantity On Sales"] = ""

    for i, product in enumerate(product_df["Product Code"]):

        for key, order_quantity_list in order_quantity_dict.items():

            if product == "—":
                # Insert nan at index
                product_df.at[product_df.index[i], "Quantity On Sales"] = np.nan

            elif product == key:
                # Insert quantity at index
                product_df.at[product_df.index[i],
                              "Quantity On Sales"] = sum(order_quantity_list)

    # Reorder columns
    product_df = product_df[["Product Code", "Description",
                             "Quantity On Hand", "Quantity On Sales"]]

    # Run export_to_excel function to grab final file
    export_to_excel(product_df)

    # Return product_df
    # return product_df


'''
Below contains get purchases program.
'''


def get_purchases(product_df):

    # Run get_des_response function
    print("\nGrabbing order quantities on purchase...")

    # Unleashed api base url
    api_url = "https://api.unleashedsoftware.com"

    # Authorize and connect to api
    auth = UnleashedApi(api_url, api_id, api_key)

    # Create dictionary to hold order quantities for each product
    order_quantity_dict = {}

    # Append each product in product_df to order_quantity_dict as dictionaries
    for product in product_df["Product Code"]:
        # Add product as key with the value as a list
        order_quantity_dict[product] = []

    # Debug statement
    # print(order_quantity_dict)

    # Keep track of number of items
    item_count = 0

    # Paginate through arbitrary large number
    for x in range(100):

        # Get response
        purchase_orders = auth.get_request(method=f"PurchaseOrders/{x+1}?").json()

        # Add number of orders to item count
        item_count += len(purchase_orders["Items"])

        # Debug statements
        # print("Length of page: {}".format(len(purchase_orders["Items"])))
        # print(f"Total item count: {item_count}")

        for product, order_quantity_list in order_quantity_dict.items():

            for order in purchase_orders["Items"]:

                if order["OrderStatus"] != "Complete":

                    for line in order["PurchaseOrderLines"]:

                        if line["Product"]["ProductCode"] == product:

                            # Append order quantity to list in order quantity dictionary
                            order_quantity_list.append(line["OrderQuantity"])

        # Break loop if item_count hits max number of orders
        if item_count == purchase_orders["Pagination"]["NumberOfItems"]:
            break

    # Debug statement
    # print(order_quantity_dict)

    # Add new blank column
    product_df["Quantity On Purchase"] = ""

    for i, product in enumerate(product_df["Product Code"]):

        for key, order_quantity_list in order_quantity_dict.items():

            if product == "—":
                # Insert nan at index
                product_df.at[product_df.index[i], "Quantity On Purchase"] = np.nan

            elif product == key:
                # Insert quantity at index
                product_df.at[product_df.index[i],
                              "Quantity On Purchase"] = sum(order_quantity_list)

    # Reorder columns
    product_df = product_df[["Product Code", "Description",
                             "Quantity On Hand", "Quantity On Purchase"]]

    # Run export_to_excel function to grab final file
    export_to_excel(product_df)

    # Return product_df
    # return product_df
