# attendance/templatetags/template_filters.py

from django import template

register = template.Library()

@register.filter
def present_count(records):
    return records.filter(status='PRESENT').count()

@register.filter
def absent_count(records):
    return records.filter(status='ABSENT').count()
