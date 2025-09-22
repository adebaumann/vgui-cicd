
from django.contrib import admin
from nested_admin import NestedStackedInline, NestedModelAdmin, NestedTabularInline
from django import forms
from .models import Rolle, RollenBeschreibung

class RollenBeschreibungInline(NestedStackedInline):
    model = RollenBeschreibung
    extra = 0
    sortable_field_name = "order"
    ordering = ("order",)
    show_change_link = True


@admin.register(Rolle)
class RollenAdmin(NestedModelAdmin):
    search_fields = ('name',)
    ordering = ('name',)
    inlines = [RollenBeschreibungInline]
