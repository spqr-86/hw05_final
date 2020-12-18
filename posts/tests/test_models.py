from django.test import TestCase

from posts.models import Post, Group, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=user,
            group=cls.group,
        )

    def test_verbose_name(self):
        field_verbose_names = {
            'text': 'Текст',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verbose_names.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self):
        field_help_texts = {
            'text': 'Напишите что-нибудь',
            'group': 'Выберите группу',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).help_text, expected)

    def test_post_name_is_text_field(self):
        expected_object_name = (
            f'Автор: {self.post.author}, '
            f'Группа: {self.post.group}, '
            f'Дата: {self.post.pub_date.strftime("%d/%m/%Y")}, '
            f'Текст: {self.post.text[:15]}'
        )
        self.assertEquals(expected_object_name, str(self.post))

    def test_group_name_is_title_field(self):
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEquals(expected_object_name, str(group))
