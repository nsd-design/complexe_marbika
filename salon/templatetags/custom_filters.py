from django import template

register = template.Library()


@register.filter
def currency(value):
    print("value :", value)
    try:
        float(value)
        return "{:,.0f} GNF".format(value).replace(",", " ")
    except (ValueError, TypeError):
        return value