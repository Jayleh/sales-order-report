# Dependencies
import sys
import datetime as dt
import pandas as pd
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
            convert_bom(product_df)
            break
        elif enquiry in soh_responses:
            # Run Stock On Hand Program
            print("\nAwesome! Now sifting through Unleashed. This may take a minute.")
            convert_soh(product_df)
            break
        # elif enquiry in des_responses:
            # Run Product Description Program
            # print("\nAwesome! Now sifting through Unleashed. This may take a minute.")
            # get_des(product_df)
            # break
        else:
            print("Uh oh. There was probably a misspelling. Please try again.\n")


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
        print("Oh no. You have the file already open! Close it and try again.")
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

    # Paginate through 5 pages
    for x in range(5):

        # Get response
        products = auth.get_request(method=f"Products/{x+1}?").json()

        for item in products["Items"]:

            for i, product in enumerate(product_df["Product Code"]):

                if item["ProductCode"] == product:

                    # product_df.iat[i, 1] = item["ProductDescription"]
                    product_df.at[product_df.index[i], "Description"] = item["ProductDescription"]

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


def convert_bom(product_df):

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

    # Run convert_soh function to grab descriptions and stock counts
    convert_soh(bom_df)


'''
Below contains stock on hand program. 
'''


def get_soh_response():
    # Unleashed api base url
    api_url = "https://api.unleashedsoftware.com"

    # Authorize and connect to api
    auth = UnleashedApi(api_url, api_id, api_key)

    # Get response
    stock_on_hand = auth.get_request(method="StockOnHand/1?pageSize=1000").json()

    return stock_on_hand


def convert_soh(product_df):
    # Grab product descriptions
    get_des(product_df)

    # Run get_soh_response function
    print("\nNow sending someone to count the stock by hand...lol jk")
    stock_on_hand = get_soh_response()

    # Add new blank column
    product_df["Quantity On Hand"] = ""

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

    # Reorder columns
    product_df = product_df[["Product Code", "Description", "Quantity On Hand"]]

    # Run export_to_excel function to grab final file
    export_to_excel(product_df)
