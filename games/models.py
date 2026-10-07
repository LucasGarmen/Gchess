import uuid
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User

class ChessGame(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('finished', 'Finalizada'),
        ('analyzing', 'Em análise'),
    ]

    RESULT_CHOICES = [
        ('white', 'Vitória das brancas'),
        ('black', 'Vitória das pretas'),
        ('draw', 'Empate'),
        ('unknown', 'Desconhecido'),
    ]
    
    CATEGORY_CHOICES = [
    ('casual', 'Casual'),
    ('ranked', 'Ranqueada'),
    ('training', 'Treino'),
]


    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    white_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='white_games')
    black_user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='black_games')
    white_guest_id = models.CharField(max_length=40, blank=True)
    black_guest_id = models.CharField(max_length=40, blank=True)
    title = models.CharField(max_length=100, blank=True)
    white_player = models.CharField(max_length=100)
    black_player = models.CharField(max_length=100)
    pgn = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='unknown')
    is_rated = models.BooleanField(default=False)
    rating_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='casual')
    time_control_minutes = models.PositiveIntegerField(blank=True, null=True)
    white_time_seconds = models.PositiveIntegerField(blank=True, null=True)
    black_time_seconds = models.PositiveIntegerField(blank=True, null=True)
    active_clock_color = models.CharField(max_length=10, blank=True)
    clock_started_at = models.DateTimeField(blank=True, null=True)
    draw_offer_by_color = models.CharField(max_length=10, blank=True)

    def __str__(self):
        white = self.white_player or 'Sin asignar'
        black = self.black_player or 'Sin asignar'
        created = self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else 'Sin fecha'

        return f"Blancas: {white} vs Negras: {black} - Creada: {created}"

    class Meta:
        indexes = [
            models.Index(fields=['owner', '-created_at'], name='game_owner_created_idx'),
            models.Index(fields=['white_user', '-created_at'], name='game_white_user_idx'),
            models.Index(fields=['black_user', '-created_at'], name='game_black_user_idx'),
            models.Index(fields=['white_guest_id', '-created_at'], name='game_white_guest_idx'),
            models.Index(fields=['black_guest_id', '-created_at'], name='game_black_guest_idx'),
            models.Index(fields=['status', '-created_at'], name='game_status_created_idx'),
        ]
    
class Move(models.Model):
    game = models.ForeignKey(ChessGame, on_delete=models.CASCADE, related_name='moves')
    move_number = models.PositiveIntegerField()
    from_square = models.CharField(max_length=2)
    to_square = models.CharField(max_length=2)
    piece_type = models.CharField(max_length=20)
    piece_color = models.CharField(max_length=10)
    promotion = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.move_number}. {self.from_square} -> {self.to_square}"

    class Meta:
        indexes = [
            models.Index(fields=['game', 'move_number', 'id'], name='move_game_order_idx'),
        ]


class UserPresence(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='presence')
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} online"


class DailyVisit(models.Model):
    date = models.DateField(unique=True)
    visits = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'visita diaria'
        verbose_name_plural = 'visitas diarias'

    def __str__(self):
        return f"{self.date}: {self.visits} visitas"


class DailyPuzzle(models.Model):
    date = models.DateField(unique=True)
    puzzle_id = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'puzzle diario'
        verbose_name_plural = 'puzzles diarios'

    def __str__(self):
        return f"{self.date}: {self.puzzle_id}"


class DailyPuzzleAttempt(models.Model):
    RESULT_CHOICES = [
        ('in_progress', 'En progreso'),
        ('correct', 'Correcto'),
        ('incorrect', 'Incorrecto'),
    ]

    daily_puzzle = models.ForeignKey(DailyPuzzle, on_delete=models.CASCADE, related_name='attempts')
    date = models.DateField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_puzzle_attempts')
    resultado = models.CharField(max_length=20, choices=RESULT_CHOICES, default='in_progress')
    tiempo = models.DurationField(default=timedelta)
    played_line = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-started_at']
        unique_together = [('date', 'user')]
        verbose_name = 'intento de puzzle diario'
        verbose_name_plural = 'intentos de puzzle diario'

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.resultado}"


class BlitzBestResult(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='blitz_best_result')
    score = models.PositiveIntegerField(default=0)
    puzzles_resueltos = models.PositiveIntegerField(default=0)
    puzzles_correctos = models.PositiveIntegerField(default=0)
    puzzles_incorrectos = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=180)
    achieved_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score', '-puzzles_correctos', 'achieved_at']
        verbose_name = 'mejor resultado blitz'
        verbose_name_plural = 'mejores resultados blitz'

    def __str__(self):
        return f"{self.user.username} - {self.score} pts"


