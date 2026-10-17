from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class UserManagementFrontendTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='test-password',
            role='ADMIN',
        )
        self.managed_user = User.objects.create_user(
            username='teacher-user',
            email='teacher@example.com',
            password='test-password',
            role='PARENT',
        )
        self.client.force_login(self.admin)

    def test_user_list_and_role_form_render(self):
        response = self.client.get(reverse('accounts:user_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.managed_user.username)
        self.assertContains(response, reverse(
            'accounts:user_role_update',
            args=[self.managed_user.pk],
        ))

        response = self.client.get(reverse(
            'accounts:user_role_update',
            args=[self.managed_user.pk],
        ))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Save role')

    def test_role_update_and_user_delete_from_list_actions(self):
        response = self.client.post(
            reverse('accounts:user_role_update', args=[self.managed_user.pk]),
            {'role': 'TEACHER'},
        )
        self.assertRedirects(response, reverse('accounts:user_list'))
        self.managed_user.refresh_from_db()
        self.assertEqual(self.managed_user.role, 'TEACHER')

        response = self.client.post(
            reverse('accounts:user_delete', args=[self.managed_user.pk]),
        )
        self.assertRedirects(response, reverse('accounts:user_list'))
        self.assertFalse(User.objects.filter(pk=self.managed_user.pk).exists())

    def test_user_list_template_prevents_self_role_and_delete_actions(self):
        response = self.client.get(reverse('accounts:user_list'))

        self.assertContains(response, 'Current account')
        self.assertNotContains(
            response,
            reverse('accounts:user_delete', args=[self.admin.pk]),
        )
