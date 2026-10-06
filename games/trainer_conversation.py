"""Small, conservative routing rules; unknown topics belong to Gemini."""
import re

from .engine_analysis import normalize_piece_text, SAN_CANDIDATE_RE, UCI_CANDIDATE_RE


CHESS_WORDS = re.compile(r"\b(ajedrez|xadrez|chess|tablero|board|posicion|posicao|position|jugada|jogada|move|partida|peon|pawn|caballo|cavalo|knight|alfil|bispo|bishop|torre|rook|reina|dama|queen|jaque|xeque|check|mate|enroque|roque|castling|apertura|abertura|opening|blancas|negras|brancas|pretas|stockfish)\b")
FOLLOWUP = re.compile(r"^(y |e |and |pero |but |mas )?(por que|porque|why|como asi|how so|explica|explain|y ahora|and now|e agora)\b")
PAST = re.compile(r"\b(buena|bueno|boa|bom|good|mala|ruim|bad|joguei|jugue|played|ultima|last|anterior)\b")


def is_current_position_request(question):
    text = normalize_piece_text(question)
    return bool(re.search(r"\b(ahora|agora|now|que hago|que hacer|que faco|what should i do)\b", text) or re.search(r"\bahi\b.*\b(hago|juego)\b", text))


def is_followup(question):
    if is_current_position_request(question):
        return False
    return bool(FOLLOWUP.search(normalize_piece_text(question).strip(" ?!")))


def question_topic(question, history):
    text = normalize_piece_text(question)
    notation = SAN_CANDIDATE_RE.search(question) or UCI_CANDIDATE_RE.search(question)
    conceptual = re.search(r"^(que es|que son|o que e|what is|what are|como se|how does)\b", text)
    board_reference = re.search(r"\b(partida|tablero|board|posicion|posicao|position|esta|this|minha|mi)\b", text)
    if conceptual and not notation and not board_reference:
        return "general"
    if CHESS_WORDS.search(text) or notation:
        return "chess"
    if re.search(r"\b(espacio|space|estrellas|stars|nasa|universo|universe)\b", text):
        return "general"
    if is_current_position_request(question) or (PAST.search(text) and re.search(r"\b(esa|ese|esta|esto|that|this|essa|isso)\b", text)):
        return "chess"
    if is_followup(question):
        for index in range(len(history) - 1, -1, -1):
            if history[index]["role"] == "user":
                return question_topic(history[index]["text"], history[:index])
    return "general"


def analysis_question(question, history):
    if is_current_position_request(question):
        return "best move in the current position"
    if is_followup(question):
        for entry in reversed(history):
            if entry["role"] == "user" and not is_followup(entry["text"]):
                return entry["text"]
    return question


def useful_engine_fallback(context, question, language):
    """Engine facts stay separate from the missing conversational answer."""
    if context.get("played_move_unavailable"):
        return None
    played = context.get("played_move") or context.get("proposed_move")
    if played:
        if not played.get("legal", True):
            return {"es": "La jugada propuesta no es legal en esa posicion.", "pt": "A jogada proposta nao e legal nessa posicao.", "en": "The proposed move is illegal in that position."}[language]
        move = played["move_san"]
        loss = max(0, -played["change_for_mover_cp"])
        if abs(played["after_score_cp_white"]) >= 90000:
            return {"es": f"{move}: el motor indica una secuencia de mate; no es una evaluacion en peones.", "pt": f"{move}: o motor indica uma sequencia de mate, nao uma avaliacao em peoes.", "en": f"{move}: the engine indicates a mate sequence, not a pawn evaluation."}[language]
        return {
            "es": f"{move}: perdida estimada frente a la mejor alternativa: {loss / 100:.2f} peones. Respuesta calculada: {played.get('engine_reply_san') or 'sin continuacion'}. No es una explicacion conversacional.",
            "pt": f"{move}: perda estimada diante da melhor alternativa: {loss / 100:.2f} peoes. Resposta calculada: {played.get('engine_reply_san') or 'sem continuacao'}. Nao e uma explicacao conversacional.",
            "en": f"{move}: estimated loss against the best alternative: {loss / 100:.2f} pawns. Calculated reply: {played.get('engine_reply_san') or 'no continuation'}. This is not a conversational explanation.",
        }[language]
    if re.search(r"\b(best|mejor|melhor|recomenda|recommend|evaluation|evaluacion|avaliacao)\b", normalize_piece_text(question)):
        from .views import trainer_context_fallback
        return trainer_context_fallback(context, language)
    return None
