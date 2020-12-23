import shutil

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User, Follow

INDEX_URL = reverse('index')
INDEX_PAGE2_URL = INDEX_URL + '?page=2'
NEW_POST_URL = reverse('new_post')
NAME = 'test_user'
NAME2 = 'user2'
SLUG = 'test-slug'
SLUG2 = 'test-slug2'
GROUP_URL = reverse('group', kwargs={'slug': SLUG})
GROUP2_URL = reverse('group', kwargs={'slug': SLUG2})
PROFILE_URL = reverse('profile', kwargs={'username': NAME})
FOLLOW_URL = reverse('profile_follow', kwargs={'username': NAME2})
UNFOLLOW_URL = reverse('profile_unfollow', kwargs={'username': NAME2})
FOLLOW_INDEX_URL = reverse('follow_index')


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=NAME)
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG,
            description='Текст')
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок',
            slug=SLUG2,
            description='Текст')
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
        cls.POST_URL = reverse('post', kwargs={
            'username': cls.post.author.username,
            'post_id': cls.post.id
        })

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_page_show_correct_context(self):
        """Шаблоны с post сформированы с правильным контекстом."""
        url_names = (
            INDEX_URL,
            GROUP_URL,
            PROFILE_URL,
            self.POST_URL,
        )
        for url in url_names:
            with self.subTest(url):
                response = self.authorized_client.get(url)
                if 'post' in response.context:
                    post = response.context['post']
                else:
                    self.assertEqual(len(response.context['page']), 1)
                    post = response.context.get('page')[0]
                self.assertEqual(post, self.post)

    def test_group_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(GROUP_URL)
        self.assertEqual(response.context['group'], self.group)

    def test_post_with_group_not_appears_on_page(self):
        """Пост с группой не попал в группу, для которой
        не был предназначен.."""
        response = self.authorized_client.get(GROUP2_URL)
        self.assertEqual(len(response.context['page']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username=NAME)
        Post.objects.bulk_create(
            list(map(lambda x: Post(author=user, text='Text'), range(13)))
        )

    def setUp(self):
        self.client = Client()

    def test_first_page_containse_ten_records(self):
        response = self.client.get(INDEX_URL)
        self.assertEqual(len(response.context['page']), 10)

    def test_second_page_containse_three_records(self):
        response = self.client.get(INDEX_PAGE2_URL)
        self.assertEqual(len(response.context['page']), 3)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=NAME)
        cls.user2 = User.objects.create_user(username=NAME2)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2.force_login(self.user2)
        self.new_post = Post.objects.create(
            author=self.user2,
            text='Текст',
        )
        self.follow = Follow.objects.create(user=self.user, author=self.user2)

    def test_user_follow_to_other_user(self):
        """Авторизованный пользователь может подписываться на других
        пользователей"""
        Follow.objects.all().delete()
        self.authorized_client.get(FOLLOW_URL)
        follow = Follow.objects.all()[0]
        self.assertEqual(follow.user, self.user)
        self.assertEqual(follow.author, self.user2)

    def test_user_unfollow_to_other_user(self):
        """Авторизованный пользователь может удалять
        пользователей из подписок"""
        self.authorized_client.get(UNFOLLOW_URL)
        self.assertNotIn(self.follow, Follow.objects.filter(user=self.user))

    def test_new_post_appears_on_page_who_follow_user(self):
        """Новая запись пользователя появляется в ленте тех,
         кто на него подписан """
        response = self.authorized_client.get(FOLLOW_INDEX_URL)
        self.assertEqual(len(response.context['page']), 1)
        self.assertIn(self.new_post, response.context['page'])

    def test_new_post_not_appears_on_page_who_not_follow_user(self):
        """Новая запись пользователя появляется
        не появляется в ленте тех, кто не подписан на него"""
        response = self.authorized_client2.get(FOLLOW_INDEX_URL)
        self.assertNotIn(self.new_post, response.context['page'])
