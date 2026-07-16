import os
import pandas as pd
import numpy as np

# Directorio base
base_dir = "/home/pjimenez/EnergyScope_Unif/Data/2030/"

# Lista de carpetas a procesar
folders = ['SIN', 'SA-TJ', 'SA-SC', 'SA-BN', 'SA-PA']

# Ruta al archivo de factores de proyección
projection_file = os.path.join(base_dir, "demanda_proyectada_2030.csv")

# Cargar el archivo de factores de proyección
# Especificamos explícitamente el separador como punto y coma
print(f"Cargando archivo de factores de proyección: {projection_file}")
projection_data = pd.read_csv(projection_file, sep=';')
print(f"Archivo de factores cargado. Forma: {projection_data.shape}")

# Función para procesar cada archivo Demands.csv
def process_demands_file(file_path, projection_data):
    print(f"Procesando archivo: {file_path}")
    
    try:
        # Cargar el archivo Demands.csv con separador punto y coma
        demands_df = pd.read_csv(file_path, sep=';')
        print(f"Archivo cargado. Forma: {demands_df.shape}")
        
        # Verificar que tenemos todas las columnas necesarias
        print(f"Columnas en el archivo: {', '.join(demands_df.columns)}")
        
        # Hacer una copia del DataFrame original para mantener la estructura
        modified_df = demands_df.copy()
        
        # Iterar sobre las filas del archivo de demanda
        for index, row in demands_df.iterrows():
            param_name = row['parameter name']  # Usamos el nombre de la columna exacto
            
            # Buscar este parámetro en el archivo de proyección
            projection_rows = projection_data[projection_data['parameter name'] == param_name]
            
            if not projection_rows.empty:
                projection_row = projection_rows.iloc[0]
                
                # Procesar cada sector (columna)
                for sector in ['HOUSEHOLDS', 'SERVICES', 'INDUSTRY', 'TRANSPORTATION', 
                              'PUBLIC_LIGHTING', 'AGRICULTURE', 'MINING', 'FISHING_OTHERS']:
                    
                    # Verificar si el sector existe en ambos DataFrames
                    if sector in demands_df.columns and sector in projection_data.columns:
                        # Obtener el valor original y el factor
                        original_value = demands_df.loc[index, sector]
                        factor = projection_row[sector]
                        
                        # Verificar que ambos son numéricos y no NaN
                        if pd.notna(original_value) and pd.notna(factor):
                            try:
                                # Convertir a float para asegurarnos que podemos hacer operaciones matemáticas
                                original_value = float(original_value)
                                factor = float(factor)
                                
                                # Si el valor original no es cero y es numérico, aplicamos el factor
                                if original_value != 0:
                                    # Multiplicar el valor por el factor
                                    modified_value = original_value * factor
                                    modified_df.loc[index, sector] = modified_value
                                    print(f"  Parámetro: {param_name}, Sector: {sector}, Valor original: {original_value}, Factor: {factor}, Nuevo valor: {modified_value}")
                            except ValueError:
                                # Si no se puede convertir a float, lo dejamos igual
                                print(f"  No se pudo convertir a número: {param_name}, Sector: {sector}, Valor: {original_value}")
        
        # Guardar el DataFrame modificado de vuelta al archivo
        modified_df.to_csv(file_path, sep=';', index=False)
        print(f"Archivo guardado: {file_path}")
        return True
    
    except Exception as e:
        print(f"Error al procesar {file_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Procesar cada carpeta
for folder in folders:
    folder_path = os.path.join(base_dir, folder)
    
    # Verificar si la carpeta existe
    if os.path.isdir(folder_path):
        print(f"\nProcesando carpeta: {folder}")
        
        # Buscar el archivo Demands.csv en esta carpeta
        demands_file = os.path.join(folder_path, "Demands.csv")
        
        if os.path.isfile(demands_file):
            # Procesar el archivo
            success = process_demands_file(demands_file, projection_data)
            if success:
                print(f"Procesamiento exitoso para {folder}")
            else:
                print(f"Error al procesar {folder}")
        else:
            print(f"No se encontró el archivo Demands.csv en {folder}")
    else:
        print(f"La carpeta {folder} no existe en {base_dir}")

print("\nProcesamiento completo.")