from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User

INDEX_URL = reverse('index')
INDEX_PAGE2_URL = INDEX_URL + '?page=2'
NEW_POST_URL = reverse('new_post')
NAME = 'test_user'
SLUG = 'test-slug'
SLUG2 = 'test-slug2'
GROUP_URL = reverse('group', kwargs={'slug': SLUG})
GROUP2_URL = reverse('group', kwargs={'slug': SLUG2})
PROFILE_URL = reverse('profile', kwargs={'username': NAME})


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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.POST_URL = reverse('post', kwargs={
            'username': self.post.author.username,
            'post_id': self.post.id
        })

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
        user = User.objects.create_user(username='test_user')
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
