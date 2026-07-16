import os
import pandas as pd
import tkinter as tk
from tkinter import messagebox

def process_demands_csv(selected_folders):
    """
    Process the Demands.csv files from selected folders and create a summed version.
    
    Args:
        selected_folders (list): List of selected folder paths
        
    Returns:
        DataFrame: Summed Demands data
    """
    demands_sum = None
    
    for folder in selected_folders:
        folder_name = os.path.basename(folder)
        demands_file = os.path.join(folder, "Demands.csv")
        
        if os.path.exists(demands_file):
            try:
                df = pd.read_csv(demands_file, sep=';')
                
                # Identify non-numeric columns to preserve
                non_numeric_columns = ['Category', 'Subcategory', 'parameter name', 'Units']
                
                # If this is the first folder, initialize the sum DataFrame
                if demands_sum is None:
                    demands_sum = df.copy()
                    # Convert numeric columns to float for summation
                    for col in demands_sum.columns:
                        if col not in non_numeric_columns:
                            demands_sum[col] = pd.to_numeric(demands_sum[col], errors='coerce').fillna(0)
                else:
                    # Add the numeric values to the sum
                    for col in df.columns:
                        if col not in non_numeric_columns and col in demands_sum.columns:
                            numeric_values = pd.to_numeric(df[col], errors='coerce').fillna(0)
                            demands_sum[col] = demands_sum[col] + numeric_values
                
                print(f"Procesado Demands.csv de {folder_name}")
                
            except Exception as e:
                print(f"Error al procesar {demands_file}: {e}")
    
    return demands_sum

def process_resources_csv(selected_folders):
    """
    Process the Resources.csv files from selected folders, matching resources by their name in the first column.
    Only sum 'avail_local' and 'avail_exterior' columns. Include all resources from all files.
    
    Args:
        selected_folders (list): List of selected folder paths
        
    Returns:
        DataFrame: Summed Resources data with only first column, avail_local, and avail_exterior
    """
    # Dictionary to store resources and their summed values
    resource_dict = {}
    
    # Track the name of the first column (it might be unnamed)
    first_col_name = None
    
    # Track all resource names found in all files
    all_resource_names = set()
    
    # Initial processing - scan all files to gather all resource names
    print("Fase 1: Recopilando nombres de recursos de todos los archivos...")
    for folder in selected_folders:
        folder_name = os.path.basename(folder)
        resources_file = os.path.join(folder, "Resources.csv")
        
        if os.path.exists(resources_file):
            try:
                df = pd.read_csv(resources_file, sep=';')
                
                # Determine the name of the first column (which contains resource names)
                if first_col_name is None:
                    first_col_name = df.columns[0]  # Get the name of the first column
                
                # Extract resource names from the first column
                if first_col_name == '':  # If first column is unnamed
                    # For unnamed columns, the values will be in the first column
                    resource_names = df.iloc[:, 0].tolist()
                else:
                    resource_names = df[first_col_name].tolist()
                
                # Add all resource names to the set
                all_resource_names.update(resource_names)
                
                print(f"Encontrados {len(resource_names)} recursos en {folder_name}")
                
            except Exception as e:
                print(f"Error al escanear {resources_file}: {e}")
    
    # Initialize the dictionary with all resource names and zero values
    for resource_name in all_resource_names:
        resource_dict[resource_name] = {'avail_local': 0, 'avail_exterior': 0}
    
    # Second phase - sum the values for each resource
    print(f"Fase 2: Sumando valores para {len(all_resource_names)} recursos...")
    for folder in selected_folders:
        folder_name = os.path.basename(folder)
        resources_file = os.path.join(folder, "Resources.csv")
        
        if os.path.exists(resources_file):
            try:
                df = pd.read_csv(resources_file, sep=';')
                
                # Get the column index for resource names (first column)
                resource_col_idx = 0
                
                # Iterate through each row to process the resources
                for idx, row in df.iterrows():
                    # Get the resource name from the first column
                    resource_name = row.iloc[resource_col_idx]
                    
                    # Safely extract avail_local and avail_exterior values
                    try:
                        avail_local = pd.to_numeric(row['avail_local'], errors='coerce')
                        avail_local = 0 if pd.isna(avail_local) else avail_local
                    except:
                        avail_local = 0
                        print(f"Advertencia: Valor inválido para avail_local en {resource_name} de {folder_name}")
                    
                    try:
                        avail_exterior = pd.to_numeric(row['avail_exterior'], errors='coerce')
                        avail_exterior = 0 if pd.isna(avail_exterior) else avail_exterior
                    except:
                        avail_exterior = 0
                        print(f"Advertencia: Valor inválido para avail_exterior en {resource_name} de {folder_name}")
                    
                    # Add to the accumulated values
                    resource_dict[resource_name]['avail_local'] += avail_local
                    resource_dict[resource_name]['avail_exterior'] += avail_exterior
                
                print(f"Procesado Resources.csv de {folder_name}")
                
            except Exception as e:
                print(f"Error al procesar {resources_file}: {e}")
    
    # Convert the dictionary to a DataFrame with only the required columns
    if resource_dict:
        resource_names = list(resource_dict.keys())
        avail_local_values = [resource_dict[name]['avail_local'] for name in resource_names]
        avail_exterior_values = [resource_dict[name]['avail_exterior'] for name in resource_names]
        
        # Create the DataFrame with the appropriate column name for the first column
        resources_sum = pd.DataFrame({
            first_col_name if first_col_name != '' else '': resource_names,
            'avail_local': avail_local_values,
            'avail_exterior': avail_exterior_values
        })
        
        # Sort the DataFrame by resource name for easier reading
        sort_col = first_col_name if first_col_name != '' else ''
        resources_sum = resources_sum.sort_values(sort_col).reset_index(drop=True)
        
        print(f"Creado archivo Resources.csv con {len(resources_sum)} recursos")
        return resources_sum
    else:
        return None

