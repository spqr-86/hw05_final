from posts.models import Group


def groups(request):
    return {'group_list': Group.objects.all()}
