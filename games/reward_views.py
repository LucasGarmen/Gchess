from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache
from django.db.models import Q
from .models import ChessGame, LearningReward
from .rewards import summary

@login_required
@require_GET
@never_cache
def progress(request):
    data = summary(request.user)
    game_id = request.GET.get('game')
    if game_id:
        try:
            game_id = int(game_id)
        except (TypeError, ValueError):
            return JsonResponse({'error':'invalid_game'}, status=400)
        game = get_object_or_404(ChessGame.objects.filter(Q(white_user=request.user)|Q(black_user=request.user)), pk=game_id)
        earned = LearningReward.objects.filter(user=request.user,key='game:'+str(game.pk)).values_list('xp',flat=True).first()
        eligible = bool(game.white_user_id and game.black_user_id and game.white_user_id != game.black_user_id and game.moves.count() >= 12)
        data['pending'] = game.status != 'finished' or (eligible and earned is None)
        data['earned'] = earned or 0
    return JsonResponse(data)
