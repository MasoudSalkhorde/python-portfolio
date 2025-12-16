from collections import defaultdict

class ContactBook():
    def __init__(self):
        self.contacts = defaultdict(dict)
    
    def add_contact(self, name, phone, email=None):
        if name in self.contacts:
            print("Contact already exists")
            return
        self.contacts[name]["phone"] = phone
        self.contacts[name]["email"] = email
        
    def view_contacts(self):
        for name, info in self.contacts.items():
            print(f"Name: {name}")
            print(f"Email: {info["email"]}")
            print(f"Phone: {info["phone"]}")
            print("-"*50)
    
    def delete_contact(self, name):
        if name in self.contacts:
            del self.contacts[name]
            print("Contact deleted successfuly!")
        else: 
            print("This contact does not exit")
            
    def update_contact(self, name, phone=None, email=None):
        if name in self.contacts:
            if phone:
                self.contacts[name]['phone'] = phone
            if email:
                self.contacts[name]['email'] = email
            print("Contact is updated successfuly")
        else:
            print("Contact does not exit")    