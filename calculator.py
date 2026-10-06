import tkinter as tk

# ---------- Functions ----------
def button_click(value):
    """Add the clicked button's value to the display."""
    current = display.get()
    display.delete(0, tk.END)
    display.insert(0, current + str(value))

def clear_display():
    """Clear the display."""
    display.delete(0, tk.END)

def calculate():
    """Evaluate the expression in the display."""
    try:
        result = eval(display.get())
        display.delete(0, tk.END)
        display.insert(0, str(result))
    except Exception:
        display.delete(0, tk.END)
        display.insert(0, "Error")

# ---------- Main Window ----------
root = tk.Tk()
root.title("Simple Calculator")
root.geometry("300x400")
root.configure(bg="#2b2b2b")

# ---------- Display ----------
display = tk.Entry(root, font=("Arial", 24), borderwidth=5,
                   relief="ridge", justify="right", bg="#ffffff")
display.grid(row=0, column=0, columnspan=4, padx=10, pady=10, ipady=10)

# ---------- Button Layout ----------
buttons = [
    ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
    ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
    ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
    ("0", 4, 0), (".", 4, 1), ("=", 4, 2), ("+", 4, 3),
]

# ---------- Create Buttons ----------
for (text, row, col) in buttons:
    if text == "=":
        action = calculate
        color = "#4CAF50"   # green
    else:
        action = lambda t=text: button_click(t)
        color = "#3c3f41" if text in "+-*/" else "#555555"

    tk.Button(root, text=text, font=("Arial", 18),
              bg=color, fg="white", command=action,
              width=5, height=2).grid(row=row, column=col, padx=3, pady=3)

# ---------- Clear Button ----------
tk.Button(root, text="C", font=("Arial", 18), bg="#d9534f", fg="white",
          command=clear_display, width=5, height=2).grid(
          row=5, column=0, columnspan=4, padx=3, pady=3, sticky="we")

# ---------- Run the App ----------
root.mainloop()