from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"
        ordering = ['title']


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Напишите что-нибудь',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
        help_text='Выберите группу',
    )
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return (
            f'Автор: {self.author}, '
            f'Группа: {self.group}, '
            f'Дата: {self.pub_date.strftime("%d/%m/%Y")}, '
            f'Текст: {self.text[:15]}'
        )

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ('-pub_date', )


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост',
        related_name='comments',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='comments'
    )

    text = models.TextField(
        verbose_name='Текст',
        help_text='Напишите что-нибудь'
    )
    created = models.DateTimeField('Дата публикации', auto_now_add=True)

    def __str__(self):
        return (
            f'Автор: {self.author}, '
            f'Пост: {self.post.id}, '
            f'Текст: {self.text[:15]}'
        )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ('-created', )
