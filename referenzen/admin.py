from django.contrib import admin
from django.utils.html import format_html
from nested_admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from .models import *

# Register your models here.
class ReferenzerklaerungInline(NestedStackedInline):
    model=Referenzerklaerung
    extra=0
    sortable_field_name="order"
    show_change_link = True

@admin.register(Referenz)
class ReferenzAdmin(NestedModelAdmin):
    list_display = ('Path', 'vorgaben_count')
    inlines=[ReferenzerklaerungInline]
    search_fields=("name_nummer","Path")
    readonly_fields=("vorgaben_list",)
    fieldsets = (
        (None, {
            'fields': ('name_nummer','name_text','oberreferenz','url', 'vorgaben_list')
        }),
    )

    def vorgaben_count(self, obj):
        """Count the number of Vorgaben that have this Stichwort"""
        count = obj.vorgabe_set.count()
        return f"{count} Vorgabe{'n' if count != 1 else ''}"
    vorgaben_count.short_description = "Anzahl Vorgaben"

    def vorgaben_list(self, obj):
        """Display list of Vorgaben that use this Stichwort"""
        vorgaben = obj.vorgabe_set.order_by('dokument__nummer', 'nummer')
        vorgaben_list = list(vorgaben)  # Evaluate queryset once
        count = len(vorgaben_list)
        if count == 0:
            return format_html("<em>Keine Vorgaben gefunden</em><p><strong>Gesamt: 0 Vorgaben</strong></p>")

        html = "<div style='max-height: 300px; overflow-y: auto;'>"
        html += "<table style='width: 100%; border-collapse: collapse;'>"
        html += "<thead><tr style='background-color: #f5f5f5;'>"
        html += "<th style='padding: 8px; border: 1px solid #ddd; text-align: left;'>Vorgabe</th>"
        html += "<th style='padding: 8px; border: 1px solid #ddd; text-align: left;'>Titel</th>"
        html += "<th style='padding: 8px; border: 1px solid #ddd; text-align: left;'>Dokument</th>"
        html += "</tr></thead>"
        html += "<tbody>"

        for vorgabe in vorgaben_list:
            html += "<tr>"
            html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{vorgabe.Vorgabennummer()}</td>"
            html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{vorgabe.titel}</td>"
            html += f"<td style='padding: 6px; border: 1px solid #ddd;'>{vorgabe.dokument.nummer} – {vorgabe.dokument.name}</td>"
            html += "</tr>"

        html += "</tbody></table>"
        html += f"</div><p><strong>Gesamt: {count} Vorgabe{'n' if count != 1 else ''}</strong></p>"

        return format_html(html)

    vorgaben_list.short_description = "Zugeordnete Vorgaben"

