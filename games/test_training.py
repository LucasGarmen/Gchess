from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import UserPuzzleStats
from games.models import DailyPuzzle, DailyPuzzleAttempt, BlitzBestResult, StreakBestResult
from games.training import MODE_CONTENT, MODE_ROUTES


class TrainingHubTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='training-user')

    def daily_attempt(self, result):
        daily = DailyPuzzle.objects.create(date=timezone.localdate(), puzzle_id='preview')
        return DailyPuzzleAttempt.objects.create(user=self.user, daily_puzzle=daily, date=daily.date, resultado=result)

    def test_guest_can_choose_modes_without_creating_training_records(self):
        response = self.client.get(reverse('training'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('login')+'?next='+reverse('daily_puzzle'))
        self.assertContains(response, reverse('practice'))
        self.assertFalse(DailyPuzzleAttempt.objects.exists())
        self.assertFalse(UserPuzzleStats.objects.exists())

    def test_all_mode_names_and_rules_are_localized(self):
        for language, rows in MODE_CONTENT.items():
            session = self.client.session
            session['language'] = language
            session.save()
            response = self.client.get(reverse('training'))
            for row in rows:
                self.assertContains(response, row[0])
                self.assertContains(response, row[3])

    def test_fresh_member_gets_daily_recommendation_without_creating_attempt(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('training'))
        self.assertFalse(response.context['daily_completed'])
        self.assertFalse(response.context['daily_in_progress'])
        self.assertEqual(response.context['training_goal'], 1)
        self.assertFalse(DailyPuzzleAttempt.objects.exists())
        self.assertFalse(UserPuzzleStats.objects.exists())

    def test_pending_daily_attempt_can_be_continued(self):
        self.daily_attempt('in_progress')
        self.client.force_login(self.user)
        response = self.client.get(reverse('training'))
        self.assertTrue(response.context['daily_in_progress'])
        self.assertFalse(response.context['daily_completed'])

    def test_correct_and_incorrect_daily_results_both_complete_today(self):
        attempt = self.daily_attempt('correct')
        self.client.force_login(self.user)
        for result in ['correct', 'incorrect']:
            attempt.resultado = result
            attempt.save()
            response = self.client.get(reverse('training'))
            self.assertTrue(response.context['daily_completed'])
            self.assertFalse(response.context['daily_in_progress'])

    def test_personal_records_are_separate_and_do_not_leak_other_accounts(self):
        other = User.objects.create_user(username='other-training-user')
        BlitzBestResult.objects.create(user=self.user, score=31)
        StreakBestResult.objects.create(user=self.user, mejor_racha=7)
        BlitzBestResult.objects.create(user=other, score=999)
        StreakBestResult.objects.create(user=other, mejor_racha=99)
        self.client.force_login(self.user)
        response = self.client.get(reverse('training'))
        self.assertEqual(response.context['training_blitz'].score, 31)
        self.assertEqual(response.context['training_streak'].mejor_racha, 7)

    def test_next_goal_advances_and_has_no_unreachable_extra_milestone(self):
        stats = UserPuzzleStats.objects.create(user=self.user, puzzles_correctos=10)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('training')).context['training_goal'], 50)
        stats.puzzles_correctos = 1000
        stats.save()
        self.assertIsNone(self.client.get(reverse('training')).context['training_goal'])

    def test_existing_mode_pages_keep_controls_and_show_matching_guide(self):
        self.client.force_login(self.user)
        for route in MODE_ROUTES:
            response = self.client.get(reverse(route))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['active_training_mode']['route'], route)
            self.assertContains(response, reverse('training'))
            if route in ['blitz', 'streak']:
                self.assertContains(response, 'id="training-challenge-start"')
                self.assertContains(response, 'practice.min.js')
