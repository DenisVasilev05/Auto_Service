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

@register.filter(name='compress_hours')
def compress_hours(business_hours):
    """Return a list of strings that compress consecutive days with identical working hours.
    Input example (dict):
        {
            'Monday': '09:00 - 18:00',
            'Tuesday': '09:00 - 18:00',
            'Wednesday': '09:00 - 18:00',
            'Thursday': '09:00 - 18:00',
            'Friday': '09:00 - 16:00',
            'Saturday': 'Closed',
            'Sunday': 'Closed',
        }
    Output example (list):
        [
            'Monday to Thursday: 09:00 - 18:00',
            'Friday: 09:00 - 16:00',
            'Saturday to Sunday: Closed',
        ]
    """
    if not isinstance(business_hours, dict):
        return []

    day_order = [
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ]

    sequences = []  # list of tuples (start_day, end_day, hours)
    prev_hours = None
    start_day = None
    end_day = None

    for day in day_order:
        hours = business_hours.get(day)
        if hours is None:
            continue
        if prev_hours is None:
            # start first sequence
            prev_hours = hours
            start_day = day
            end_day = day
        elif hours == prev_hours:
            # extend current sequence
            end_day = day
        else:
            # close current sequence and start new
            sequences.append((start_day, end_day, prev_hours))
            start_day = day
            end_day = day
            prev_hours = hours

    if prev_hours is not None:
        sequences.append((start_day, end_day, prev_hours))

    # Format sequences
    formatted = []
    for start, end, hours in sequences:
        if start == end:
            formatted.append(f"{start}: {hours}")
        else:
            formatted.append(f"{start} to {end}: {hours}")
    return formatted 