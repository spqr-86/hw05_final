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
NOT_EXISTING_URL = 'not-exist/'


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
        self.URLS_AND_RESPONSES = [
            (INDEX_URL, 200, self.guest_client),
            (GROUP_URL, 200, self.guest_client),
            (PROFILE_URL, 200, self.guest_client),
            (PROFILE_URL, 200, self.authorized_client_2),
            (self.POST_URL, 200, self.guest_client),
            (NEW_POST_URL, 200, self.authorized_client),
            (NEW_POST_URL, 302, self.guest_client),
            (self.POST_EDIT_URL, 200, self.authorized_client),
            (self.POST_EDIT_URL, 302, self.authorized_client_2),
            (self.POST_EDIT_URL, 302, self.guest_client),
            (FOLLOW_URL, 200, self.authorized_client),
            (NOT_EXISTING_URL, 404, self.guest_client)
        ]
        self.URLS_REDIRECT = [
            (NEW_POST_URL, LOGIN_URL_NEXT + NEW_POST_URL, self.guest_client),
            (FOLLOW_URL, LOGIN_URL_NEXT + FOLLOW_URL, self.guest_client),
            (self.POST_EDIT_URL, LOGIN_URL_NEXT +
             self.POST_EDIT_URL, self.guest_client),
            (self.POST_EDIT_URL, self.POST_URL, self.authorized_client_2),
        ]

    def test_urls_response(self):
        """Проверка ответа страниц"""
        for url, code, client in self.URLS_AND_RESPONSES:
            with self.subTest(url):
                response = client.get(url)
                self.assertEqual(response.status_code, code)

    def test_urls_redirect(self):
        """Проверка перенаправления пользователя"""
        for url, redirect, client in self.URLS_REDIRECT:
            with self.subTest(url):
                response = client.get(url)
                self.assertRedirects(response, redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            INDEX_URL: 'index.html',
            GROUP_URL: 'group.html',
            PROFILE_URL: 'profile.html',
            self.POST_URL: 'posts/post.html',
            NEW_POST_URL: 'posts/new_post.html',
            self.POST_EDIT_URL: 'posts/new_post.html',
            FOLLOW_URL: 'follow.html',
            NOT_EXISTING_URL: 'misc/404.html',
        }
        for url in templates_url_names:
            with self.subTest(url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response, templates_url_names[url])
