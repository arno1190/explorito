#!/usr/bin/env python3
"""
Script pour créer la structure de leçons basée sur la méthode Ratus
Organise les pages extraites en leçons pédagogiques cohérentes
"""

import json
from pathlib import Path

OUTPUT_BASE = Path(__file__).parent.parent / "extracted_content"
MANIFEST_PATH = OUTPUT_BASE / "ratus_manifest.json"

# Structure des leçons Ratus (progression syllabique typique)
RATUS_LESSON_STRUCTURE = [
    {
        "lesson_number": 1,
        "title": "Le rat et le chat",
        "sounds": ["a"],
        "words": ["rat", "chat", "a"],
        "pages": list(range(10, 15)),
        "type": "introduction"
    },
    {
        "lesson_number": 2,
        "title": "Marou le pirate",
        "sounds": ["m", "ma", "mo", "mu"],
        "words": ["Marou", "moto", "ma", "ami"],
        "pages": list(range(15, 20)),
        "type": "syllabe_simple"
    },
    {
        "lesson_number": 3,
        "title": "Ralette",
        "sounds": ["r", "ra", "ri", "ro", "ru"],
        "words": ["Ralette", "Ratus", "rat", "riz", "rue"],
        "pages": list(range(20, 25)),
        "type": "syllabe_simple"
    },
    {
        "lesson_number": 4,
        "title": "L'école de Ratus",
        "sounds": ["l", "la", "le", "li", "lo", "lu"],
        "words": ["école", "lit", "loup", "bol", "mal"],
        "pages": list(range(25, 30)),
        "type": "syllabe_simple"
    },
    {
        "lesson_number": 5,
        "title": "Mina la fourmi",
        "sounds": ["i", "mi", "ni"],
        "words": ["Mina", "fourmi", "mini", "ami", "nid"],
        "pages": list(range(30, 35)),
        "type": "syllabe_simple"
    },
    {
        "lesson_number": 6,
        "title": "Papa, maman",
        "sounds": ["p", "pa", "pi", "po"],
        "words": ["papa", "pipe", "pari", "pur", "puma"],
        "pages": list(range(35, 40)),
        "type": "syllabe_simple"
    },
    {
        "lesson_number": 7,
        "title": "Belo a disparu",
        "sounds": ["b", "ba", "bi", "bo", "bu"],
        "words": ["Belo", "balle", "bol", "bar", "bébé"],
        "pages": list(range(40, 45)),
        "type": "syllabe_simple"
    },
    {
        "lesson_number": 8,
        "title": "Le vélo de Ratus",
        "sounds": ["v", "va", "vi", "vo", "vu"],
        "words": ["vélo", "vol", "vase", "voile", "vu"],
        "pages": list(range(45, 50)),
        "type": "syllabe_simple"
    },
    {
        "lesson_number": 9,
        "title": "Ratus à la télévision",
        "sounds": ["t", "ta", "ti", "to", "tu"],
        "words": ["télé", "tarte", "tube", "moto", "porte"],
        "pages": list(range(50, 55)),
        "type": "syllabe_simple"
    },
    {
        "lesson_number": 10,
        "title": "Ratus raconte des salades",
        "sounds": ["s", "sa", "si", "so", "su"],
        "words": ["salade", "salle", "sucre", "sol", "rose"],
        "pages": list(range(55, 60)),
        "type": "syllabe_simple"
    },
    {
        "lesson_number": 11,
        "title": "Au feu !",
        "sounds": ["f", "fa", "fi", "fo", "fu"],
        "words": ["feu", "farine", "fusée", "café", "sofa"],
        "pages": list(range(60, 65)),
        "type": "syllabe_simple"
    },
    {
        "lesson_number": 12,
        "title": "Une drôle de poule",
        "sounds": ["ou"],
        "words": ["poule", "loup", "fou", "pour", "jour"],
        "pages": list(range(65, 70)),
        "type": "son_complexe"
    },
    {
        "lesson_number": 13,
        "title": "On a volé Marou",
        "sounds": ["on"],
        "words": ["on", "bon", "pont", "melon", "mouton"],
        "pages": list(range(70, 75)),
        "type": "son_complexe"
    },
    {
        "lesson_number": 14,
        "title": "Ratus champion",
        "sounds": ["ch"],
        "words": ["champion", "chat", "chocolat", "cheval", "bouche"],
        "pages": list(range(75, 80)),
        "type": "son_complexe"
    },
    {
        "lesson_number": 15,
        "title": "Un invité bizarre",
        "sounds": ["in", "im"],
        "words": ["invité", "lapin", "pain", "timbre", "impossible"],
        "pages": list(range(80, 85)),
        "type": "son_complexe"
    },
    {
        "lesson_number": 16,
        "title": "Ratus sur l'île déserte",
        "sounds": ["an", "am", "en", "em"],
        "words": ["île", "banane", "lampe", "dent", "temps"],
        "pages": list(range(85, 90)),
        "type": "son_complexe"
    },
    {
        "lesson_number": 17,
        "title": "La soupe aux étoiles",
        "sounds": ["é", "è", "ê"],
        "words": ["étoile", "télé", "fenêtre", "forêt", "fête"],
        "pages": list(range(90, 95)),
        "type": "voyelles_accentuées"
    },
    {
        "lesson_number": 18,
        "title": "Ratus magicien",
        "sounds": ["c", "ç"],
        "words": ["magicien", "glace", "ça", "garçon", "leçon"],
        "pages": list(range(95, 100)),
        "type": "c_dur_doux"
    },
    {
        "lesson_number": 19,
        "title": "Un voyage en auto",
        "sounds": ["au", "eau"],
        "words": ["auto", "bateau", "eau", "chaud", "cadeau"],
        "pages": list(range(100, 105)),
        "type": "son_complexe"
    },
    {
        "lesson_number": 20,
        "title": "Un roi sur un pois",
        "sounds": ["oi"],
        "words": ["roi", "pois", "voiture", "étoile", "voir"],
        "pages": list(range(105, 110)),
        "type": "son_complexe"
    },
    {
        "lesson_number": 21,
        "title": "Ratus chez le coiffeur",
        "sounds": ["eu", "œu"],
        "words": ["feu", "deux", "cœur", "peur", "œuf"],
        "pages": list(range(110, 115)),
        "type": "son_complexe"
    },
    {
        "lesson_number": 22,
        "title": "La grande aig uille",
        "sounds": ["g", "gu"],
        "words": ["aiguille", "vague", "guide", "guitare", "fatigue"],
        "pages": list(range(115, 120)),
        "type": "g_dur_doux"
    },
    {
        "lesson_number": 23,
        "title": "La montagne",
        "sounds": ["gn"],
        "words": ["montagne", "agneau", "baignoire", "ligne", "champignon"],
        "pages": list(range(120, 125)),
        "type": "son_complexe"
    },
    {
        "lesson_number": 24,
        "title": "Récapitulation",
        "sounds": ["révision"],
        "words": [],
        "pages": list(range(125, 131)),
        "type": "révision"
    }
]


