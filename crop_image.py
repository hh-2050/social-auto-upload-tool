from PIL import Image
import os

def crop_image(image_path):
    try:
        # Open the image
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Calculate the height for 3:4 aspect ratio (based on original width)
            new_height = int(width * 4 / 3)
            
            # Ensure we don't exceed the original image height
            if new_height > height:
                print(f"Warning: {image_path} is not tall enough for a 3:4 crop with the original width")
                return False
            
            # Define the box (left, upper, right, lower)
            box = (0, 0, width, new_height)
            
            # Crop the image
            cropped_img = img.crop(box)
            
            # Save the cropped image to a temporary file with the same extension
            base_name, ext = os.path.splitext(image_path)
            temp_path = f"{base_name}_temp{ext}"
            
            try:
                # Save with the same format as the original
                cropped_img.save(temp_path, quality=95, subsampling=0, format=img.format)
                
                # Replace the original with the cropped version
                os.replace(temp_path, image_path)
            except Exception as save_error:
                print(f"Error saving {image_path}: {str(save_error)}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                return False
            
            print(f"Processed: {image_path}")
            print(f"  Original dimensions: {width}x{height}")
            print(f"  Cropped dimensions: {width}x{new_height} (3:4 aspect ratio)")
            return True
            
    except Exception as e:
        print(f"Error processing {image_path}: {str(e)}")
        # Clean up temp file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        return False

def process_directory(directory):
    # Supported image extensions
    image_extensions = ('.jpg', '.jpeg', '.JPG', '.JPEG')
    processed_count = 0
    error_count = 0
    
    print(f"\nProcessing directory: {directory}")
    
    # Walk through all subdirectories
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith(image_extensions):
                file_path = os.path.join(root, filename)
                print(f"\nFound image: {file_path}")
                
                if crop_image(file_path):
                    processed_count += 1
                else:
                    error_count += 1
    
    return processed_count, error_count

if __name__ == "__main__":
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("Starting batch image cropping...")
    print(f"Working directory: {script_dir}")
    
    processed, errors = process_directory(script_dir)
    
    print("\nProcessing complete!")
    print(f"Images successfully processed: {processed}")
    print(f"Images with errors: {errors}")
    
    if processed == 0 and errors == 0:
        print("\nNo JPG/JPEG images were found in the directory.")
