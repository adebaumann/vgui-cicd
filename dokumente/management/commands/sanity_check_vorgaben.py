from django.core.management.base import BaseCommand
from django.db import transaction
from dokumente.models import Vorgabe
import datetime


class Command(BaseCommand):
    help = 'Run sanity checks on Vorgaben to detect conflicts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix conflicts (not implemented yet)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS('Starting Vorgaben sanity check...'))
        
        # Run the sanity check
        conflicts = Vorgabe.sanity_check_vorgaben()
        
        if not conflicts:
            self.stdout.write(self.style.SUCCESS('✓ No conflicts found in Vorgaben'))
            return
        
        self.stdout.write(
            self.style.WARNING(f'Found {len(conflicts)} conflicts:')
        )
        
        for i, conflict in enumerate(conflicts, 1):
            self._display_conflict(i, conflict)
        
        if options['fix']:
            self.stdout.write(self.style.ERROR('Auto-fix not implemented yet'))

    def _display_conflict(self, index, conflict):
        """Display a single conflict"""
        v1 = conflict['vorgabe1']
        v2 = conflict['vorgabe2']
        
        self.stdout.write(f"\n{index}. {conflict['message']}")
        
        if self.verbose:
            self.stdout.write(f"   Vorgabe 1: {v1.Vorgabennummer()}")
            self.stdout.write(f"   Valid from: {v1.gueltigkeit_von} to {v1.gueltigkeit_bis or 'unlimited'}")
            self.stdout.write(f"   Title: {v1.titel}")
            
            self.stdout.write(f"   Vorgabe 2: {v2.Vorgabennummer()}")
            self.stdout.write(f"   Valid from: {v2.gueltigkeit_von} to {v2.gueltigkeit_bis or 'unlimited'}")
            self.stdout.write(f"   Title: {v2.titel}")
        
        # Show the overlapping period
        overlap_start = max(v1.gueltigkeit_von, v2.gueltigkeit_von)
        overlap_end = min(
            v1.gueltigkeit_bis or datetime.date.max,
            v2.gueltigkeit_bis or datetime.date.max
        )
        
        if overlap_end != datetime.date.max:
            self.stdout.write(f"   Overlap: {overlap_start} to {overlap_end}")
        else:
            self.stdout.write(f"   Overlap starts: {overlap_start} (no end)")