import os
from PIL import Image
import glob
from pathlib import Path

def convert_to_webp(source, quality=80):
    """Convert image to WebP format"""
    destination = source.rsplit('.', 1)[0] + '.webp'
    
    # Skip if WebP version already exists
    if os.path.exists(destination):
        return None
        
    image = Image.open(source)
    
    # Convert RGBA to RGB if necessary
    if image.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        image = background
    
    # Save the image
    try:
        image.save(destination, 'WEBP', quality=quality)
        print(f"Converted: {source} -> {destination}")
        return destination
    except Exception as e:
        print(f"Error converting {source}: {e}")
        return None

def process_directory(directory):
    """Process all images in a directory"""
    # Supported image formats (case-insensitive)
    formats = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.JPG', '*.JPEG', '*.PNG', '*.GIF']
    
    # Get all image files
    image_files = []
    for format in formats:
        image_files.extend(glob.glob(os.path.join(directory, '**', format), recursive=True))
    
    converted = []
    for image_file in image_files:
        if 'webp' not in image_file.lower():  # Case-insensitive check for webp
            result = convert_to_webp(image_file)
            if result:
                converted.append((image_file, result))
    
    return converted

def main():
    # Base directory is the Flask app static folder
    base_dir = Path(__file__).parent.parent / 'app' / 'static'
    
    # Directories to process
    directories = [
        base_dir / 'uploads',
        base_dir / 'uploads' / 'avatars',
        base_dir / 'uploads' / 'blog',
        base_dir / 'img'
    ]
    
    # Process each directory
    total_converted = []
    for directory in directories:
        if directory.exists():
            print(f"\nProcessing directory: {directory}")
            converted = process_directory(str(directory))
            total_converted.extend(converted)
    
    # Print summary
    print(f"\nTotal images converted: {len(total_converted)}")
    for original, webp in total_converted:
        print(f"Converted: {original} -> {webp}")

if __name__ == '__main__':
    main()
