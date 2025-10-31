from django.contrib import admin
#from nested_inline.admin import NestedStackedInline, NestedModelAdmin
from nested_admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from django import forms
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

class ChecklistenfragenInline(NestedTabularInline):
    model=Checklistenfrage
    extra=0
    fk_name="vorgabe"
#    form=ChecklistenForm
    classes = ['collapse']


class VorgabeKurztextInline(NestedTabularInline):
    model=VorgabeKurztext
    extra=0
    sortable_field_name = "order"
    show_change_link=True
    classes = ['collapse']
    #inline=inhalt

class VorgabeLangtextInline(NestedTabularInline):
    model=VorgabeLangtext
    extra=0
    sortable_field_name = "order"
    show_change_link=True
    classes = ['collapse']
    #inline=inhalt

class GeltungsbereichInline(NestedTabularInline):
    model=Geltungsbereich
    extra=0
    sortable_field_name = "order"
    show_change_link=True
    classes = ['collapse']
    classes = ['collapse']
    #inline=inhalt

class EinleitungInline(NestedTabularInline):
        model = Einleitung
        extra = 0
        sortable_field_name = "order"
        show_change_link = True
        classes = ['collapse']

class VorgabeForm(forms.ModelForm):
    referenzen = TreeNodeMultipleChoiceField(queryset=Referenz.objects.all(), required=False)
    class Meta:
        model = Vorgabe
        fields = '__all__'

class VorgabeInline(SortableInlineAdminMixin, NestedTabularInline):  # or StackedInline for more vertical layout
    model = Vorgabe
    form = VorgabeForm
    extra = 0
    sortable_field_name = "order"  # Add this - make sure your Vorgabe model has an 'order' field
    #show_change_link = True
    inlines = [VorgabeKurztextInline,VorgabeLangtextInline,ChecklistenfragenInline]
    autocomplete_fields = ['stichworte','referenzen','relevanz']
    #search_fields=['nummer','name']ModelAdmin.
    list_filter=['stichworte']
    #classes=["collapse"]

class StichworterklaerungInline(NestedTabularInline):
    model=Stichworterklaerung
    extra=0
    sortable_field_name = "order"
    ordering=("order",)
    show_change_link = True

@admin.register(Stichwort)
class StichwortAdmin(NestedModelAdmin):
    search_fields = ('stichwort',)
    ordering=('stichwort',)
    inlines=[StichworterklaerungInline]

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):    
    class Media:
        js = ['admin/js/jquery.init.js', 'custom/js/inline_toggle.js']
        css = {'all': ['custom/css/admin_extras.css']}
    list_display=['name']
    


@admin.register(Dokument)
class DokumentAdmin(SortableAdminBase, NestedModelAdmin):
    actions_on_top=True
    inlines = [EinleitungInline,GeltungsbereichInline,VorgabeInline]
    #filter_horizontal=['autoren','pruefende']
    list_display=['nummer','name','dokumententyp']
    search_fields=['nummer','name']
    class Media:
#        js = ('admin/js/vorgabe_collapse.js',)
        css = {
            'all': ('admin/css/vorgabe_border.css',
#                    'admin/css/vorgabe_collapse.css',
                    )
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

admin.site.register(Checklistenfrage)
admin.site.register(Dokumententyp)
#admin.site.register(Person)
#admin.site.register(Referenz, DraggableM§PTTAdmin)
admin.site.register(Vorgabe)

#admin.site.register(Changelog)
