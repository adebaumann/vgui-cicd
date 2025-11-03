"""
Utility functions for Vorgaben sanity checking
"""
import datetime
from django.db.models import Count
from itertools import combinations
from dokumente.models import Vorgabe


def check_vorgabe_conflicts():
    """
    Check for conflicts in Vorgaben.
    
    Main rule: If there are two Vorgaben with the same number, Thema and Dokument,
    their valid_from and valid_to date ranges shouldn't intersect.
    
    Returns:
        list: List of conflict dictionaries
    """
    conflicts = []
    
    # Find Vorgaben with same dokument, thema, and nummer
    duplicate_groups = (
        Vorgabe.objects.values('dokument', 'thema', 'nummer')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )
    
    for group in duplicate_groups:
        # Get all Vorgaben in this group
        vorgaben = Vorgabe.objects.filter(
            dokument=group['dokument'],
            thema=group['thema'], 
            nummer=group['nummer']
        )
        
        # Check all pairs for date range intersections
        for vorgabe1, vorgabe2 in combinations(vorgaben, 2):
            if date_ranges_intersect(
                vorgabe1.gueltigkeit_von, vorgabe1.gueltigkeit_bis,
                vorgabe2.gueltigkeit_von, vorgabe2.gueltigkeit_bis
            ):
                conflicts.append({
                    'vorgabe1': vorgabe1,
                    'vorgabe2': vorgabe2,
                    'conflict_type': 'date_range_intersection',
                    'message': f"Vorgaben {vorgabe1.Vorgabennummer()} and {vorgabe2.Vorgabennummer()} "
                              f"have intersecting validity periods"
                })
    
    return conflicts


def date_ranges_intersect(start1, end1, start2, end2):
    """
    Check if two date ranges intersect.
    None end date means open-ended range.
    
    Args:
        start1, start2: Start dates
        end1, end2: End dates (can be None for open-ended)
        
    Returns:
        bool: True if ranges intersect
    """
    # If either start date is None, treat it as invalid case
    if not start1 or not start2:
        return False
        
    # If end date is None, treat it as far future
    end1 = end1 or datetime.date.max
    end2 = end2 or datetime.date.max
    
    # Ranges intersect if start1 <= end2 and start2 <= end1
    return start1 <= end2 and start2 <= end1


def format_conflict_report(conflicts, verbose=False):
    """
    Format conflicts into a readable report.
    
    Args:
        conflicts: List of conflict dictionaries
        verbose: Whether to show detailed information
        
    Returns:
        str: Formatted report
    """
    if not conflicts:
        return "✓ No conflicts found in Vorgaben"
    
    lines = [f"Found {len(conflicts)} conflicts:"]
    
    for i, conflict in enumerate(conflicts, 1):
        lines.append(f"\n{i}. {conflict['message']}")
        
        if verbose:
            v1 = conflict['vorgabe1']
            v2 = conflict['vorgabe2']
            
            lines.append(f"   Vorgabe 1: {v1.Vorgabennummer()}")
            lines.append(f"   Valid from: {v1.gueltigkeit_von} to {v1.gueltigkeit_bis or 'unlimited'}")
            lines.append(f"   Title: {v1.titel}")
            
            lines.append(f"   Vorgabe 2: {v2.Vorgabennummer()}")
            lines.append(f"   Valid from: {v2.gueltigkeit_von} to {v2.gueltigkeit_bis or 'unlimited'}")
            lines.append(f"   Title: {v2.titel}")
        
        # Show the overlapping period
        v1 = conflict['vorgabe1']
        v2 = conflict['vorgabe2']
        overlap_start = max(v1.gueltigkeit_von, v2.gueltigkeit_von)
        overlap_end = min(
            v1.gueltigkeit_bis or datetime.date.max,
            v2.gueltigkeit_bis or datetime.date.max
        )
        
        if overlap_end != datetime.date.max:
            lines.append(f"   Overlap: {overlap_start} to {overlap_end}")
        else:
            lines.append(f"   Overlap starts: {overlap_start} (no end)")
    
    return "\n".join(lines)