#!/usr/bin/env python3
"""
clean-geojson-caltopo.py v1.0 — 15 janvier 2026 à 12:45
Nettoie un fichier GeoJSON pour import CalTopo.

Corrections appliquées :
- Apostrophes courbes → droites
- Clés avec ":" → "_" (ex: description:de → description_de)
- Virgules décimales → points (ex: "0,3m" → "0.3m")
- Caractères spéciaux islandais préservés (UTF-8)

Usage:
    python3 clean-geojson-caltopo.py iceland-fords-osm-caltopo.geojson
    python3 clean-geojson-caltopo.py input.geojson -o output-clean.geojson
"""

import json
import argparse
import re
from pathlib import Path


def clean_string(value: str) -> str:
    """Nettoie une chaîne de caractères."""
    if not isinstance(value, str):
        return value
    
    # Apostrophes courbes → droites
    value = value.replace('´', "'").replace(''', "'").replace(''', "'")
    
    # Guillemets courbes → droits
    value = value.replace('"', '"').replace('"', '"')
    
    # Virgules décimales dans les mesures (ex: "0,3m" → "0.3m")
    value = re.sub(r'(\d),(\d)', r'\1.\2', value)
    
    return value


def clean_properties(props: dict) -> dict:
    """Nettoie les propriétés d'une feature."""
    cleaned = {}
    
    for key, value in props.items():
        # Renommer les clés avec ":" → "_"
        new_key = key.replace(':', '_')
        
        # Nettoyer la valeur si c'est une chaîne
        if isinstance(value, str):
            cleaned[new_key] = clean_string(value)
        else:
            cleaned[new_key] = value
    
    return cleaned


def clean_geojson(input_path: str, output_path: str = None) -> dict:
    """Nettoie un fichier GeoJSON pour CalTopo."""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stats = {
        'total': 0,
        'keys_renamed': 0,
        'strings_cleaned': 0
    }
    
    for feature in data.get('features', []):
        stats['total'] += 1
        props = feature.get('properties', {})
        
        # Compter les modifications
        for key in props:
            if ':' in key:
                stats['keys_renamed'] += 1
        
        for value in props.values():
            if isinstance(value, str):
                cleaned = clean_string(value)
                if cleaned != value:
                    stats['strings_cleaned'] += 1
        
        # Appliquer le nettoyage
        feature['properties'] = clean_properties(props)
    
    # Fichier de sortie
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}-clean{p.suffix}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {'output': output_path, 'stats': stats}


def main():
    parser = argparse.ArgumentParser(
        description="Nettoie un GeoJSON pour import CalTopo"
    )
    parser.add_argument('input', help='Fichier GeoJSON source')
    parser.add_argument('-o', '--output', help='Fichier de sortie (défaut: *-clean.geojson)')
    
    args = parser.parse_args()
    
    result = clean_geojson(args.input, args.output)
    
    print(f"\n✅ Fichier créé : {result['output']}")
    print(f"\n📊 Statistiques :")
    print(f"   • Features traitées : {result['stats']['total']}")
    print(f"   • Clés renommées (: → _) : {result['stats']['keys_renamed']}")
    print(f"   • Chaînes nettoyées : {result['stats']['strings_cleaned']}")


if __name__ == '__main__':
    main()