def process_technologies_csv(selected_folders):
    """
    Process the Technologies.csv files from selected folders and create a summed version.
    For Technologies.csv, we sum f_min and f_max columns, matching by Technologies param names.
    For c_p column, we take the value from the first folder in the list where the technology appears.
    Ensures all technologies from all files are included.
    
    Args:
        selected_folders (list): List of selected folder paths
        
    Returns:
        DataFrame: Summed Technologies data with the required columns
    """
    # Dictionary to store technology parameters and their values
    tech_dict = {}
    
    # Track all technology names found in all files
    all_tech_names = set()
    
    # Initial processing - scan all files to gather all technology names
    print("Fase 1: Recopilando nombres de tecnologías de todos los archivos...")
    for folder in selected_folders:
        folder_name = os.path.basename(folder)
        technologies_file = os.path.join(folder, "Technologies.csv")
        
        if os.path.exists(technologies_file):
            try:
                df = pd.read_csv(technologies_file, sep=';')
                
                # Add all technology names to the set
                tech_names = df['Technologies param'].tolist()
                all_tech_names.update(tech_names)
                
                print(f"Encontradas {len(tech_names)} tecnologías en {folder_name}")
                
            except Exception as e:
                print(f"Error al escanear {technologies_file}: {e}")
    
    # Initialize the dictionary with all technology names and default values
    for tech_name in all_tech_names:
        tech_dict[tech_name] = {'f_min': 0, 'f_max': 0, 'c_p': None}
    
    # First, process c_p values in order of folders (to ensure we get values from first folder first)
    print("Fase 2.1: Procesando valores de c_p en orden de carpetas...")
    for folder in selected_folders:
        folder_name = os.path.basename(folder)
        technologies_file = os.path.join(folder, "Technologies.csv")
        
        if os.path.exists(technologies_file):
            try:
                df = pd.read_csv(technologies_file, sep=';')
                
                # Create a dictionary of technologies in this file for easy lookup
                folder_tech_dict = {}
                for _, row in df.iterrows():
                    tech_name = row['Technologies param']
                    
                    try:
                        c_p = pd.to_numeric(row['c_p'], errors='coerce')
                        c_p = None if pd.isna(c_p) else c_p
                    except:
                        c_p = None
                        print(f"Advertencia: Valor inválido para c_p en {tech_name} de {folder_name}")
                    
                    folder_tech_dict[tech_name] = c_p
                
                # Iterate through all technologies
                for tech_name in all_tech_names:
                    # If this technology exists in current folder and we don't have a c_p value yet
                    if tech_name in folder_tech_dict and tech_dict[tech_name]['c_p'] is None:
                        tech_dict[tech_name]['c_p'] = folder_tech_dict[tech_name]
                
                print(f"Procesados valores de c_p de {folder_name}")
                
            except Exception as e:
                print(f"Error al procesar valores de c_p en {technologies_file}: {e}")
    
    # Second, sum f_min and f_max values
    print("Fase 2.2: Sumando valores de f_min y f_max...")
    for folder in selected_folders:
        folder_name = os.path.basename(folder)
        technologies_file = os.path.join(folder, "Technologies.csv")
        
        if os.path.exists(technologies_file):
            try:
                df = pd.read_csv(technologies_file, sep=';')
                
                # Iterate through each row to process the technologies
                for _, row in df.iterrows():
                    tech_name = row['Technologies param']
                    
                    # Safely extract values, handling potential errors
                    try:
                        f_min = pd.to_numeric(row['f_min'], errors='coerce')
                        f_min = 0 if pd.isna(f_min) else f_min
                    except:
                        f_min = 0
                        print(f"Advertencia: Valor inválido para f_min en {tech_name} de {folder_name}")
                    
                    try:
                        f_max = pd.to_numeric(row['f_max'], errors='coerce')
                        f_max = 0 if pd.isna(f_max) else f_max
                    except:
                        f_max = 0
                        print(f"Advertencia: Valor inválido para f_max en {tech_name} de {folder_name}")
                    
                    # Add f_min and f_max to the accumulated values
                    tech_dict[tech_name]['f_min'] += f_min
                    tech_dict[tech_name]['f_max'] += f_max
                
                print(f"Procesados valores de f_min y f_max de {folder_name}")
                
            except Exception as e:
                print(f"Error al procesar valores de f_min y f_max en {technologies_file}: {e}")
    
    # Convert the dictionary to a DataFrame with the required columns
    if tech_dict:
        tech_names = list(tech_dict.keys())
        c_p_values = [tech_dict[name]['c_p'] for name in tech_names]
        f_min_values = [tech_dict[name]['f_min'] for name in tech_names]
        f_max_values = [tech_dict[name]['f_max'] for name in tech_names]
        
        technologies_sum = pd.DataFrame({
            'Technologies param': tech_names,
            'c_p': c_p_values,
            'f_min': f_min_values,
            'f_max': f_max_values
        })
        
        # Sort the DataFrame by Technologies param for easier reading
        technologies_sum = technologies_sum.sort_values('Technologies param').reset_index(drop=True)
        
        print(f"Creado archivo Technologies.csv con {len(technologies_sum)} tecnologías")
        return technologies_sum
    else:
        return None

