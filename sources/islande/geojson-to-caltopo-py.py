#!/usr/bin/env python3
"""
convert_geojson_caltopo.py
Version 1.0 — 15 janvier 2026

Convertit tous les fichiers .json et .geojson d'un dossier
au format CalTopo (avec folderId, class, title, etc.)

Usage:
    python convert_geojson_caltopo.py [dossier]
    
Si aucun dossier n'est spécifié, utilise le dossier courant.
Les fichiers convertis sont sauvegardés avec le suffixe -caltopo.geojson
"""

import json
import os
import sys
import uuid
from pathlib import Path


def generate_uuid():
    """Génère un UUID au format CalTopo"""
    return str(uuid.uuid4())


def get_color_from_properties(props):
    """Extrait la couleur depuis les propriétés existantes"""
    # Chercher dans différents champs possibles
    for key in ['marker-color', 'color', 'stroke', 'fill']:
        if key in props and props[key]:
            color = str(props[key]).replace('#', '').upper()
            if len(color) == 6:
                return color
    return 'FF0000'  # Rouge par défaut


def get_title_from_properties(props):
    """Extrait le titre depuis les propriétés existantes"""
    for key in ['title', 'name', 'Name', 'NAME', 'label', 'Label']:
        if key in props and props[key]:
            return str(props[key])
    return 'Sans nom'


def get_description_from_properties(props):
    """Extrait la description depuis les propriétés existantes"""
    for key in ['description', 'desc', 'Description', 'comment', 'comments']:
        if key in props and props[key]:
            return str(props[key])
    return ''


def convert_coordinates(coords, geom_type):
    """Convertit les coordonnées au format CalTopo [lon, lat, 0, 0]"""
    if geom_type == 'Point':
        # Point simple
        if len(coords) >= 2:
            return [coords[0], coords[1], 0, 0]
        return coords
    elif geom_type == 'LineString':
        # Ligne
        return [[c[0], c[1], 0, 0] for c in coords]
    elif geom_type == 'Polygon':
        # Polygone (liste de rings)
        return [[[c[0], c[1], 0, 0] for c in ring] for ring in coords]
    elif geom_type == 'MultiPoint':
        return [[c[0], c[1], 0, 0] for c in coords]
    elif geom_type == 'MultiLineString':
        return [[[c[0], c[1], 0, 0] for c in line] for line in coords]
    elif geom_type == 'MultiPolygon':
        return [[[[c[0], c[1], 0, 0] for c in ring] for ring in poly] for poly in coords]
    return coords


def get_class_from_geometry(geom_type):
    """Détermine la class CalTopo selon le type de géométrie"""
    if geom_type == 'Point':
        return 'Marker'
    elif geom_type in ['LineString', 'MultiLineString', 'Polygon', 'MultiPolygon']:
        return 'Shape'
    return 'Marker'


def convert_feature(feature, folder_id):
    """Convertit une feature au format CalTopo"""
    props = feature.get('properties', {}) or {}
    geom = feature.get('geometry')
    
    if not geom:
        return None
    
    geom_type = geom.get('type', 'Point')
    coords = geom.get('coordinates', [])
    
    title = get_title_from_properties(props)
    description = get_description_from_properties(props)
    color = get_color_from_properties(props)
    feature_class = get_class_from_geometry(geom_type)
    
    new_feature = {
        'type': 'Feature',
        'id': generate_uuid(),
        'geometry': {
            'type': geom_type,
            'coordinates': convert_coordinates(coords, geom_type)
        },
        'properties': {
            'title': title,
            'description': description,
            'class': feature_class,
            'folderId': folder_id,
            'visible': True,
            'labelVisible': True
        }
    }
    
    # Ajouter les propriétés spécifiques selon le type
    if feature_class == 'Marker':
        new_feature['properties'].update({
            'marker-symbol': 'point',
            'marker-color': color,
            'marker-size': '1',
            'marker-rotation': None
        })
    else:
        new_feature['properties'].update({
            'stroke': f'#{color}',
            'stroke-width': 3,
            'stroke-opacity': 1,
            'fill': f'#{color}',
            'fill-opacity': 0.2
        })
    
    return new_feature


def convert_file(input_path, output_path):
    """Convertit un fichier GeoJSON au format CalTopo"""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  ❌ Erreur JSON: {e}")
        return None
    except Exception as e:
        print(f"  ❌ Erreur lecture: {e}")
        return None
    
    # Extraire les features
    if data.get('type') == 'FeatureCollection':
        features = data.get('features', [])
    elif data.get('type') == 'Feature':
        features = [data]
    else:
        print(f"  ⚠️  Format non reconnu")
        return None
    
    if not features:
        print(f"  ⚠️  Aucune feature trouvée")
        return None
    
    # Créer le folder pour ce fichier
    folder_name = Path(input_path).stem
    folder_id = generate_uuid()
    
    folder_feature = {
        'type': 'Feature',
        'id': folder_id,
        'geometry': None,
        'properties': {
            'title': folder_name,
            'class': 'Folder',
            'visible': True,
            'labelVisible': True
        }
    }
    
    # Convertir les features
    converted_features = [folder_feature]
    converted_count = 0
    skipped_count = 0
    
    for feature in features:
        converted = convert_feature(feature, folder_id)
        if converted:
            converted_features.append(converted)
            converted_count += 1
        else:
            skipped_count += 1
    
    # Créer le GeoJSON CalTopo
    output_data = {
        'type': 'FeatureCollection',
        'features': converted_features
    }
    
    # Sauvegarder
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ❌ Erreur écriture: {e}")
        return None
    
    return {
        'converted': converted_count,
        'skipped': skipped_count,
        'folder': folder_name
    }


def main():
    # Déterminer le dossier
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
    else:
        folder = Path.cwd()
    
    if not folder.exists():
        print(f"❌ Dossier inexistant: {folder}")
        sys.exit(1)
    
    print(f"📁 Dossier: {folder}")
    print("-" * 50)
    
    # Trouver les fichiers .json et .geojson
    files = list(folder.glob('*.json')) + list(folder.glob('*.geojson'))
    
    # Exclure les fichiers déjà convertis
    files = [f for f in files if not f.stem.endswith('-caltopo')]
    
    if not files:
        print("⚠️  Aucun fichier .json ou .geojson trouvé")
        sys.exit(0)
    
    print(f"📄 {len(files)} fichier(s) à convertir\n")
    
    total_converted = 0
    total_skipped = 0
    success_count = 0
    
    for filepath in sorted(files):
        print(f"🔄 {filepath.name}")
        
        output_name = filepath.stem + '-caltopo.geojson'
        output_path = filepath.parent / output_name
        
        result = convert_file(filepath, output_path)
        
        if result:
            print(f"   ✅ {result['converted']} features → {output_name}")
            if result['skipped'] > 0:
                print(f"   ⚠️  {result['skipped']} feature(s) ignorée(s)")
            total_converted += result['converted']
            total_skipped += result['skipped']
            success_count += 1
        print()
    
    print("-" * 50)
    print(f"✅ {success_count}/{len(files)} fichier(s) converti(s)")
    print(f"📊 {total_converted} features au total")
    if total_skipped > 0:
        print(f"⚠️  {total_skipped} feature(s) ignorée(s)")


if __name__ == '__main__':
    main()
