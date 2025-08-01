from .models import Profile


def profile_pic(request):
    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        return {'profile_pic': profile.image}
    return {}
