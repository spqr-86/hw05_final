from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, User, Post, Follow

INDEX_URL = reverse('index')
FOLLOW_INDEX_URL = reverse('follow_index')
NEW_POST_URL = reverse('new_post')
NAME = 'test_user'
NAME_2 = 'user-2'
SLUG = 'test-slug'
GROUP_URL = reverse('group', kwargs={'slug': SLUG})
PROFILE_URL = reverse('profile', kwargs={'username': NAME})
LOGIN_URL_NEXT = reverse('login') + f'?next='
FOLLOW_URL = reverse('follow_index')
NOT_EXISTING_PAGE = 'not-exist/'


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        site = Site.objects.get(pk=1)
        self.about_author_flatpage = FlatPage.objects.create(
            url='/about-author/',
            title='About author',
            content='<b>content</b>',
        )
        self.about_spec_flatpage = FlatPage.objects.create(
            url='/about-spec/',
            title='About spec',
            content='<b>content</b>',
        )
        self.about_author_flatpage.sites.add(site)
        self.about_spec_flatpage.sites.add(site)
        self.static_pages = (self.about_author_flatpage.url,
                             self.about_spec_flatpage.url,)

    def test_static_pages_response(self):
        """Проверка доступности url"""
        for url in self.static_pages:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200, url)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=NAME)
        cls.user_2 = User.objects.create_user(username=NAME_2)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group,
        )
        cls.new_post = Post.objects.create(
            author=cls.user_2,
            text='Текст',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2.force_login(self.user_2)
        self.follow = Follow.objects.create(user=self.user, author=self.user_2)
        self.POST_URL = reverse('post', args=[
            self.post.author.username,
            self.post.id,
        ])
        self.POST_EDIT_URL = reverse('post_edit', args=[
            self.post.author.username,
            self.post.id,
        ])

        self.URLS = {
            INDEX_URL: {
                'availability_for_anonymous': True,
                'template_name': 'index.html',
            },
            GROUP_URL: {
                'availability_for_anonymous': True,
                'template_name': 'group.html',
            },
            PROFILE_URL: {
                'availability_for_anonymous': True,
                'template_name': 'profile.html',
            },
            self.POST_URL: {
                'availability_for_anonymous': True,
                'template_name': 'posts/post.html',
            },
            NEW_POST_URL: {
                'availability_for_anonymous': False,
                'template_name': 'posts/new_post.html'
            },
            self.POST_EDIT_URL: {
                'availability_for_anonymous': False,
                'redirect': self.POST_URL,
                'template_name': 'posts/new_post.html',
            },
            FOLLOW_URL: {
                'availability_for_anonymous': False,
                'template_name': 'follow.html',
            },
            NOT_EXISTING_PAGE: {
                'availability_for_anonymous': True,
                '404': True,
                'template_name': 'misc/404.html',
            },
        }

    def test_urls_exists_at_desired_location_anonymous(self):
        """Проверка ответа страниц"""
        for url, data in self.URLS.items():
            with self.subTest(url):
                response_for_guest_client = self.guest_client.get(url)
                response_for_authorized_client = self.authorized_client.get(url)
                if data['availability_for_anonymous'] is False:
                    self.assertEqual(
                        response_for_guest_client.status_code, 302)
                    self.assertEqual(
                        response_for_authorized_client.status_code, 200)
                    if 'redirect' in data:
                        response = self.authorized_client_2.get(url)
                        self.assertEqual(response.status_code, 302)
                else:
                    if '404' not in data:
                        self.assertEqual(
                            response_for_guest_client.status_code, 200)
                        self.assertEqual(
                            response_for_authorized_client.status_code, 200)
                    else:
                        self.assertEqual(
                            response_for_guest_client.status_code, 404)

    def test_urls_redirect(self):
        """Проверка перенаправления пользователя"""
        for url, data in self.URLS.items():
            with self.subTest(url):
                if data['availability_for_anonymous'] is False:
                    response = self.guest_client.get(url)
                    self.assertRedirects(response, LOGIN_URL_NEXT + url)
                else:
                    if 'redirect' in data:
                        response = self.authorized_client_2.get(url)
                        self.assertRedirects(response, data['redirect'])

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, data in self.URLS.items():
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, data['template_name'])

    def test_new_post_appears_on_page_who_follow_user(self):
        """Новая запись пользователя появляется в ленте тех,
         кто на него подписан """
        response = self.authorized_client.get(FOLLOW_INDEX_URL)
        self.assertEqual(len(response.context['page']), 1)
        self.assertIn(self.new_post, response.context['page'])

    def test_new_post_not_appears_on_page_who_not_follow_user(self):
        """Новая запись пользователя не появляется
        в ленте тех, кто не подписан на него"""
        response = self.authorized_client_2.get(FOLLOW_INDEX_URL)
        self.assertNotIn(self.new_post, response.context['page'])
