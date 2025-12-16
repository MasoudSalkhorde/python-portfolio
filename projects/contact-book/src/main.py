from src.utils.contact_book import ContactBook

def main():
    book = ContactBook()

    while True:
        print("\n=== Contact Book App ===")
        print("1. Add contact")
        print("2. Edit contact")
        print("3. View contacts")
        print("4. Delete contact")
        print("5. Quit")

        user_choice = input("Select an option: ").strip()

        if user_choice == "5":
            print("Goodbye!")
            break

        elif user_choice == "1":
            name = input("Enter name: ").strip()
            phone = input("Enter phone: ").strip()
            email = input("Enter email: ").strip()
            book.add_contact(name, phone, email)

        elif user_choice == "2":
            name = input("Enter name: ").strip()
            phone = input("Enter new phone: ").strip()
            email = input("Enter new email: ").strip()
            book.update_contact(name, phone, email)

        elif user_choice == "3":
            book.view_contacts()

        elif user_choice == "4":
            name = input("Enter name: ").strip()
            book.delete_contact(name)

        else:
            print("❌ Invalid option. Please try again.")

if __name__ == "__main__":
    main()
