#!/usr/bin/env python
"""
Simple script to test Vorgaben sanity checking
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VorgabenUI.settings')
django.setup()

from dokumente.utils import check_vorgabe_conflicts, format_conflict_report


def main():
    print("Running Vorgaben sanity check...")
    print("=" * 50)
    
    # Check for conflicts
    conflicts = check_vorgabe_conflicts()
    
    # Generate and display report
    report = format_conflict_report(conflicts, verbose=True)
    print(report)
    
    print("=" * 50)
    
    if conflicts:
        print(f"\n⚠️  Found {len(conflicts)} conflicts that need attention!")
        sys.exit(1)
    else:
        print("✅ All Vorgaben are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()