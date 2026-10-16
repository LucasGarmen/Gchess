import json
from unittest.mock import patch
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase, RequestFactory, SimpleTestCase, override_settings
from .i18n import current_language
from .models import UserFeedback
from .launch_texts import TEXTS


class BrowserLanguageTests(SimpleTestCase):
    def language(self, header, saved=None):
        request=RequestFactory().get('/', HTTP_ACCEPT_LANGUAGE=header)
        request.session={} if saved is None else {'language':saved}
        return current_language(request)

    def test_browser_regions_weights_and_saved_choice(self):
        self.assertEqual(self.language('es-AR,pt;q=0.8,en;q=0.7'),'es')
        self.assertEqual(self.language('pt-BR,en;q=0.9'),'pt')
        self.assertEqual(self.language('fr,en-US;q=0.8,es;q=0.4'),'en')
        self.assertEqual(self.language('es;q=0,en;q=0.8'),'en')
        self.assertEqual(self.language('es-AR','pt'),'pt')
        self.assertEqual(self.language('de'),'pt')

    def test_copy_has_matching_keys(self):
        for words in TEXTS.values():
            self.assertEqual(set(words),set(TEXTS['en']))
            self.assertEqual(len(words['demo_lines']),4)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", FEEDBACK_EMAIL="gchesssuport@gmail.com")
class LaunchFeedbackTests(TestCase):
    def setUp(self):
        cache.clear()

    def post(self, payload):
        return self.client.post('/feedback/',json.dumps(payload),content_type='application/json')

    def test_guest_feedback_is_saved_and_support_is_notified(self):
        response=self.post({'message':'The board is easy to use','category':'idea','page':'/games/1/?token=private#chat'})
        self.assertEqual(response.status_code,200)
        item=UserFeedback.objects.get()
        self.assertEqual(item.page,'/games/')
        self.assertEqual(item.category,'idea')
        self.assertEqual(len(mail.outbox),1)
        self.assertEqual(mail.outbox[0].to,['gchesssuport@gmail.com'])
        self.assertIn(item.message,mail.outbox[0].body)
        self.assertNotIn('token=private',mail.outbox[0].body)
        self.assertEqual(self.post({'message':'Another message','category':'bug'}).status_code,429)
        self.assertEqual(UserFeedback.objects.count(),1)
        self.assertEqual(len(mail.outbox),1)

    def test_smtp_failure_keeps_report_and_success_response(self):
        with patch('games.feedback.send_mail', side_effect=OSError('SMTP unavailable')):
            with self.assertLogs('games.feedback', level='WARNING') as logs:
                response=self.post({'message':'Chat does not open on my phone','category':'bug'})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json()['saved'])
        self.assertEqual(UserFeedback.objects.count(),1)
        self.assertNotIn('Chat does not open',str(logs.output))

    def test_bug_notification_uses_configured_recipient(self):
        with override_settings(FEEDBACK_EMAIL='support@example.com'):
            self.post({'message':'Board is not visible','category':'bug'})
        self.assertEqual(mail.outbox[0].to,['support@example.com'])
        self.assertIn('Error reportado',mail.outbox[0].subject)

    def test_invalid_payload_and_method_are_rejected(self):
        self.assertEqual(self.client.get('/feedback/').status_code,405)
        for payload in [[],{'message':'x','category':'idea'},{'message':'a'*2001,'category':'idea'},{'message':'Valid text','category':'other'}]:
            self.assertEqual(self.post(payload).status_code,400)
        self.assertFalse(UserFeedback.objects.exists())

    def test_csrf_is_required(self):
        response=Client(enforce_csrf_checks=True).post('/feedback/',json.dumps({'message':'Valid text','category':'idea'}),content_type='application/json')
        self.assertEqual(response.status_code,403)
        self.assertFalse(UserFeedback.objects.exists())

    def test_home_demo_feedback_and_no_account_copy_in_three_languages(self):
        for language in ['es','pt','en']:
            response=self.client.get('/',HTTP_ACCEPT_LANGUAGE=language)
            self.assertEqual(response.status_code,200)
            self.assertContains(response,TEXTS[language]['no_account'])
            self.assertContains(response,TEXTS[language]['feedback'])
            self.assertContains(response,'id="hero-demo-comment"')
            self.assertContains(response,'id="feedback-dialog"')
            self.assertContains(response,'id="home-open-bot"')
            self.assertContains(response,TEXTS[language]['hero_title'])
            self.assertContains(response,TEXTS[language]['hero_analyze'])
            self.assertContains(response,TEXTS[language]['garry_explains'])
            self.assertContains(response,TEXTS[language]['welcome_play'])
            self.assertContains(response,TEXTS[language]['welcome_message'])
            self.assertContains(response,TEXTS[language]['welcome_chat'])
            self.assertContains(response,'id="home-quick-start"')
            self.assertNotContains(response,'id="hero-demo-play"')
            self.assertContains(response,'class="home-explore"')
            self.assertContains(response,'data-entry-level="800"')
            self.assertContains(response,'class="entry-exact-level"')
            self.assertContains(response,'href="/analyze/" class="home-analysis-button"')

    def test_footer_language_choice_overrides_browser_and_keeps_target(self):
        response=self.client.post('/language/',{'language':'en','next':'/training/'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(response.url,'/training/')
        page=self.client.get('/training/',HTTP_ACCEPT_LANGUAGE='es')
        self.assertContains(page,TEXTS['en']['footer_language'])
        self.assertContains(page,'id="footer-language-select"')
        self.assertContains(page,'id="feedback-floating"')
