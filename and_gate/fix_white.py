with open("generate_pdf.py", encoding="utf-8") as f:
    txt = f.read()

# Fix: fg='white' -> fg='#ffffff'
txt = txt.replace("fg='white'", "fg='#ffffff'")
txt = txt.replace('fg="white"', 'fg="#ffffff"')

with open("generate_pdf.py", "w", encoding="utf-8") as f:
    f.write(txt)
print("Fixed!")