def load_manifest():
    """Charge le manifeste JSON"""
    with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_manifest(manifest):
    """Sauvegarde le manifeste JSON"""
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def create_lesson_structure(manifest):
    """
    Crée une structure de leçons détaillée basée sur la méthode Ratus

    Args:
        manifest: Le manifeste actuel

    Returns:
        Manifeste mis à jour avec la structure des leçons
    """
    print("\n📚 Creating lesson structure...")
    print("="*60)

    # Mapper les images aux leçons
    all_images = manifest.get('images', [])

    structured_lessons = []

    for lesson_info in RATUS_LESSON_STRUCTURE:
        lesson = {
            "id": f"ratus_lesson_{lesson_info['lesson_number']:02d}",
            "number": lesson_info['lesson_number'],
            "title": lesson_info['title'],
            "type": lesson_info['type'],
            "sounds": lesson_info['sounds'],
            "key_words": lesson_info['words'],
            "pages": lesson_info['pages'],
            "images": []
        }

        # Associer les images de ces pages
        for page_num in lesson_info['pages']:
            page_images = [img for img in all_images if img.get('page') == page_num]
            lesson['images'].extend(page_images)

        lesson['image_count'] = len(lesson['images'])

        structured_lessons.append(lesson)

        print(f"✅ Lesson {lesson['number']:2d}: {lesson['title']}")
        print(f"   Sounds: {', '.join(lesson['sounds'])}")
        print(f"   Images: {lesson['image_count']}")

    print(f"\n{'='*60}")
    print(f"Total lessons created: {len(structured_lessons)}")
    print("="*60)

    return structured_lessons


def main():
    print("\n" + "📖 RATUS LESSON STRUCTURE CREATOR 📖".center(60))
    print("="*60)

    manifest = load_manifest()
    structured_lessons = create_lesson_structure(manifest)

    # Mise à jour du manifeste
    manifest['structured_lessons'] = structured_lessons
    manifest['lesson_metadata'] = {
        'total_lessons': len(structured_lessons),
        'lesson_types': list(set(lesson['type'] for lesson in structured_lessons)),
        'progression': 'syllabique',
        'method': 'Ratus et Ses Amis'
    }

    save_manifest(manifest)

    print("\n✅ Manifest updated with lesson structure")
    print(f"📄 Saved to: {MANIFEST_PATH}")
    print("\n✨ Lesson structure creation completed! ✨\n")


if __name__ == "__main__":
    main()
