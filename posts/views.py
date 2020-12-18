from django.views.generic import CreateView
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Post, Group, User
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {
        'page': page,
        'paginator': paginator,
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {
        'group': group,
        'page': page,
        'paginator': paginator,
    })


class PostView(LoginRequiredMixin, CreateView):
    form_class = PostForm
    success_url = reverse_lazy('index')
    template_name = 'posts/new_post.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'profile.html', {
        'author': author,
        'page': page,
        'paginator': paginator,
    })


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = Post.objects.get(pk=post_id, author=author)
    comments = post.comments.all()
    form = CommentForm()
    return render(request, 'posts/post.html', {
        'author': author,
        'post': post,
        'form': form,
        'comments': comments,
    })


@login_required()
def post_edit(request, username, post_id):
    if username != request.user.username:
        return redirect('post', username=username, post_id=post_id)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = PostForm(data=request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'posts/new_post.html', {
        'form': form,
        'post': post
    })


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required()
def add_comment(request, username, post_id):
    form = CommentForm(data=request.POST or None)
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if form.is_valid():
        form.instance.post = post
        form.instance.author = request.user
        form.save()
    return redirect('post', username=username, post_id=post_id)
