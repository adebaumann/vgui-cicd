from django.contrib import admin
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
    inlines=[ReferenzerklaerungInline]
    list_display =['Path']
    search_fields=("referenz",)