"""Copy for the welcome demo and lightweight feedback flow."""
TEXTS = {
 'es': {'no_account':'Jugá ahora, sin crear una cuenta.', 'demo':'Demostración de Garry', 'pause':'Pausar demostración', 'resume':'Reanudar demostración', 'demo_lines':['Tomá el centro: e4 abre camino al alfil y a la dama.','Desarrollá tus piezas: el alfil apunta a f7.','Dama y alfil coordinan el ataque sobre f7.','¡Jaque mate! La dama está protegida por el alfil.'], 'feedback':'Sugerir idea o reportar error', 'kind':'¿Qué querés contarnos?', 'idea':'Una idea', 'bug':'Un problema', 'message':'Tu mensaje', 'hint':'Contanos qué pasó o qué mejorarías. No incluyas contraseñas ni datos privados.', 'send':'Enviar comentario', 'cancel':'Cerrar', 'sending':'Enviando…', 'thanks':'Gracias. Tu comentario quedó guardado.', 'error':'No se pudo enviar. Tu mensaje sigue acá; intentá de nuevo.', 'thinking':'Garry está preparando tu respuesta…', 'engine':'El motor está calculando la jugada…'},
 'pt': {'no_account':'Jogue agora, sem criar uma conta.', 'demo':'Demonstração de Garry', 'pause':'Pausar demonstração', 'resume':'Retomar demonstração', 'demo_lines':['Ocupe o centro: e4 abre caminho para o bispo e a dama.','Desenvolva suas peças: o bispo aponta para f7.','Dama e bispo coordenam o ataque em f7.','Xeque-mate! A dama está protegida pelo bispo.'], 'feedback':'Sugerir ideia ou relatar erro', 'kind':'O que você quer nos contar?', 'idea':'Uma ideia', 'bug':'Um problema', 'message':'Sua mensagem', 'hint':'Conte o que aconteceu ou o que melhoraria. Não inclua senhas nem dados privados.', 'send':'Enviar comentário', 'cancel':'Fechar', 'sending':'Enviando…', 'thanks':'Obrigado. Seu comentário foi salvo.', 'error':'Não foi possível enviar. Sua mensagem continua aqui; tente novamente.', 'thinking':'Garry está preparando sua resposta…', 'engine':'O motor está calculando o lance…'},
 'en': {'no_account':'Play now. No account needed.', 'demo':'Demo with Garry', 'pause':'Pause demo', 'resume':'Resume demo', 'demo_lines':['Claim the centre: e4 opens lines for your bishop and queen.','Develop your pieces: the bishop targets f7.','Queen and bishop coordinate an attack on f7.','Checkmate! The bishop protects the queen.'], 'feedback':'Suggest an idea or report a bug', 'kind':'What would you like to share?', 'idea':'An idea', 'bug':'A problem', 'message':'Your message', 'hint':'Tell us what happened or what you would improve. Do not include passwords or private data.', 'send':'Send feedback', 'cancel':'Close', 'sending':'Sending…', 'thanks':'Thank you. Your feedback has been saved.', 'error':'Could not send. Your message is still here; please try again.', 'thinking':'Garry is preparing your reply…', 'engine':'The engine is calculating a move…'},
}

for language, message in {'es':'Esperá 30 segundos antes de enviar otro comentario.','pt':'Aguarde 30 segundos antes de enviar outro comentário.','en':'Please wait 30 seconds before sending another message.'}.items():
    TEXTS[language]['rate_limit'] = message

HERO = {
 'es': {'hero_title':'Entendé cada jugada. Mejorá con Garry.', 'hero_intro':'Jugá a tu nivel, preguntá por qué y aprendé con las explicaciones de Garry, tu coach con IA.', 'hero_play':'Jugar contra Garry', 'hero_analyze':'Probar análisis de partida', 'hero_badge':'Jugá gratis de inmediato · Sin crear cuenta', 'demo_name':'Mate Pastor', 'demo_coach':'Garry · Ejemplo de explicación'},
 'pt': {'hero_title':'Entenda cada lance. Evolua com Garry.', 'hero_intro':'Jogue no seu nível, pergunte o porquê e aprenda com as explicações de Garry, seu coach com IA.', 'hero_play':'Jogar contra Garry', 'hero_analyze':'Experimentar análise de partida', 'hero_badge':'Jogue grátis agora · Sem criar conta', 'demo_name':'Mate do Pastor', 'demo_coach':'Garry · Exemplo de explicação'},
 'en': {'hero_title':'Understand every move. Improve with Garry.', 'hero_intro':'Play at your level, ask why and learn with explanations from Garry.', 'hero_play':'Play against Garry', 'hero_analyze':'Try game analysis', 'hero_badge':'Play free right away · No account needed', 'demo_name':"Scholar’s Mate", 'demo_coach':'Garry · Example explanation'},
}
for language, words in HERO.items():
    TEXTS[language].update(words)

FINISH = {
 'es': {'feedback_short':'Feedback', 'footer_explore':'Explorá Gchess', 'footer_community':'Comunidad y contacto', 'footer_language':'Idioma de la página', 'footer_apply':'Aplicar', 'footer_note':'Jugá, entendé y seguí aprendiendo.'},
 'pt': {'feedback_short':'Feedback', 'footer_explore':'Explore o Gchess', 'footer_community':'Comunidade e contato', 'footer_language':'Idioma da página', 'footer_apply':'Aplicar', 'footer_note':'Jogue, entenda e continue aprendendo.'},
 'en': {'feedback_short':'Feedback', 'footer_explore':'Explore Gchess', 'footer_community':'Community and contact', 'footer_language':'Page language', 'footer_apply':'Apply', 'footer_note':'Play, understand and keep learning.'},
}
for language, words in FINISH.items():
    TEXTS[language].update(words)

for language, words in {
 'es': {'garry_explains':'Garry te explica:', 'demo_start':'Jugar contra Garry ahora (Gratis)'},
 'pt': {'garry_explains':'Garry explica:', 'demo_start':'Jogar contra Garry agora (Grátis)'},
 'en': {'garry_explains':'Garry explains:', 'demo_start':'Play against Garry now (Free)'},
}.items():
    TEXTS[language].update(words)
