import nbformat
from itertools import zip_longest

# Lade beide Notebooks
code_nb = nbformat.read("notebooks/00_main_code.ipynb", as_version=4)
text_nb = nbformat.read("notebooks/00_main.ipynb", as_version=4)

# Neue Zellenliste erstellen
merged_cells = []

for code_cell, text_cell in zip_longest(code_nb.cells, text_nb.cells):
    if code_cell and text_cell:
        merged_cell = code_cell.copy()
        if text_cell.cell_type == "markdown":
            if merged_cell.cell_type == "markdown":
                merged_cell.source = text_cell.source
            else:
                # Wenn Code-Zelle, aber Text-Zelle markdown ist → beide behalten
                merged_cells.append(merged_cell)
                merged_cells.append(nbformat.v4.new_markdown_cell(source=text_cell.source))
                continue
        merged_cells.append(merged_cell)
    
    elif code_cell:
        merged_cells.append(code_cell)
    
    elif text_cell:
        merged_cells.append(text_cell)

# Neues Notebook speichern
merged_nb = nbformat.v4.new_notebook()
merged_nb.cells = merged_cells
nbformat.write(merged_nb, "merged_notebook.ipynb")
