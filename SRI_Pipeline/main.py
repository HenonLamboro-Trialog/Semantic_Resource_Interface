from config_loader import ConfigLoader
from semantic_interface import SemanticInterface
from mqtt_client import MQTTClient
from rdf_converter import RDFConverter
import json, csv, os, yaml


def load_json_from_file(file_path):
    """Loads JSON data from a file."""
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}")
        return None

def load_csv_from_file(file_path):
    """Loads CSV data from a file and returns it as a list of dictionaries."""
    try:
        with open(file_path, mode='r') as file:
            reader = csv.DictReader(file)
            data = [row for row in reader]
        return data
    except Exception as e:
        print(f"Error loading CSV file: {str(e)}")
        return None

def main():
    # Load MQTT configuration from YAML
    config = ConfigLoader.load_env()

    if not config.get("mqtt"):
        print("Error: MQTT configuration is missing.")
        return

    # Initialize components
    mqtt_client = MQTTClient(config['mqtt'])
    rdf_converter = RDFConverter()
    interface = SemanticInterface(mqtt_client, rdf_converter)
    
    # Start the interface
    interface.start()
    
    print("\nSemantic Resource Interface")
    print("Available Resource and Service Types: ev, pv, hvac, building, weather")
    
    try:
        while True:           
            data_type = input("\nEnter Resource type (or 'quit' to exit): ").lower()
            if data_type == 'quit':
                break
                
            if data_type not in ['ev', 'pv', 'hvac', 'building', 'weather']:
                print("Invalid data type!")
                continue

             # Offer user the choice to either input JSON manually or upload a file
            choice = input("Enter '1' to input JSON data or '2' to upload a JSON file or '3' to upload CSV file: ")
            
            if choice == '1':
                # Input JSON manually
                try:
                    data_str = input("Enter JSON data: ")
                    data = json.loads(data_str)
                    interface.process_input(data_type, data)
                    print("Data processed and published successfully!")
                except json.JSONDecodeError:
                    print("Invalid JSON format!")
                except Exception as e:
                    print(f"Error processing data: {str(e)}")
            
            elif choice == '2':
                # Upload JSON file
                file_path = input("Enter the path to the JSON file: ")
                
                if not os.path.isfile(file_path):
                    print("File not found! Please provide a valid path.")
                    continue
                
                data = load_json_from_file(file_path)
                
                if data:
                    interface.process_input(data_type, data)
                    print("Data processed and published successfully!")
            
            elif choice == '3':
                # Upload CSV file
                file_path = input("Enter the path to the CSV file: ")
                
                if not os.path.isfile(file_path):
                    print("File not found! Please provide a valid path.")
                    continue
                
                data = load_csv_from_file(file_path)
                
                if data:
                    interface.process_input(data_type, data)
                    print("Data processed and published successfully!")

            
            else:
                print("Invalid choice! Please enter '1' or '2'.")

    finally:
        interface.stop()

if __name__ == "__main__":
    main()