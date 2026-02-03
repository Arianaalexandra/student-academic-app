import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# vezi structura tabelei
cursor.execute("PRAGMA table_info(grades)")
columns = cursor.fetchall()

print("Coloane existente:")
for col in columns:
    print(col)

# verificăm dacă există coloana email
column_names = [col[1] for col in columns]

if "email" not in column_names:
    print("Adaug coloana email...")
    cursor.execute("ALTER TABLE grades ADD COLUMN email TEXT")
    conn.commit()
    print("Coloana email a fost adăugată.")
else:
    print("Coloana email există deja.")

# dacă există student_email, copiem datele
if "student_email" in column_names:
    print("Copiez datele din student_email în email...")
    cursor.execute("""
        UPDATE grades
        SET email = student_email
        WHERE email IS NULL
    """)
    conn.commit()
    print("Datele au fost copiate.")

conn.close()
print("GATA ✔")
