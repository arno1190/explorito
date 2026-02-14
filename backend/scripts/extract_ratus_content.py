#!/usr/bin/env python3
"""
Script pour extraire et traiter le contenu du PDF Ratus et Ses Amis
- Extraction des images (personnages, syllabes, mots, scènes)
- OCR du texte si nécessaire
- Organisation par leçon
- Génération du manifeste de contenu
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import fitz  # PyMuPDF
from PIL import Image
import io
from collections import defaultdict

# Configuration
PDF_PATH = "/Users/arnaudpascal/Downloads/656351809-Ratus-Et-Ses-Amis.pdf"
OUTPUT_BASE = Path(__file__).parent.parent / "extracted_content"
IMAGES_DIR = OUTPUT_BASE / "images"
TEXTS_DIR = OUTPUT_BASE / "texts"

# Seuils de qualité pour les images
MIN_IMAGE_WIDTH = 50
MIN_IMAGE_HEIGHT = 50
MIN_IMAGE_SIZE = 5000  # pixels carrés minimum


def setup_directories():
    """Crée la structure de dossiers nécessaire"""
    for subdir in ["characters", "syllables", "words", "scenes"]:
        (IMAGES_DIR / subdir).mkdir(parents=True, exist_ok=True)
    TEXTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✅ Directories created at {OUTPUT_BASE}")


def extract_images_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extrait toutes les images du PDF

    Args:
        pdf_path: Chemin vers le PDF Ratus

    Returns:
        Liste de dictionnaires contenant les métadonnées des images extraites
    """
    print(f"📖 Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)

    extracted_images = []
    image_counter = 0

    print(f"📄 Total pages: {len(doc)}")

    for page_num in range(len(doc)):
        page = doc[page_num]
        print(f"Processing page {page_num + 1}/{len(doc)}...", end="\r")

        # Extraire les images de la page
        image_list = page.get_images(full=True)

        # Extraire aussi le texte de la page pour contexte
        page_text = page.get_text("text")

        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Ouvrir l'image avec PIL
                pil_image = Image.open(io.BytesIO(image_bytes))
                width, height = pil_image.size

                # Filtrer les images trop petites (probablement des icônes)
                if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                    continue

                if width * height < MIN_IMAGE_SIZE:
                    continue

                # Nom de fichier unique
                image_filename = f"ratus_p{page_num+1:03d}_img{img_index+1:02d}.{image_ext}"
                image_path = IMAGES_DIR / "scenes" / image_filename

                # Sauvegarder l'image brute
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)

                extracted_images.append({
                    "filename": image_filename,
                    "page": page_num + 1,
                    "index": img_index,
                    "width": width,
                    "height": height,
                    "format": image_ext,
                    "path": str(image_path.relative_to(OUTPUT_BASE)),
                    "context_text": page_text[:200] if page_text else "",  # Premiers 200 chars
                    "counter": image_counter
                })

                image_counter += 1

            except Exception as e:
                print(f"\n⚠️  Error extracting image {img_index} from page {page_num + 1}: {e}")
                continue

    print(f"\n✅ Extracted {len(extracted_images)} images from {len(doc)} pages")
    doc.close()

    return extracted_images


def extract_text_by_page(pdf_path: str) -> Dict[int, str]:
    """
    Extrait tout le texte du PDF page par page

    Args:
        pdf_path: Chemin vers le PDF

    Returns:
        Dictionnaire {page_num: texte}
    """
    print(f"\n📝 Extracting text from PDF...")
    doc = fitz.open(pdf_path)

    text_by_page = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        text_by_page[page_num + 1] = text

        # Sauvegarder le texte de chaque page
        text_file = TEXTS_DIR / f"page_{page_num+1:03d}.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text)

    print(f"✅ Extracted text from {len(doc)} pages")
    doc.close()

    return text_by_page


