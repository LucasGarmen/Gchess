from django import template
from games.rewards import summary
from games.reward_texts import TEXTS
from games.i18n import current_language
register = template.Library()

@register.inclusion_tag('games/_reward_progress.html', takes_context=True)
def reward_progress(context):
    request = context['request']
    if not request.user.is_authenticated:
        return {}
    return dict(reward=summary(request.user), words=TEXTS[current_language(request)])

@register.simple_tag
def reward_words(language):
    return TEXTS.get(language, TEXTS["pt"])

@register.simple_tag
def review_reward(review):
    from games.rewards import review_reward_key
    from games.models import LearningReward
    if not review:
        return 0
    key = review_reward_key(review)
    return LearningReward.objects.filter(user=review.user, key=key).values_list('xp', flat=True).first() or 0 if key else 0
