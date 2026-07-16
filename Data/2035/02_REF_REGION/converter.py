import csv

# -------- CONFIGURACIÓ --------
input_file = "Technologies.csv"  # <-- Canvia això pel nom del teu fitxer
output_file = "Technologies.csv"  # <-- O posa el mateix nom que l'input per sobreescriure
# --------------------------------

with open(input_file, 'r', encoding='utf-8') as infile, \
        open(output_file, 'w', encoding='utf-8', newline='') as outfile:
    reader = csv.reader(infile, delimiter=';')
    writer = csv.writer(outfile, delimiter=';')

    for row in reader:
        new_row = []
        for cell in row:
            # Substituir la coma per punt si el contingut sembla un número amb coma decimal
            new_cell = cell.replace(',', '.') if ',' in cell and cell.replace(',', '').replace('.', '').replace('-',
                                                                                                                '').isdigit() else cell
            new_row.append(new_cell)
        writer.writerow(new_row)

print(f"Conversió completada. Fitxer desat com a: {output_file}")
