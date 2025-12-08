from django.contrib import admin
#from nested_inline.admin import NestedStackedInline, NestedModelAdmin
from nested_admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from django import forms
from django.utils.html import format_html
from mptt.forms import TreeNodeMultipleChoiceField
from mptt.admin import DraggableMPTTAdmin
from adminsortable2.admin import SortableInlineAdminMixin, SortableAdminBase

# Register your models here.
from .models import *
from stichworte.models import Stichwort, Stichworterklaerung
from referenzen.models import Referenz



#class ChecklistenForm(forms.ModelForm):
#    class Meta:
#        model=Checklistenfrage
#        fields="__all__"
#        widgets = {
#            'frage': forms.Textarea(attrs={'rows': 1, 'cols': 100}),
#        }

class ChecklistenfragenInline(NestedStackedInline):
    model=Checklistenfrage
    extra=0
    fk_name="vorgabe"
    classes = ['collapse']
    verbose_name_plural = "Checklistenfragen"
    fieldsets = (
        (None, {
            'fields': ('frage',),
            'classes': ('wide',),
        }),
    )


class VorgabeKurztextInline(NestedStackedInline):
    model=VorgabeKurztext
    extra=0
    sortable_field_name = "order"
    show_change_link=True
    classes = ['collapse']
    verbose_name_plural = "Kurztext-Abschnitte"
    fieldsets = (
        (None, {
            'fields': ('abschnitttyp', 'inhalt', 'order'),
            'classes': ('wide',),
        }),
    )

class VorgabeLangtextInline(NestedStackedInline):
    model=VorgabeLangtext
    extra=0
    sortable_field_name = "order"
    show_change_link=True
    classes = ['collapse']
    verbose_name_plural = "Langtext-Abschnitte"
    fieldsets = (
        (None, {
            'fields': ('abschnitttyp', 'inhalt', 'order'),
            'classes': ('wide',),
        }),
    )

class GeltungsbereichInline(NestedStackedInline):
    model=Geltungsbereich
    extra=0
    sortable_field_name = "order"
    show_change_link=True
    classes = ['collapse']
    verbose_name_plural = "Geltungsbereich-Abschnitte"
    fieldsets = (
        (None, {
            'fields': ('abschnitttyp', 'inhalt', 'order'),
            'classes': ('wide',),
        }),
    )

class EinleitungInline(NestedStackedInline):
    model = Einleitung
    extra = 0
    sortable_field_name = "order"
    show_change_link = True
    classes = ['collapse']
    verbose_name_plural = "Einleitungs-Abschnitte"
    fieldsets = (
        (None, {
            'fields': ('abschnitttyp', 'inhalt', 'order'),
            'classes': ('wide',),
        }),
    )

class VorgabeForm(forms.ModelForm):
    referenzen = TreeNodeMultipleChoiceField(queryset=Referenz.objects.all(), required=False)
    
    class Meta:
        model = Vorgabe
        fields = '__all__'
    
    def clean_thema(self):
        """Validate that thema is provided."""
        thema = self.cleaned_data.get('thema')
        if not thema:
            raise forms.ValidationError('Thema ist ein Pflichtfeld. Bitte wählen Sie ein Thema aus.')
        return thema

class VorgabeInline(SortableInlineAdminMixin, NestedStackedInline):
    model = Vorgabe
    form = VorgabeForm
    extra = 0
    sortable_field_name = "order"
    show_change_link = False
    can_delete = False
    inlines = [VorgabeKurztextInline, VorgabeLangtextInline, ChecklistenfragenInline]
    autocomplete_fields = ['stichworte','referenzen','relevanz']
    # Remove collapse class so Vorgaben show by default
    
    fieldsets = (
        ('Grunddaten', {
            'fields': (('order', 'nummer'), ('thema', 'titel')),
            'classes': ('wide',),
        }),
        ('Gültigkeit', {
            'fields': (('gueltigkeit_von', 'gueltigkeit_bis'),),
            'classes': ('wide',),
        }),
        ('Verknüpfungen', {
            'fields': (('referenzen', 'stichworte', 'relevanz'),),
            'classes': ('wide',),
        }),
    )

class StichworterklaerungInline(NestedTabularInline):
    model=Stichworterklaerung
    extra=0
    sortable_field_name = "order"
    ordering=("order",)
    show_change_link = True

