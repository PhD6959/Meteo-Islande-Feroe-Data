#!/usr/bin/env python3
"""
geojson-to-gpx.py v1.0 — 15 janvier 2026 à 13:15
Convertit un fichier GeoJSON (points) en GPX pour import CalTopo.

Usage:
    python3 geojson-to-gpx.py iceland-fords-osm-caltopo.geojson
    python3 geojson-to-gpx.py input.geojson -o output.gpx
"""

import json
import argparse
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def clean_text(text: str) -> str:
    """Nettoie le texte pour XML."""
    if not isinstance(text, str):
        return str(text) if text else ""
    # Apostrophes et guillemets
    text = text.replace('´', "'").replace(''', "'").replace(''', "'")
    text = text.replace('"', '"').replace('"', '"')
    return text


def geojson_to_gpx(input_path: str, output_path: str = None) -> dict:
    """Convertit un GeoJSON en GPX."""
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Créer la structure GPX
    gpx = Element('gpx')
    gpx.set('version', '1.1')
    gpx.set('creator', 'geojson-to-gpx.py')
    gpx.set('xmlns', 'http://www.topografix.com/GPX/1/1')
    
    stats = {'total': 0, 'converted': 0, 'skipped': 0}
    
    for feature in data.get('features', []):
        stats['total'] += 1
        
        geom = feature.get('geometry', {})
        props = feature.get('properties', {})
        
        # Seulement les points
        if geom.get('type') != 'Point':
            stats['skipped'] += 1
            continue
        
        coords = geom.get('coordinates', [])
        if len(coords) < 2:
            stats['skipped'] += 1
            continue
        
        lon, lat = coords[0], coords[1]
        
        # Créer le waypoint
        wpt = SubElement(gpx, 'wpt')
        wpt.set('lat', str(lat))
        wpt.set('lon', str(lon))
        
        # Nom (title ou name ou fallback)
        name = props.get('title') or props.get('name') or f"POI {stats['total']}"
        name_el = SubElement(wpt, 'name')
        name_el.text = clean_text(name)
        
        # Description (compilation des propriétés utiles)
        desc_parts = []
        for key in ['description', 'depth', 'fixme', 'note', 'surface']:
            if key in props and props[key]:
                desc_parts.append(f"{key}: {props[key]}")
        
        if desc_parts:
            desc_el = SubElement(wpt, 'desc')
            desc_el.text = clean_text(' | '.join(desc_parts))
        
        # Symbole (pour CalTopo)
        sym_el = SubElement(wpt, 'sym')
        sym_el.text = 'Waypoint'
        
        stats['converted'] += 1
    
    # Fichier de sortie
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}.gpx")
    
    # Écrire le GPX avec indentation
    xml_str = tostring(gpx, encoding='unicode')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
    
    # Supprimer la déclaration XML dupliquée
    lines = pretty_xml.split('\n')
    if lines[0].startswith('<?xml'):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return {'output': output_path, 'stats': stats}


def main():
    parser = argparse.ArgumentParser(
        description="Convertit un GeoJSON en GPX pour CalTopo"
    )
    parser.add_argument('input', help='Fichier GeoJSON source')
    parser.add_argument('-o', '--output', help='Fichier GPX de sortie')
    
    args = parser.parse_args()
    
    result = geojson_to_gpx(args.input, args.output)
    
    print(f"\n✅ Fichier créé : {result['output']}")
    print(f"\n📊 Statistiques :")
    print(f"   • Features lues : {result['stats']['total']}")
    print(f"   • Waypoints créés : {result['stats']['converted']}")
    print(f"   • Ignorées (non-points) : {result['stats']['skipped']}")


if __name__ == '__main__':
    main()
