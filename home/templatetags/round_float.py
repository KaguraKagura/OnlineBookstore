from django import template

register = template.Library()


@register.filter(name='round_float')
def round_float(float_num, decimal_count):
    return round(float_num, decimal_count)