class StreakBestResult(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak_best_result')
    mejor_racha = models.PositiveIntegerField(default=0)
    puzzles_resueltos = models.PositiveIntegerField(default=0)
    achieved_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-mejor_racha', '-puzzles_resueltos', 'achieved_at']
        verbose_name = 'mejor racha streak'
        verbose_name_plural = 'mejores rachas streak'

    def __str__(self):
        return f"{self.user.username} - {self.mejor_racha}"


class GameInvitation(models.Model):
    OPPONENT_CHOICES = [
        ('direct', 'Oponente escolhido'),
        ('link', 'Convite por link'),
        ('random', 'Oponente aleatório'),
    ]

    COLOR_CHOICES = [
        ('white', 'Brancas'),
        ('black', 'Pretas'),
        ('random', 'Aleatório'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('accepted', 'Aceita'),
        ('rejected', 'Recusada'),
        ('cancelled', 'Cancelada'),
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='sent_game_invitations')
    creator_guest_id = models.CharField(max_length=40, blank=True)
    creator_guest_name = models.CharField(max_length=100, blank=True)
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='received_game_invitations')
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    opponent_mode = models.CharField(max_length=20, choices=OPPONENT_CHOICES)
    creator_color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    is_rated = models.BooleanField(default=False)
    time_control_minutes = models.PositiveIntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rematch_of = models.ForeignKey(ChessGame, on_delete=models.SET_NULL, null=True, blank=True, related_name='rematch_invitations')
    game = models.ForeignKey(ChessGame, on_delete=models.SET_NULL, blank=True, null=True, related_name='invitations')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        creator = self.creator.username if self.creator_id else (self.creator_guest_name or 'Invitado')
        return f"Convite de {creator}"

    class Meta:
        indexes = [
            models.Index(fields=['status', 'opponent', 'created_at'], name='invite_status_opp_idx'),
            models.Index(fields=['status', 'opponent_mode', 'created_at'], name='invite_status_mode_idx'),
            models.Index(fields=['creator', 'status'], name='invite_creator_status_idx'),
            models.Index(fields=['token', 'opponent_mode'], name='invite_token_mode_idx'),
        ]


class GameChatMessage(models.Model):
    game = models.ForeignKey(ChessGame, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='sent_game_chat_messages')
    sender_guest_id = models.CharField(max_length=40, blank=True)
    sender_guest_name = models.CharField(max_length=100, blank=True)
    text = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [
            models.Index(fields=['game', 'created_at', 'id'], name='chat_game_order_idx'),
            models.Index(fields=['game', 'sender', 'id'], name='chat_game_sender_idx'),
            models.Index(fields=['game', 'sender_guest_id', 'id'], name='chat_game_guest_idx'),
        ]

    def __str__(self):
        sender = self.sender.username if self.sender_id else (self.sender_guest_name or 'Invitado')
        return f"{sender}: {self.text[:40]}"


class GameChatRead(models.Model):
    game = models.ForeignKey(ChessGame, on_delete=models.CASCADE, related_name='chat_reads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_chat_reads')
    last_read_message = models.ForeignKey(GameChatMessage, on_delete=models.SET_NULL, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('game', 'user')]

    def __str__(self):
        return f"{self.user.username} leu chat da partida {self.game_id}"


class Friendship(models.Model):
    """One canonical pair; only the recipient may accept a pending request."""
    low_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_low')
    high_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_high')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_sent')
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('accepted', 'Accepted')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['low_user', 'high_user'], name='friendship_unique_pair'),
            models.CheckConstraint(condition=models.Q(low_user__lt=models.F('high_user')), name='friendship_ordered_pair'),
            models.CheckConstraint(condition=models.Q(requester=models.F('low_user')) | models.Q(requester=models.F('high_user')), name='friendship_requester_member'),
        ]


class GameReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_reviews')
    game = models.ForeignKey(ChessGame, on_delete=models.CASCADE, null=True, blank=True, related_name='reviews')
    fingerprint = models.CharField(max_length=64)
    language = models.CharField(max_length=2)
    player_color = models.CharField(max_length=5, choices=[('white', 'White'), ('black', 'Black')])
    goal_completed_at = models.DateTimeField(null=True, blank=True)
    pgn = models.TextField()
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'fingerprint', 'language', 'player_color'], name='review_unique_user_position')]
        indexes = [models.Index(fields=['user', '-created_at'], name='review_user_created_idx')]


class Tournament(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_tournaments')
    name = models.CharField(max_length=80)
    status = models.CharField(max_length=12, choices=[('lobby', 'Lobby'), ('active', 'Active'), ('finished', 'Finished'), ('cancelled', 'Cancelled')], default='lobby')
    visibility = models.CharField(max_length=7, choices=[('private','Private'),('public','Public')], default='private', db_index=True)
    password_hash = models.CharField(max_length=128, blank=True, editable=False)
    max_players = models.PositiveSmallIntegerField(default=8)
    time_control_minutes = models.PositiveSmallIntegerField(default=10)
    current_round = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [models.CheckConstraint(condition=models.Q(max_players__gte=2, max_players__lte=16), name='tournament_capacity_range'), models.CheckConstraint(condition=models.Q(time_control_minutes__in=[3,5,10,15,30]), name='tournament_valid_time')]


class TournamentEntry(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='entries')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='tournament_entries')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['joined_at', 'pk']
        constraints = [models.UniqueConstraint(fields=['tournament', 'user'], name='unique_tournament_player')]


class TournamentMatch(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    round_number = models.PositiveSmallIntegerField()
    board_number = models.PositiveSmallIntegerField()
    white = models.ForeignKey(User, on_delete=models.PROTECT, related_name='white_tournament_matches')
    black = models.ForeignKey(User, on_delete=models.PROTECT, related_name='black_tournament_matches', null=True, blank=True)
    game = models.OneToOneField(ChessGame, on_delete=models.PROTECT, related_name='tournament_match', null=True, blank=True)

    class Meta:
        ordering = ['round_number', 'board_number']
        constraints = [models.UniqueConstraint(fields=['tournament', 'round_number', 'board_number'], name='unique_tournament_board'), models.CheckConstraint(condition=~models.Q(white=models.F('black')), name='tournament_distinct_players')]


class TournamentNotice(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='notices')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tournament_notices')
    kind = models.CharField(max_length=12, choices=[('invite','Invite'),('round','Round')])
    round_number = models.PositiveSmallIntegerField(default=0)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['tournament','user','kind','round_number'], name='unique_tournament_notice')]
        indexes = [models.Index(fields=['user','read'], name='tournament_notice_user_idx')]


class DailyTraining(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_training_sessions')
    date = models.DateField()
    tasks = models.JSONField(default=list)
    progress = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user','date'], name='unique_daily_training_user_date')]
