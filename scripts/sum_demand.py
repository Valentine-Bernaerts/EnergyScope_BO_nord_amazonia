import os
import pandas as pd
import numpy as np

def sum_demands_files(base_dir, output_file, excluded_folders=None):
    """
    Suma todos los archivos Demands.csv encontrados en el árbol de directorios,
    excluyendo las carpetas especificadas.
    
    Args:
        base_dir: Directorio base donde buscar
        output_file: Ruta del archivo de salida
        excluded_folders: Lista de nombres de carpetas a excluir
    """
    if excluded_folders is None:
        excluded_folders = []
    
    # Lista para almacenar todos los DataFrames
    all_dfs = []
    files_found = 0
    files_processed = 0
    
    # Para mantener el orden original de los parámetros
    parameter_order = []
    order_established = False
    
    # Verificar si el directorio base existe
    if not os.path.exists(base_dir):
        print(f"Error: El directorio especificado no existe: {base_dir}")
        return
    
    print(f"Buscando archivos Demands.csv en {base_dir} y sus subdirectorios...")
    print(f"Excluyendo las carpetas: {', '.join(excluded_folders)}")
    
    # Recorrer la estructura de directorios
    for root, dirs, files in os.walk(base_dir):
        # Comprobamos si el directorio actual está dentro de una carpeta excluida
        current_path = os.path.relpath(root, base_dir)
        skip_dir = False
        
        # Comprobamos si el directorio actual o alguno de sus padres está en la lista de excluidos
        for excluded in excluded_folders:
            if excluded in current_path.split(os.sep):
                skip_dir = True
                break
        
        if skip_dir:
            # Modificamos dirs in-place para evitar recorrer los subdirectorios
            dirs[:] = []
            continue
            
        # Verificar si Demands.csv existe en este directorio
        demands_file = os.path.join(root, "Demands.csv")
        if os.path.exists(demands_file):
            files_found += 1
            try:
                # Leer el archivo CSV con separador punto y coma
                df = pd.read_csv(demands_file, sep=';')
                
                # Verificar la estructura esperada
                expected_columns = [
                    'Category', 'Subcategory', 'parameter name', 
                    'HOUSEHOLDS', 'SERVICES', 'INDUSTRY', 'TRANSPORTATION',
                    'PUBLIC_LIGHTING', 'AGRICULTURE', 'MINING', 'FISHING_OTHERS', 'Units'
                ]
                
                # Verificar si todas las columnas esperadas están presentes
                missing_cols = [col for col in expected_columns if col not in df.columns]
                if missing_cols:
                    print(f"Advertencia: El archivo {demands_file} no tiene las columnas requeridas: {missing_cols}")
                    print(f"Columnas encontradas: {df.columns.tolist()}")
                    continue
                
                # Guardar el orden de los parámetros del primer archivo válido
                if not order_established:
                    parameter_order = df['parameter name'].tolist()
                    order_established = True
                
                # Convertir columnas numéricas a float
                numeric_cols = [
                    'HOUSEHOLDS', 'SERVICES', 'INDUSTRY', 'TRANSPORTATION',
                    'PUBLIC_LIGHTING', 'AGRICULTURE', 'MINING', 'FISHING_OTHERS'
                ]
                
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Reemplazar valores NaN con 0
                    df[col] = df[col].fillna(0)
                
                # Añadir este DataFrame a nuestra lista
                all_dfs.append(df)
                files_processed += 1
                print(f"Procesado: {demands_file}")
                
            except Exception as e:
                print(f"Error al procesar {demands_file}: {e}")
    
    print(f"\nResumen del proceso:")
    print(f"Encontrados: {files_found} archivos Demands.csv")
    print(f"Procesados correctamente: {files_processed} archivos")
    
    if not all_dfs:
        print("No se pudo procesar ningún archivo Demands.csv. Verifique el formato de los archivos.")
        return
    
    try:
        # Concatenar todos los dataframes
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Columnas para agrupar (estas no se sumarán)
        group_cols = ['Category', 'Subcategory', 'parameter name', 'Units']
        
        # Columnas numéricas para sumar
        value_cols = [
            'HOUSEHOLDS', 'SERVICES', 'INDUSTRY', 'TRANSPORTATION',
            'PUBLIC_LIGHTING', 'AGRICULTURE', 'MINING', 'FISHING_OTHERS'
        ]
        
        # Agrupar y sumar los valores
        result_df = combined_df.groupby(group_cols)[value_cols].sum().reset_index()
        
        # Crear un diccionario para mapear 'parameter name' al índice en parameter_order
        if parameter_order:
            order_dict = {param: idx for idx, param in enumerate(parameter_order)}
            
            # Añadir una columna temporal para ordenar
            result_df['sort_key'] = result_df['parameter name'].map(order_dict)
            
            # Ordenar por esta columna (y manejar valores que no estén en el mapeo)
            result_df = result_df.sort_values(
                by='sort_key', 
                key=lambda x: x.map(lambda y: 9999 if pd.isna(y) else y)
            ).drop('sort_key', axis=1)
        
        # Asegurar que el orden de las columnas sea el mismo que el original
        final_cols = [
            'Category', 'Subcategory', 'parameter name',
            'HOUSEHOLDS', 'SERVICES', 'INDUSTRY', 'TRANSPORTATION',
            'PUBLIC_LIGHTING', 'AGRICULTURE', 'MINING', 'FISHING_OTHERS', 'Units'
        ]
        result_df = result_df[final_cols]
        
        # Guardar el resultado con punto y coma como separador
        result_df.to_csv(output_file, index=False, sep=';')
        print(f"\nResultado guardado exitosamente en: {output_file}")
        print(f"El archivo resultante contiene {len(result_df)} filas.")
        
        # Mostrar algunas estadísticas básicas
        print("\nResumen de los datos sumados:")
        for col in value_cols:
            total = result_df[col].sum()
            print(f"Total {col}: {total:.2f}")
        
    except Exception as e:
        print(f"Error durante la agregación de datos: {e}")

# Directorio base, archivo de salida y carpetas excluidas
if __name__ == "__main__":
    # Ajusta esta ruta según tu entorno
    base_directory = "/home/pjimenez/EnergyScope_Unif/Data/2021/"
    output_file = os.path.join(base_directory, "Demands_total.csv")
    
    # Carpetas a excluir
    excluded_folders = ["02_REF_REGION", "Z_archives"]
    
    # Ejecutar la función principal
    sum_demands_files(base_directory, output_file, excluded_folders)