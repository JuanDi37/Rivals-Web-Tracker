import pandas as pd

# Lista de nombres de archivo
files = ['rivals_data1.csv', 'rivals_data2.csv', 'rivals_data3.csv', 'rivals_data4.csv', 'rivals_data5.csv']

# Leer y concatenar todos los archivos
df_combined = pd.concat([pd.read_csv(file) for file in files], ignore_index=True)

# Guardar el resultado en un nuevo archivo
df_combined.to_csv('rivals_data_final.csv', index=False, encoding='utf-8')

print(f"[+] Combinados {len(df_combined)} registros en 'rivals_data_final.csv'")