@admin.register(Stichwort)
class StichwortAdmin(NestedModelAdmin):
    list_display = ('stichwort', 'vorgaben_count')
    search_fields = ('stichwort',)
    ordering=('stichwort',)
    inlines=[StichworterklaerungInline]
    readonly_fields = ('vorgaben_list',)
    fieldsets = (
        (None, {
            'fields': ('stichwort', 'vorgaben_list')
        }),
    )
    
    def vorgaben_count(self, obj):
        """Count the number of Vorgaben that have this Stichwort"""
        count = obj.vorgabe_set.count()
        return f"{count} Vorgabe{'n' if count != 1 else ''}"
    vorgaben_count.short_description = "Anzahl Vorgaben"
    
    def vorgaben_list(self, obj):
        """Display list of Vorgaben that use this Stichwort"""
        vorgaben = obj.vorgabe_set.select_related('dokument', 'thema').order_by('dokument__nummer', 'nummer')
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
    
    def get_queryset(self, request):
        """Optimize queryset with related data"""
        return super().get_queryset(request).prefetch_related('vorgabe_set')

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):    
    class Media:
        js = ['admin/js/jquery.init.js', 'custom/js/inline_toggle.js']
        css = {'all': ['custom/css/admin_extras.css']}
    list_display=['name']
    ordering = ['name']
    


@admin.register(Dokument)
class DokumentAdmin(SortableAdminBase, NestedModelAdmin):
    actions_on_top=True
    inlines = [EinleitungInline, GeltungsbereichInline, VorgabeInline]
    filter_horizontal=['autoren','pruefende']
    list_display=['nummer','name','dokumententyp','gueltigkeit_von','gueltigkeit_bis','aktiv']
    search_fields=['nummer','name']
    list_filter=['dokumententyp','aktiv','gueltigkeit_von']
    
    fieldsets = (
        ('Grunddaten', {
            'fields': ('nummer', 'name', 'dokumententyp', 'aktiv'),
            'classes': ('wide',),
        }),
        ('Verantwortlichkeiten', {
            'fields': ('autoren', 'pruefende'),
            'classes': ('wide', 'collapse'),
        }),
        ('Gültigkeit & Metadaten', {
            'fields': ('gueltigkeit_von', 'gueltigkeit_bis', 'signatur_cso', 'anhaenge'),
            'classes': ('wide', 'collapse'),
        }),
    )
    
    class Media:
        js = ('admin/js/vorgabe_collapse.js',)
        css = {
            'all': ('admin/css/vorgabe_border.css',)
        }


#admin.site.register(Stichwort)

@admin.register(VorgabenTable)
class VorgabenTableAdmin(admin.ModelAdmin):
    list_display = ['order', 'nummer', 'dokument', 'thema', 'titel', 'gueltigkeit_von', 'gueltigkeit_bis']
    list_display_links = ['dokument']
    list_editable = ['order', 'nummer', 'thema', 'titel', 'gueltigkeit_von', 'gueltigkeit_bis']
    list_filter = ['dokument', 'thema', 'gueltigkeit_von', 'gueltigkeit_bis']
    search_fields = ['nummer', 'titel', 'dokument__nummer', 'dokument__name']
    autocomplete_fields = ['dokument', 'thema', 'stichworte', 'referenzen', 'relevanz']
    ordering = ['order']
    list_per_page = 100

    fieldsets = (
        ('Grunddaten', {
            'fields': ('order', 'nummer', 'dokument', 'thema', 'titel')
        }),
        ('Gültigkeit', {
            'fields': ('gueltigkeit_von', 'gueltigkeit_bis')
        }),
        ('Verknüpfungen', {
            'fields': ('referenzen', 'stichworte', 'relevanz'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Thema)
class ThemaAdmin(admin.ModelAdmin):
    search_fields = ['name']
    ordering = ['name']

@admin.register(Vorgabe)
class VorgabeAdmin(NestedModelAdmin):
    form = VorgabeForm
    list_display = ['vorgabe_nummer', 'titel', 'dokument', 'thema', 'gueltigkeit_von', 'gueltigkeit_bis']
    list_filter = ['dokument', 'thema', 'gueltigkeit_von', 'gueltigkeit_bis']
    search_fields = ['nummer', 'titel', 'dokument__nummer', 'dokument__name']
    autocomplete_fields = ['stichworte', 'referenzen', 'relevanz']
    ordering = ['dokument', 'order']
    
    inlines = [
        VorgabeKurztextInline, 
        VorgabeLangtextInline, 
        ChecklistenfragenInline
    ]
    
    fieldsets = (
        ('Grunddaten', {
            'fields': (('order', 'nummer'), ('dokument', 'thema'), 'titel'),
            'classes': ('wide',),
        }),
        ('Gültigkeit', {
            'fields': (('gueltigkeit_von', 'gueltigkeit_bis'),),
            'classes': ('wide',),
        }),
        ('Verknüpfungen', {
            'fields': (('referenzen', 'stichworte', 'relevanz'),),
            'classes': ('wide',),
        }),
    )
    
    def vorgabe_nummer(self, obj):
        return obj.Vorgabennummer()
    vorgabe_nummer.short_description = 'Vorgabennummer'

admin.site.register(Checklistenfrage)
admin.site.register(Dokumententyp)
admin.site.register(VorgabeComment)

#admin.site.register(Changelog)
