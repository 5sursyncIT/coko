#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/home/youssoupha/coko/backend')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coko.settings_local')

# Setup Django
django.setup()

from django.db import connection

def inspect_table_structure():
    cursor = connection.cursor()
    
    # Get table info for reading_sessions
    cursor.execute("PRAGMA table_info(reading_sessions);")
    reading_sessions_info = cursor.fetchall()
    
    print("=== Structure de la table reading_sessions ===")
    for column in reading_sessions_info:
        print(f"Column: {column[1]}, Type: {column[2]}, NotNull: {column[3]}, Default: {column[4]}, PK: {column[5]}")
    
    # Get table info for bookmarks
    cursor.execute("PRAGMA table_info(bookmarks);")
    bookmarks_info = cursor.fetchall()
    
    print("\n=== Structure de la table bookmarks ===")
    for column in bookmarks_info:
        print(f"Column: {column[1]}, Type: {column[2]}, NotNull: {column[3]}, Default: {column[4]}, PK: {column[5]}")
    
    cursor.close()

if __name__ == '__main__':
    inspect_table_structure()