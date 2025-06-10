from django import template

register = template.Library()

@register.filter(name='get_range')
def get_range(value):
    """
    Filter - returns a list containing range made from given value
    Usage (in template):
    {% for i in rating|get_range %}
        <i class="fas fa-star"></i>
    {% endfor %}
    """
    try:
        value = int(value)
        if value < 0:
            value = 0
        elif value > 5:  # Assuming 5-star rating system
            value = 5
        return range(value)
    except (ValueError, TypeError):
        return range(0)  # Return empty range if value is invalid 