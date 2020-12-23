from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, User, Post

INDEX_URL = reverse('index')
NEW_POST_URL = reverse('new_post')
NAME = 'test_user'
SLUG = 'test-slug'
GROUP_URL = reverse('group', kwargs={'slug': SLUG})
PROFILE_URL = reverse('profile', kwargs={'username': NAME})
LOGIN_URL_NEXT = reverse('login') + f'?next='


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
        cls.user2 = User.objects.create_user(username='test_user2')
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
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        self.POST_URL = reverse('post', args=[
            self.post.author.username,
            self.post.id,
        ])
        self.POST_EDIT_URL = reverse('post_edit', args=[
            self.post.author.username,
            self.post.id,
        ])
        self.urls_anonymous = (
            INDEX_URL,
            GROUP_URL,
            PROFILE_URL,
            self.POST_URL,
        )
        self.urls_authorized = (
            NEW_POST_URL,
            self.POST_EDIT_URL,
        )

    def test_urls_exists_at_desired_location_anonymous(self):
        """Проверка доступности страниц"""
        for url in (self.urls_anonymous + self.urls_authorized):
            with self.subTest(url):
                if url in self.urls_anonymous:
                    response = self.guest_client.get(url)
                else:
                    response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_urls_redirect(self):
        """Проверка перенаправления пользователя"""
        for url in self.urls_authorized:
            with self.subTest(url):
                response_guest_client = self.guest_client.get(url)
                response_authorized_client = self.authorized_client2.get(
                    self.POST_EDIT_URL)
                self.assertRedirects(
                    response_guest_client, LOGIN_URL_NEXT + url
                )
                if url == self.POST_EDIT_URL:
                    self.assertRedirects(
                        response_authorized_client, self.POST_URL
                    )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            INDEX_URL: 'index.html',
            GROUP_URL: 'group.html',
            PROFILE_URL: 'profile.html',
            self.POST_URL: 'posts/post.html',
            NEW_POST_URL: 'posts/new_post.html',
            self.POST_EDIT_URL: 'posts/new_post.html',
        }
        for reverse_name, template in templates_url_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
