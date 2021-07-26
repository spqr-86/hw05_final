import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

INDEX_URL = reverse('index')
NEW_POST_URL = reverse('new_post')
LOGIN_URL_NEXT_NEW_POST = (reverse('login') + f'?next={NEW_POST_URL}')


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Группа1',
            slug='test-slug',
            description='Текст',
        )
        cls.new_group = Group.objects.create(
            title='Группа2',
            slug='new-slug',
            description='Текст',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif',
        )
        self.post = Post.objects.create(
            text='Пост1',
            author=self.user,
            group=self.group,
            image=self.uploaded,
        )
        self.POST_URL = reverse('post', args=[
            self.post.author.username,
            self.post.id,
        ])
        self.POST_EDIT_URL = reverse('post_edit', args=[
            self.post.author.username,
            self.post.id,
        ])
        self.LOGIN_URL_NEXT_POST_EDIT = (
            reverse('login') + f'?next={self.POST_EDIT_URL}'
        )
        self.ADD_COMMENT_URL = reverse('add_comment', args=[
            self.user.username,
            self.post.id,
        ])
        self.LOGIN_URL_NEXT_ADD_COMMENT = (
            reverse('login') + f'?next={self.ADD_COMMENT_URL}'
        )

    def test_create_new_post(self):
        """Валидная форма создает Post."""
        Post.objects.all().delete()
        post_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True,
        )
        post = response.context['page'][0]
        self.assertRedirects(response, INDEX_URL)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)
        self.assertEqual(bool(post.image), True)

    def test_edit_post(self):
        """Валидная форма редактирует Post."""
        form_data = {
            'text': 'Измененный текст',
            'group': self.new_group.id,
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.post.refresh_from_db()
        self.assertRedirects(response, self.POST_URL)
        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group.id, form_data['group'])

    def test_anonymous_create_new_post(self):
        """Анонимный пользавотель не может создать пост"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост',
            'group': self.group.id,
        }
        response = self.guest_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, LOGIN_URL_NEXT_NEW_POST
        )
        self.assertEqual(Post.objects.count(), post_count)

    def test_anonymous_edit_post(self):
        """Анонимный пользавотель не может редактировать пост"""
        form_data = {
            'text': 'Измененный текст',
            'group': self.new_group.id,
        }
        response = self.guest_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, self.LOGIN_URL_NEXT_POST_EDIT
        )
        edit_post = Post.objects.get(id=self.post.id)
        self.assertEqual(self.post, edit_post)

    def test_new_post_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(NEW_POST_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(self.POST_EDIT_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_add_comment(self):
        """Авторизированный пользователь может комментировать пост"""
        new_user = User.objects.create_user(username='new_user')
        new_authorized_client = Client()
        new_authorized_client.force_login(new_user)
        Comment.objects.all().delete()
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = new_authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True,
        )
        self.assertEqual(len(response.context['post'].comments.all()), 1)
        comment = response.context['post'].comments.all()[0]
        self.assertRedirects(response, self.POST_URL)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, new_user)

    def test_anonymous_add_comment(self):
        """Анонимный пользавотель не может комментировать пост"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.guest_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, self.LOGIN_URL_NEXT_ADD_COMMENT
        )
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_index_cache(self):
        """проверка работы кэша """
        response = self.authorized_client.get(INDEX_URL)
        content = response.content
        response = self.authorized_client.get(INDEX_URL)
        Post.objects.all().delete()
        self.assertEqual(content, response.content)
        cache.clear()
        response = self.authorized_client.get(INDEX_URL)
        self.assertNotEqual(content, response.content)
