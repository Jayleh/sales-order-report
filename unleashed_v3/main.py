# Dependencies
from library.enquiry import file_input


"""Bill Of Materials Program .

Must place excel file in the "product_list_import" folder. Processed files may be found in the
"unl_enquiry" folder named with the timestamp and its original file name.

When asked to enter file name, you may exit the program by typing "cancel" or "exit"."""


def run_enquiry():
    # Potential user response lists
    yes_list = ["yes", "y", "yep", "yeah", "yea", "sure",
                "ya", "yah", "ye", "affirmative", "absolutely"]
    no_list = ["no", "n", "na", "nah", "nope", "never", "no way", "nein"]

    # Execute Code
    run_program = True

    while run_program:
        # Run file_input function
        file_input()

        # Ask to run again
        again = True

        while again:
            run_again = input("Do you want to run another file? (y/n): ").lower()
            if run_again in yes_list:
                print("\nOkay, let's do it.")
                again = False
            elif run_again in no_list:
                print("\nThanks for using Unleashed The Program! Have a good one.")
                again = False
                run_program = False
            elif (run_again not in no_list) and (run_again not in yes_list):
                print("It was a yes or no question. Try again.\n")
            else:
                print("Umm. Something went wrong. Imma dip, peace out.")
                again = False
                run_program = False


if __name__ == '__main__':
    print("Welcome to Unleashed The Program!\n")
    run_enquiry()
