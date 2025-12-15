# Contact Book (Python)

A simple **CLI Contact Book** built in Python that lets you **add, view, search, update, delete, import/export** contacts, with data persisted to a JSON file.

---

## Features

- ✅ Add a contact (name, phone, email, address, tags, notes)
- ✅ List all contacts (sorted)
- ✅ Search contacts (by name / phone / email / tags)
- ✅ Update a contact
- ✅ Delete a contact
- ✅ Prevent duplicates (configurable)
- ✅ Save/load contacts automatically (JSON)
- ✅ Export to CSV / Import from CSV

---

## Demo (example)

```bash
$ python -m src.main
1) Add contact
2) List contacts
3) Search
4) Update
5) Delete
6) Import CSV
7) Export CSV
0) Exit
```

## Project Structure
```
contact-book/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ data/
│  └─ contacts.json
└─ src/
   ├─ main.py
   ├─ contact.py
   ├─ contact_book.py
   └─ utils/
        └─contant.py
```
## Getting Started
Clone and run
```
git clone <your-repo-url>
cd contact-book
python -m src.main
```
## 📦 Requirements

- Python 3.6+

## 📄 License

You are free to use, modify, and distribute this project.
