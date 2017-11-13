from django.conf.urls import url

from . import views

app_name = 'vkapp'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    url(r'^home/$', views.home, name='home'),
    url(r'^findcommonfriends/$', views.find_common_friends, name='findcommonfriends'),
    url(r'^friendspath/$', views.find_friend_path, name='friendspath'),
    url(r'^friendsgraph/$', views.friends_graph, name='friendsgraph'),
    url(r'^scheduledcomments/$', views.view_scheduled_comments, name='scheduledcomments'),
    url(r'^deletecomment/$', views.delete_comment, name='deletecomment'),
]
