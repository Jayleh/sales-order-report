import os
import datetime as dt
import pandas as pd
from unleashed import api_id, api_key
from unleashed.api import UnleashedApi


def check_folder():
    path = 'unleashed/static/doc/import'
    files = os.listdir(path)

    try:
        for file in files:
            if file != ".gitignore":
                return file
    except IndexError:
        print("No file uploaded.")


def convert_to_dataframe():
    filename = check_folder()

    product_df = pd.read_excel(f"unleashed/static/doc/import/{filename}", skip_blank_lines=False)

    return product_df


def configure_request():
    # Unleashed api base url
    api_url = "https://api.unleashedsoftware.com"

    # Authorize and connect to api
    auth = UnleashedApi(api_url, api_id, api_key)

    return auth


def get_bom_response():
    """
    API request for bill of materials. Returns all.
    """

    # Authorize and connect to api
    auth = configure_request()

    # Get response
    bills_of_materials = auth.get_request(method="BillOfMaterials?includeObsolete=false").json()

    return bills_of_materials


def get_bom(bills_of_materials):
    """
    Unzips all bill of materials associated with each product in original excel file.
    Call stock on hand request. *For loops subject to debugging
    """

    # Get initial dataframe from excel upload file
    product_df = convert_to_dataframe()

    # Create dictionary to hold list of line items for each product in product_df
    bom_dict = {}

    # Append each product in product_df to bom_list as dictionaries
    for product in product_df["Product Code"]:
        # Add product as key with the value as a list
        bom_dict[product] = []

    unit_cost = {}

    # First run to grab bom line items of final product
    for product, line_list in bom_dict.items():
        for bill in bills_of_materials["Items"]:
            if bill["Product"]["ProductCode"] == product:
                unit_cost[product] = bill["Product"]["LastCost"]
                for line in bill["BillOfMaterialsLines"]:
                    line_item = line["Product"]["ProductCode"]
                    line_item_cost = line["UnitCost"]
                    if line_item != 'LBR':
                        line_list.append(line_item)
                        unit_cost[line_item] = line_item_cost

    # Find bill of materials for those line items
    for product, line_list in bom_dict.items():
        # For each line item in line item list
        for i, item in enumerate(line_list):
            # Loop through products bills in response
            for bill in bills_of_materials["Items"]:
                # If product code in response matches line item name
                if bill["Product"]["ProductCode"] == item:
                    unit_cost[item] = bill["Product"]["LastCost"]
                    # For each line item in the bom lines, reversed
                    for line in reversed(bill["BillOfMaterialsLines"]):
                        # Assign line item as variable
                        line_item = line["Product"]["ProductCode"]
                        line_item_cost = line["UnitCost"]
                        # Don't want labor SKU
                        if line_item != 'LBR':
                            # Insert line item into line item list in bom_dict
                            line_list.insert(i + 1, line_item)
                            unit_cost[line_item] = line_item_cost

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

    bom_df["Unit Cost"] = ""

    for i, row in bom_df.iterrows():
        for product, cost in unit_cost.items():
            if row["Product Code"] == product:
                bom_df.at[bom_df.index[i], "Unit Cost"] = cost

    return bom_df


def get_soh_response():
    """
    API request for bill of materials. Returns all.
    """

    # Authorize and connect to api
    auth = configure_request()

    # All item quantity list
    item_list = []

    # Paginate through arbitrary large number
    for x in range(100):

        # Get response
        stock_on_hand = auth.get_request(method=f"StockOnHand/{x+1}?").json()

        # Add items to item_list
        for item in stock_on_hand["Items"]:
            item_list.append(item)

        # Break loop if item_count hits max number of orders
        if stock_on_hand["Pagination"]["PageNumber"] == stock_on_hand["Pagination"]["NumberOfPages"]:
            break

    # Stock on hand dictionary
    soh_dict = {"Items": item_list}

    return soh_dict


