from django import template

register = template.Library()
@register.filter
def add_commas(value):

    if isinstance(value, int):
        return '{:,}'.format(value)
    elif isinstance(value, float):
        return '{:,.2f}'.format(value)
    else:
        return value