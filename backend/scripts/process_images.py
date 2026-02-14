#!/usr/bin/env python3
"""
Script pour traiter et optimiser les images extraites du PDF Ratus
- Conversion en WebP pour optimisation
- Redimensionnement adaptatif
- Organisation par type (détectée manuellement dans le manifeste)
"""

import json
from pathlib import Path
from PIL import Image
import sys

OUTPUT_BASE = Path(__file__).parent.parent / "extracted_content"
IMAGES_DIR = OUTPUT_BASE / "images"
MANIFEST_PATH = OUTPUT_BASE / "ratus_manifest.json"

# Tailles cibles pour optimisation
MAX_WIDTH = 1200
MAX_HEIGHT = 1200
WEBP_QUALITY = 85


def load_manifest():
    """Charge le manifeste JSON"""
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_manifest(manifest):
    """Sauvegarde le manifeste JSON"""
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def optimize_image(image_path: Path) -> dict:
    """
    Optimise une image (redimensionnement + conversion WebP)

    Args:
        image_path: Chemin vers l'image source

    Returns:
        Dictionnaire avec les métadonnées de l'image optimisée
    """
    try:
        img = Image.open(image_path)
        original_size = image_path.stat().st_size
        width, height = img.size

        # Redimensionner si nécessaire
        if width > MAX_WIDTH or height > MAX_HEIGHT:
            ratio = min(MAX_WIDTH / width, MAX_HEIGHT / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"  📐 Resized from {width}x{height} to {new_width}x{new_height}")
        else:
            new_width, new_height = width, height

        # Convertir en WebP
        webp_path = image_path.with_suffix('.webp')
        img.save(webp_path, 'WEBP', quality=WEBP_QUALITY, method=6)
        new_size = webp_path.stat().st_size

        compression_ratio = (1 - new_size / original_size) * 100

        print(f"  💾 {image_path.name}")
        print(f"     Original: {original_size / 1024:.1f} KB → WebP: {new_size / 1024:.1f} KB")
        print(f"     Compression: {compression_ratio:.1f}%")

        return {
            'original_path': str(image_path.relative_to(OUTPUT_BASE)),
            'webp_path': str(webp_path.relative_to(OUTPUT_BASE)),
            'original_size': original_size,
            'webp_size': new_size,
            'compression_ratio': round(compression_ratio, 2),
            'dimensions': {'width': new_width, 'height': new_height}
        }

    except Exception as e:
        print(f"  ❌ Error processing {image_path.name}: {e}")
        return None


def process_all_images():
    """Traite toutes les images du dossier scenes"""
    print("\n🖼️  Processing images...")
    print("="*60)

    scenes_dir = IMAGES_DIR / "scenes"
    image_files = list(scenes_dir.glob("*.jpeg")) + list(scenes_dir.glob("*.jpg"))

    print(f"Found {len(image_files)} images to process\n")

    processed = []
    total_original = 0
    total_webp = 0

    for idx, image_path in enumerate(image_files, 1):
        print(f"\n[{idx}/{len(image_files)}]")
        result = optimize_image(image_path)

        if result:
            processed.append(result)
            total_original += result['original_size']
            total_webp += result['webp_size']

    print("\n" + "="*60)
    print("📊 PROCESSING SUMMARY")
    print("="*60)
    print(f"✅ Successfully processed: {len(processed)} images")
    print(f"📦 Total original size: {total_original / (1024*1024):.2f} MB")
    print(f"📦 Total WebP size: {total_webp / (1024*1024):.2f} MB")
    print(f"💾 Space saved: {(total_original - total_webp) / (1024*1024):.2f} MB")
    print(f"📉 Average compression: {(1 - total_webp/total_original)*100:.1f}%")
    print("="*60)

    return processed


def update_manifest_with_processed_images(processed_images):
    """Met à jour le manifeste avec les informations des images optimisées"""
    print("\n📝 Updating manifest...")

    manifest = load_manifest()

    # Ajouter les informations d'optimisation
    manifest['processed_images'] = processed_images
    manifest['processing_metadata'] = {
        'total_processed': len(processed_images),
        'optimization_settings': {
            'max_width': MAX_WIDTH,
            'max_height': MAX_HEIGHT,
            'webp_quality': WEBP_QUALITY
        }
    }

    save_manifest(manifest)
    print("✅ Manifest updated")


def main():
    print("\n" + "🎨 IMAGE PROCESSING TOOL 🎨".center(60))
    print("="*60)

    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest not found: {MANIFEST_PATH}")
        print("Please run extract_ratus_content.py first")
        sys.exit(1)

    processed = process_all_images()
    update_manifest_with_processed_images(processed)

    print("\n✨ Image processing completed successfully! ✨\n")


if __name__ == "__main__":
    main()