def get_soh(product_df, soh_dict):
    """
    Adds new column of quantity on hand. Calls pick_order function.
    """

    auth = configure_request()

    # Add product description and quantity on hand columns
    product_df["Description"] = ""
    product_df["Quantity On Hand"] = ""
    product_df["Allocated Quantity"] = ""
    product_df["Available Quantity"] = ""

    print("Counting stock on hand...")

    # Grab list of product to enquire
    product_list = product_df["Product Code"]

    # Grab quantity on hand from api response
    for i, product in enumerate(product_list):
        for item in soh_dict['Items']:
            if product == item["ProductCode"]:
                try:
                    product_df.at[product_df.index[i],
                                  "Description"] = item["ProductDescription"]
                    product_df.at[product_df.index[i], "Quantity On Hand"] = item["QtyOnHand"]
                    product_df.at[product_df.index[i],
                                  "Allocated Quantity"] = item["AllocatedQty"]
                    product_df.at[product_df.index[i],
                                  "Available Quantity"] = item["AvailableQty"]
                except Exception as e:
                    print(e)
                    continue

    # Return product_df
    return product_df


def get_sales(product_df):
    """
    API request for sales order data. Adds sales order quantity column to dataframe.
    """

    # Debug statement
    print("Inserting order quantities on sales orders...")

    auth = configure_request()

    # Create dictionary to hold order quantities for each product
    order_quantity_dict = {}

    # Append each product in product_df to order_quantity_dict as dictionaries
    for product in product_df["Product Code"]:
        # Add product as key with the value as a list
        order_quantity_dict[product] = []

    # Create order status variable for query
    order_status = "Parked,Placed,Backordered"

    # Paginate through arbitrary large number
    for x in range(100):

        # Get response
        sales_orders = auth.get_request(
            method=f"SalesOrders/{x+1}?orderStatus={order_status}&pageSize=200").json()

        for product, order_quantity_list in order_quantity_dict.items():

            for order in sales_orders["Items"]:

                if order["OrderStatus"] != "Complete":

                    for line in order["SalesOrderLines"]:

                        if line["Product"]["ProductCode"] == product:

                            # Append order quantity to list in order quantity dictionary
                            order_quantity_list.append(line["OrderQuantity"])

        # Break loop if item_count hits max number of orders
        if sales_orders["Pagination"]["PageNumber"] == sales_orders["Pagination"]["NumberOfPages"]:
            break

    # Add new blank column
    product_df["Quantity On Sales"] = ""

    for i, product in enumerate(product_df["Product Code"]):

        for key, order_quantity_list in order_quantity_dict.items():

            if product == "—":
                # Insert nan at index
                product_df.at[product_df.index[i], "Quantity On Sales"] = ""

            elif product == key:
                # Insert quantity at index
                product_df.at[product_df.index[i],
                              "Quantity On Sales"] = sum(order_quantity_list)

    # Return product_df
    return product_df


def get_purchases(product_df):
    """
    API request for purchase orders data. Adds purchase order quantity column to dataframe.
    """

    # Debug statement
    print("Reading in order quantities on purchase orders...")

    auth = configure_request()

    # Create dictionary to hold order quantities for each product
    order_quantity_dict = {}

    # Append each product in product_df to order_quantity_dict as dictionaries
    for product in product_df["Product Code"]:
        # Add product as key with the value as a list
        order_quantity_dict[product] = []

    # Debug statement
    # print(order_quantity_dict)

    last_year = dt.datetime.now().year - 1

    # Paginate through arbitrary large number
    for x in range(100):

        # Get response
        purchase_orders = auth.get_request(
            method=f"PurchaseOrders/{x+1}?startDate={last_year}-01-01").json()

        for product, order_quantity_list in order_quantity_dict.items():

            for order in purchase_orders["Items"]:

                if order["OrderStatus"] != "Complete":

                    for line in order["PurchaseOrderLines"]:

                        if line["Product"]["ProductCode"] == product:

                            # Append order quantity to list in order quantity dictionary
                            order_quantity_list.append(line["OrderQuantity"])

        # Break loop if item_count hits max number of orders
        if purchase_orders["Pagination"]["PageNumber"] == purchase_orders["Pagination"]["NumberOfPages"]:
            break

    # Add new blank column
    product_df["Quantity On Purchases"] = ""

    for i, product in enumerate(product_df["Product Code"]):

        for key, order_quantity_list in order_quantity_dict.items():

            if product == "—":
                # Insert nan at index
                product_df.at[product_df.index[i], "Quantity On Purchases"] = ""

            elif product == key:
                # Insert quantity at index
                product_df.at[product_df.index[i],
                              "Quantity On Purchases"] = sum(order_quantity_list)

    # Reorder columns
    product_df = product_df[["Product Code", "Description", "Quantity On Hand", "Allocated Quantity",
                             "Available Quantity", "Quantity On Sales", "Quantity On Purchases", "Unit Cost"]]

    # Return product_df
    return product_df
