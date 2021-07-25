import shutil

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User, Follow

INDEX_URL = reverse('index')
FOLLOW_INDEX_URL = reverse('follow_index')
INDEX_PAGE_2_URL = INDEX_URL + '?page=2'
NEW_POST_URL = reverse('new_post')
NAME_1 = 'test_user'
NAME_2 = 'user-2'
SLUG_1 = 'test-slug'
SLUG_2 = 'test-slug2'
GROUP_1_URL = reverse('group', kwargs={'slug': SLUG_1})
GROUP_2_URL = reverse('group', kwargs={'slug': SLUG_2})
PROFILE_1_URL = reverse('profile', kwargs={'username': NAME_1})
FOLLOW_2_URL = reverse('profile_follow', kwargs={'username': NAME_2})
UNFOLLOW_2_URL = reverse('profile_unfollow', kwargs={'username': NAME_2})


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=NAME_1)
        cls.user_2 = User.objects.create_user(username=NAME_2)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG_1,
            description='Текст')
        cls.group_2 = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG_2,
            description='Текст',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
            group=cls.group,
            image=uploaded,
        )
        cls.POST_1_URL = reverse('post', kwargs={
            'username': cls.post.author.username,
            'post_id': cls.post.id
        })
        cls.follow = Follow.objects.create(user=cls.user_2, author=cls.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client_2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2.force_login(self.user_2)
        self.URL_NAMES = {
            INDEX_URL: self.authorized_client,
            GROUP_1_URL: self.authorized_client,
            PROFILE_1_URL: self.authorized_client,
            self.POST_1_URL: self.authorized_client,
            FOLLOW_INDEX_URL: self.authorized_client_2,
        }
        self.URL_CONTEXT = [
            (PROFILE_1_URL, self.user, 'author'),
            (GROUP_1_URL, self.group, 'group'),
            (self.POST_1_URL, self.user, 'author'),
        ]

    def test_templates_with_post_show_correct_context(self):
        """Страницы с post сформированы с правильным контекстом."""
        for url, client in self.URL_NAMES.items():
            with self.subTest(url):
                response = client.get(url)
                if 'post' in response.context:
                    post = response.context['post']
                else:
                    self.assertEqual(len(response.context['page']), 1)
                    post = response.context.get('page')[0]
                self.assertEqual(post, self.post)

    def test_pages_show_correct_context(self):
        """Страницы сформирован с правильным контекстом."""
        for url, result, context in self.URL_CONTEXT:
            response = self.authorized_client.get(url)
            self.assertEqual(response.context[context], result)

    def test_post_with_group_not_appears_on_page(self):
        """Пост с группой не попал в группу, для которой
        не был предназначен.."""
        response = self.authorized_client.get(GROUP_2_URL)
        self.assertEqual(len(response.context['page']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username=NAME_1)
        Post.objects.bulk_create(
            list(map(lambda x: Post(author=user, text='Text'), range(13)))
        )

    def setUp(self):
        self.client = Client()

    def test_first_page_containse_ten_records(self):
        response = self.client.get(INDEX_URL)
        self.assertEqual(len(response.context['page']), 10)

    def test_second_page_containse_three_records(self):
        response = self.client.get(INDEX_PAGE_2_URL)
        self.assertEqual(len(response.context['page']), 3)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=NAME_1)
        cls.user_2 = User.objects.create_user(username=NAME_2)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.follow = Follow.objects.create(user=self.user, author=self.user_2)
        self.new_post = Post.objects.create(
            author=self.user_2,
            text='Текст',
        )

    def test_user_follow_to_other_user(self):
        """Авторизованный пользователь может подписываться на других
        пользователей"""
        Follow.objects.all().delete()
        self.authorized_client.get(FOLLOW_2_URL)
        self.assertEqual(Follow.objects.filter(
            user=self.user, author=self.user_2).exists(), True)

    def test_user_unfollow_to_other_user(self):
        """Авторизованный пользователь может удалять
        пользователей из подписок"""
        self.authorized_client.get(UNFOLLOW_2_URL)
        self.assertEqual(
            Follow.objects.filter(
                user=self.user, author=self.user_2).exists(), False)

    def test_new_post_not_appears_on_page_who_not_follow_user(self):
        """Новая запись пользователя не появляется
        в ленте тех, кто не подписан на него"""
        self.authorized_client.force_login(self.user_2)
        response = self.authorized_client.get(FOLLOW_INDEX_URL)
        self.assertNotIn(self.new_post, response.context['page'])