def save_results(demands_sum, resources_sum, technologies_sum, output_dir, output_folder_name):
    """
    Save the summed results to CSV files in the output folder.
    
    Args:
        demands_sum (DataFrame): Summed Demands data
        resources_sum (DataFrame): Summed Resources data
        technologies_sum (DataFrame): Summed Technologies data
        output_dir (str): Directory where the output folder will be created
        output_folder_name (str): Name of the output folder
    """
    # Create the output folder
    output_path = os.path.join(output_dir, output_folder_name)
    os.makedirs(output_path, exist_ok=True)
    
    # Save the summed DataFrames to CSV files
    if demands_sum is not None:
        demands_sum.to_csv(os.path.join(output_path, "Demands.csv"), sep=';', index=False)
        print(f"Guardado Demands.csv sumado")
    
    if resources_sum is not None:
        resources_sum.to_csv(os.path.join(output_path, "Resources.csv"), sep=';', index=False)
        print(f"Guardado Resources.csv sumado")
    
    if technologies_sum is not None:
        technologies_sum.to_csv(os.path.join(output_path, "Technologies.csv"), sep=';', index=False)
        print(f"Guardado Technologies.csv sumado")
    
    print(f"Todos los archivos guardados en: {output_path}")
    return output_path

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

def main():
    """
    Main function to execute the program.
    """
    # Set hardcoded repository path and output folder name as specified
    repo_path = "/home/pjimenez/EnergyScope_Unif/Data/2022/"
    output_folder_name = "SA-SC"
    
    # Specific folders to sum
    folder_names_to_sum = ["SC-AS", "SC-CC", "SC-CQ", "SC-GB", "SC-MI", "SC-VC", "SC-VL"]
    
    print(f"Usando repositorio: {repo_path}")
    print(f"Buscando carpetas específicas: {', '.join(folder_names_to_sum)}")
    print(f"La carpeta de salida será: {output_folder_name}")
    
    # Find the specific folders
    selected_folders = find_specific_folders(repo_path, folder_names_to_sum)
    
    if not selected_folders:
        print("No se encontraron las carpetas especificadas. Saliendo.")
        return
    
    # Check if we found all requested folders
    found_names = [os.path.basename(folder) for folder in selected_folders]
    missing_folders = [name for name in folder_names_to_sum if name not in found_names]
    
    if missing_folders:
        print(f"Advertencia: No se encontraron las siguientes carpetas: {', '.join(missing_folders)}")
        proceed = input("¿Desea continuar con las carpetas encontradas? (s/n): ")
        if proceed.lower() != 's':
            print("Operación cancelada por el usuario.")
            return
    
    # Process the CSV files
    print("Procesando archivos...")
    demands_sum = process_demands_csv(selected_folders)
    resources_sum = process_resources_csv(selected_folders)
    technologies_sum = process_technologies_csv(selected_folders)
    
    # Check if any data was processed
    if demands_sum is None and resources_sum is None and technologies_sum is None:
        print("Error: No se encontraron archivos CSV válidos en las carpetas seleccionadas.")
        return
    
    # Save the results
    output_path = save_results(demands_sum, resources_sum, technologies_sum, repo_path, output_folder_name)
    
    print(f"Éxito: Procesamiento completo. Resultados guardados en: {output_path}")

if __name__ == "__main__":
    main()