import os
import pandas as pd

def find_specific_folders(repo_path, folder_names):
    """
    Find specific folders by name within the repository.
    
    Args:
        repo_path (str): Path to the repository
        folder_names (list): List of folder names to find
        
    Returns:
        list: List of full paths to the specified folders
    """
    found_folders = []
    
    for root, dirs, files in os.walk(repo_path):
        for dir_name in dirs:
            if dir_name in folder_names:
                folder_path = os.path.join(root, dir_name)
                found_folders.append(folder_path)
                print(f"Encontrada carpeta: {dir_name} en {folder_path}")
    
    return found_folders

def process_technology_files(selected_folders, orden_file):
    """
    Process the Technologies.csv files and update the orden.csv template.
    
    Args:
        selected_folders (list): List of selected folder paths
        orden_file (str): Path to the orden.csv template
        
    Returns:
        DataFrame: Updated orden.csv with values from Technologies.csv files
    """
    # Read the orden.csv file as a template
    try:
        orden_df = pd.read_csv(orden_file, sep=';')
        print(f"Archivo orden.csv cargado con {len(orden_df)} tecnologías")
    except Exception as e:
        print(f"Error al cargar el archivo orden.csv: {e}")
        return None
    
    # Dictionary to store technology parameters from folders
    tech_dict = {}
    
    # Process each folder and collect technology parameters
    for folder in selected_folders:
        folder_name = os.path.basename(folder)
        technologies_file = os.path.join(folder, "Technologies.csv")
        
        if os.path.exists(technologies_file):
            try:
                df = pd.read_csv(technologies_file, sep=';')
                print(f"Procesando {technologies_file} con {len(df)} tecnologías")
                
                # Create a dictionary for easy lookup
                for _, row in df.iterrows():
                    tech_name = row['Technologies param']
                    
                    # If this is the first time we see this technology, initialize it
                    if tech_name not in tech_dict:
                        # Get all columns except 'Technologies param'
                        param_dict = {col: row[col] for col in df.columns if col != 'Technologies param'}
                        tech_dict[tech_name] = param_dict
                        
                print(f"Procesado Technologies.csv de {folder_name}")
                
            except Exception as e:
                print(f"Error al procesar {technologies_file}: {e}")
    
    # Update the orden.csv template with values from the processed files
    updated_count = 0
    for index, row in orden_df.iterrows():
        tech_name = row['Technologies param']
        
        if tech_name in tech_dict:
            # Update all columns except 'Technologies param'
            for col in orden_df.columns:
                if col != 'Technologies param' and col in tech_dict[tech_name]:
                    orden_df.at[index, col] = tech_dict[tech_name][col]
            updated_count += 1
    
    print(f"Actualizado orden.csv con {updated_count} tecnologías de las carpetas seleccionadas")
    
    return orden_df

def main():
    """
    Main function to execute the program.
    """
    # Set hardcoded paths
    repo_path = "/home/pjimenez/EnergyScope_Unif/Data/2022/"
    orden_file = "/home/pjimenez/EnergyScope_Unif/scripts/order/orden.csv"
    output_file = "/home/pjimenez/EnergyScope_Unif/scripts/order/final.csv"
    
    # Specific folders to process
    folder_names_to_process = ["SA-SC"]
    
    print(f"Usando repositorio: {repo_path}")
    print(f"Archivo orden.csv: {orden_file}")
    print(f"Archivo de salida: {output_file}")
    print(f"Buscando carpetas específicas: {', '.join(folder_names_to_process)}")
    
    # Check if orden.csv exists
    if not os.path.exists(orden_file):
        print(f"Error: El archivo orden.csv no existe en la ruta especificada: {orden_file}")
        return
    
    # Find the specific folders
    selected_folders = find_specific_folders(repo_path, folder_names_to_process)
    
    if not selected_folders:
        print("No se encontraron las carpetas especificadas. Saliendo.")
        return
    
    # Check if we found all requested folders
    found_names = [os.path.basename(folder) for folder in selected_folders]
    missing_folders = [name for name in folder_names_to_process if name not in found_names]
    
    if missing_folders:
        print(f"Advertencia: No se encontraron las siguientes carpetas: {', '.join(missing_folders)}")
        proceed = input("¿Desea continuar con las carpetas encontradas? (s/n): ")
        if proceed.lower() != 's':
            print("Operación cancelada por el usuario.")
            return
    
    # Process the files
    print("Procesando archivos...")
    updated_orden_df = process_technology_files(selected_folders, orden_file)
    
    if updated_orden_df is None:
        print("Error al procesar los archivos. Saliendo.")
        return
    
    # Save the results
    updated_orden_df.to_csv(output_file, sep=';', index=False)
    
    print(f"Éxito: Procesamiento completo. Resultado guardado en: {output_file}")

if __name__ == "__main__":
    main()