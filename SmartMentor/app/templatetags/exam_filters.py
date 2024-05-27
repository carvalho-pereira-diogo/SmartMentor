from django import template
from app.models import Option

register = template.Library()

# Custom template filter to get the value of a dictionary key
@register.filter
def get_key(value, arg):
    return value.get(str(arg))

# Custom template tag to get the text of an option
@register.simple_tag
def get_option_text(question_id, user_answer, options):
    try:
        option = options.get(question_id=question_id, letter=user_answer)
        return option.text
    except Option.DoesNotExist:
        return 'Not available'
