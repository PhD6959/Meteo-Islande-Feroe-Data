#!/usr/bin/env python3
"""
poi_add_title.py v1.0 — 15 janvier 2026 à 21:45
Ajoute un champ 'title' (requis par CalTopo) aux fichiers POI GeoJSON.

Usage:
    python3 poi_add_title.py grocery-gas-stations.geojson
    python3 poi_add_title.py grocery-gas-stations.geojson -o output-caltopo.geojson
"""

import json
import argparse
from pathlib import Path

def add_title_for_caltopo(input_path: str, output_path: str = None) -> dict:
    """Ajoute le champ 'title' requis par CalTopo pour chaque Feature."""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stats = {'total': 0, 'from_name': 0, 'fallback': 0}
    
    for feature in data.get('features', []):
        stats['total'] += 1
        props = feature.get('properties', {})
        
        name = props.get('name')
        
        if name:
            props['title'] = name
            stats['from_name'] += 1
        else:
            # Fallback: folder ou numéro séquentiel
            fallback = props.get('folder') or f"POI {stats['total']}"
            props['title'] = fallback
            stats['fallback'] += 1
    
    # Fichier de sortie
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}-caltopo{p.suffix}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {'output': output_path, 'stats': stats}

def main():
    parser = argparse.ArgumentParser(
        description="Ajoute un champ 'title' aux POI pour import CalTopo"
    )
    parser.add_argument('input', help='Fichier GeoJSON source')
    parser.add_argument('-o', '--output', help='Fichier de sortie (défaut: *-caltopo.geojson)')
    
    args = parser.parse_args()
    
    result = add_title_for_caltopo(args.input, args.output)
    
    print(f"\n✅ Fichier créé : {result['output']}")
    print(f"\n📊 Statistiques :")
    print(f"   • Features traitées : {result['stats']['total']}")
    print(f"   • Titre depuis 'name' : {result['stats']['from_name']}")
    print(f"   • Fallback : {result['stats']['fallback']}")

if __name__ == '__main__':
    main()