def analyze_content_structure(images: List[Dict], texts: Dict[int, str]) -> Dict[str, Any]:
    """
    Analyse la structure du contenu pour identifier les leçons

    Args:
        images: Liste des images extraites
        texts: Texte par page

    Returns:
        Structure organisée par leçon
    """
    print(f"\n🔍 Analyzing content structure...")

    # Mots-clés pour identifier les sections
    lesson_keywords = ["leçon", "lecon", "exercice", "lecture", "son"]

    lessons = defaultdict(lambda: {
        "title": "",
        "pages": [],
        "images": [],
        "content": "",
        "sounds": [],
        "words": []
    })

    current_lesson = 1

    for page_num, text in texts.items():
        text_lower = text.lower()

        # Détecter si c'est une nouvelle leçon
        if any(keyword in text_lower for keyword in lesson_keywords):
            # Essayer d'extraire le numéro de leçon
            # Pattern simple: chercher "leçon X" ou "lecon X"
            import re
            match = re.search(r'le[çc]on\s+(\d+)', text_lower)
            if match:
                current_lesson = int(match.group(1))

        # Associer la page à la leçon courante
        lessons[current_lesson]["pages"].append(page_num)
        lessons[current_lesson]["content"] += text + "\n"

        # Associer les images de cette page
        page_images = [img for img in images if img["page"] == page_num]
        lessons[current_lesson]["images"].extend(page_images)

    print(f"✅ Identified {len(lessons)} potential lessons")

    return dict(lessons)


def create_manifest(images: List[Dict], lessons: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crée le fichier manifeste JSON avec toutes les métadonnées

    Args:
        images: Liste des images extraites
        lessons: Structure des leçons

    Returns:
        Manifeste complet
    """
    print(f"\n📋 Creating manifest...")

    manifest = {
        "source": "Ratus et Ses Amis",
        "extraction_date": "2026-02-02",
        "total_images": len(images),
        "total_lessons": len(lessons),
        "images": images,
        "lessons": lessons,
        "metadata": {
            "pdf_path": PDF_PATH,
            "method": "Méthode syllabique Ratus",
            "target_level": "CP",
            "subjects": ["Français", "Lecture"]
        }
    }

    manifest_path = OUTPUT_BASE / "ratus_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"✅ Manifest saved to {manifest_path}")

    return manifest


def generate_summary_report(manifest: Dict[str, Any]):
    """Génère un rapport récapitulatif de l'extraction"""
    print("\n" + "="*60)
    print("📊 EXTRACTION SUMMARY REPORT")
    print("="*60)
    print(f"\n📖 Source: {manifest['metadata']['pdf_path']}")
    print(f"📅 Extraction date: {manifest['extraction_date']}")
    print(f"\n🖼️  Total images extracted: {manifest['total_images']}")
    print(f"📚 Total lessons identified: {manifest['total_lessons']}")

    print("\n📂 Images by size:")
    images = manifest['images']
    small = len([img for img in images if img['width'] * img['height'] < 50000])
    medium = len([img for img in images if 50000 <= img['width'] * img['height'] < 200000])
    large = len([img for img in images if img['width'] * img['height'] >= 200000])
    print(f"   Small (< 50k pixels): {small}")
    print(f"   Medium (50k-200k): {medium}")
    print(f"   Large (> 200k): {large}")

    print("\n📝 Lessons breakdown:")
    for lesson_num, lesson_data in sorted(manifest['lessons'].items(), key=lambda x: int(x[0]))[:10]:
        print(f"   Lesson {lesson_num}: {len(lesson_data['images'])} images, {len(lesson_data['pages'])} pages")

    if len(manifest['lessons']) > 10:
        print(f"   ... and {len(manifest['lessons']) - 10} more lessons")

    print("\n✅ All files saved to: " + str(OUTPUT_BASE))
    print("="*60)


def main():
    """Fonction principale d'extraction"""
    print("\n" + "🎓 RATUS CONTENT EXTRACTION TOOL 🎓".center(60))
    print("="*60 + "\n")

    # Vérifier que le PDF existe
    if not os.path.exists(PDF_PATH):
        print(f"❌ ERROR: PDF not found at {PDF_PATH}")
        sys.exit(1)

    # Setup
    setup_directories()

    # Extraction des images
    images = extract_images_from_pdf(PDF_PATH)

    if not images:
        print("❌ No images extracted. Check PDF content.")
        sys.exit(1)

    # Extraction du texte
    texts = extract_text_by_page(PDF_PATH)

    # Analyse de la structure
    lessons = analyze_content_structure(images, texts)

    # Création du manifeste
    manifest = create_manifest(images, lessons)

    # Rapport final
    generate_summary_report(manifest)

    print("\n✨ Extraction completed successfully! ✨\n")


if __name__ == "__main__":
    main()
