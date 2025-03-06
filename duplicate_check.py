import os
from PIL import Image
import imagehash

def find_duplicates(folder):
    hashes = {}
    duplicates = []
    
    for file in os.listdir(folder):
        file_path = os.path.join(folder, file)
        
        if os.path.isfile(file_path) and file.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp')):
            try:
                img = Image.open(file_path)
                h = imagehash.average_hash(img)
                
                if h in hashes:
                    duplicates.append((file_path, hashes[h]))
                else:
                    hashes[h] = file_path
            except Exception as e:
                print(f"Error processing {file}: {e}")
    
    return duplicates

if __name__ == "__main__":
    folder_path = input("Enter the path to the folder: ")
    duplicates = find_duplicates(folder_path)
    
    if duplicates:
        print("Duplicate images found:")
        for dup in duplicates:
            print(f"{dup[0]} is a duplicate of {dup[1]}")
    else:
        print("No duplicates found.")
