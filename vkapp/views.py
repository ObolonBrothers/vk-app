from django.http import HttpResponseRedirect
from django.shortcuts import render
from . import vkapi
from datetime import datetime, timedelta
from threading import Thread, Event


def index(request):
    if 'access_token' in request.session:
        access_token = request.session['access_token']
        token_expires = request.session['token_expire']
        user_id = request.session['user_id']
        if access_token is not None and token_expires is not None and user_id is not None:
            if datetime.now() < datetime.fromtimestamp(int(token_expires)):
                return HttpResponseRedirect("home")

    return HttpResponseRedirect("login")


def home(request):
    if 'token_expire' in request.session:
        if request.session['token_expire'] is None or datetime.now() > datetime.fromtimestamp(
                int(request.session['token_expire'])):
            return logout(request)

        user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
        return render(request, "vkapp/home.html", {'user': user})
    else:
        return logout(request)


def login(request):
    if request.method == 'POST':
        access_token, user_id, expires_in = vkapi.get_auth_params_by_url(request.POST['token_url'])
        if access_token is None or user_id is None or expires_in is None:
            return render(request, "vkapp/login.html",
                          {'APP_ID': vkapi.APP_ID, 'error_message': 'Login error, try again!'})

        request.session['access_token'] = access_token
        request.session['user_id'] = user_id
        if expires_in == "0":
            expires = datetime.now() + timedelta(minutes=43800) # one month
        else:
            expires = datetime.now() + timedelta(seconds=int(expires_in))
        request.session['token_expire'] = expires.timestamp()

        return HttpResponseRedirect("/")
    else:
        return render(request, "vkapp/login.html", {'APP_ID': vkapi.APP_ID})


def logout(request):
    request.session['access_token'] = None
    request.session['token_expire'] = None
    request.session['user_id'] = None
    return HttpResponseRedirect("/vk")


def find_common_friends(request):
    if request.method == 'POST':
        link1 = request.POST['user1']
        link2 = request.POST['user2']

        if link1 is None or link2 is None:
            user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
            return render(request, "vkapp/find_common_friends.html",
                          {'user': user, 'error_message': 'Wrong details, try again!'})

        link1 = link1.split('/')[-1]
        link2 = link2.split('/')[-1]

        if link1 == '' or link2 == '':
            user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
            return render(request, "vkapp/find_common_friends.html",
                          {'user': user, 'error_message': 'Wrong details, try again!'})

        users, common = vkapi.get_common_friends(request.session['access_token'], link1, link2)

        if users is None or common is None:
            user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
            return render(request, "vkapp/find_common_friends.html",
                          {'user': user, 'error_message': 'Wrong details, try again!'})

        return render(request, "vkapp/show_common_friends.html",
                      {'user1': users[0], 'user2': users[1], 'common_friends': common, 'common_number': len(common)})
    else:
        if 'token_expire' in request.session:
            if request.session['token_expire'] is None or datetime.now() > datetime.fromtimestamp(
                    int(request.session['token_expire'])):
                return logout(request)

            user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
            return render(request, "vkapp/find_common_friends.html", {'user': user})
        else:
            return logout(request)


def find_friend_path(request):
    if request.method == 'POST':
        link1 = request.POST['user1']
        link2 = request.POST['user2']

        if link1 is None or link2 is None:
            user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
            return render(request, "vkapp/find_friend_path.html",
                          {'user': user, 'error_message': 'Wrong details, try again!'})

        link1 = link1.split('/')[-1]
        link2 = link2.split('/')[-1]

        if link1 == '' or link2 == '':
            user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
            return render(request, "vkapp/find_friend_path.html",
                          {'user': user, 'error_message': 'Wrong details, try again!'})

        u1, u2, users = vkapi.get_friend_path(request.session['access_token'], link1, link2)

        if users is None:
            user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
            return render(request, "vkapp/find_friend_path.html",
                          {'user': user, 'error_message': 'Wrong details, try again!'})

        return render(request, "vkapp/show_friend_path.html",
                      {'user1': u1, 'user2': u2, 'common_friends': users, 'common_number': len(users)})
    else:
        if 'token_expire' in request.session:
            if request.session['token_expire'] is None or datetime.now() > datetime.fromtimestamp(
                    int(request.session['token_expire'])):
                return logout(request)

            user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
            return render(request, "vkapp/find_friend_path.html", {'user': user})
        else:
            return logout(request)


def friends_graph(request):
    if request.method == 'POST':
        user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
        link = request.POST['user']
        if link is None:
            return render(request, "vkapp/find_friends_graph.html",
                          {'user': user, 'error_message': 'Wrong details, try again!'})

        link = link.split('/')[-1]

        if link == '':
            return render(request, "vkapp/find_friends_graph.html",
                          {'user': user, 'error_message': 'Wrong details, try again!'})

        picture_url = vkapi.get_friends_graph(request.session['access_token'], link)

        if picture_url is None:
            return render(request, "vkapp/find_friends_graph.html",
                          {'user': user, 'error_message': 'Bad user!'})

        user = vkapi.get_user(request.session['access_token'], link)[0]

        return render(request, "vkapp/show_friends_graph.html",
                      {'user': user, 'picture_url': picture_url})
    else:
        if 'token_expire' in request.session:
            if request.session['token_expire'] is None or datetime.now() > datetime.fromtimestamp(
                    int(request.session['token_expire'])):
                return logout(request)

            user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
            return render(request, "vkapp/find_friends_graph.html", {'user': user})
        else:
            return logout(request)


def view_scheduled_comments(request):
    if request.method == 'POST':
        user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
        if not (user['uid'] in vkapi.comment_threads):
            vkapi.comment_threads[user['uid']] = []

        group_domain = request.POST['vk_group']
        group_domain = group_domain.split('/')[-1]
        date = request.POST['post_date']
        ptime = request.POST['post_time']
        comment_text = request.POST['comment']

        if group_domain == '' or date == '' or ptime == '' or comment_text == '':
            return render(request, "vkapp/view_scheduled_comments.html",
                          {'user': user, 'error_message': 'Details error, try again!',
                           'comment_threads': vkapi.comment_threads[user['uid']]})

        post_time = datetime.strptime(date + ' ' + ptime, "%Y-%m-%d %H:%M")

        if (post_time < datetime.now()):
            return render(request, "vkapp/view_scheduled_comments.html",
                          {'user': user, 'error_message': 'Set future time please!',
                           'comment_threads': vkapi.comment_threads[user['uid']]})

        if (post_time - datetime.now()).seconds > 60 * 60 * 5:
            return render(request, "vkapp/view_scheduled_comments.html",
                          {'user': user, 'error_message': 'Too future time!',
                           'comment_threads': vkapi.comment_threads[user['uid']]})

        group = vkapi.get_group(request.session['access_token'], group_domain)
        if group is None:
            return render(request, "vkapp/view_scheduled_comments.html",
                          {'user': user, 'error_message': 'Group link error, try again!',
                           'comment_threads': vkapi.comment_threads[user['uid']]})

        kill = Event()
        t = Thread(target=vkapi.comment, args=(kill, request.session['access_token'], group, post_time, comment_text, user['uid']))
        t.start()

        print(group)
        vkapi.comment_threads[user['uid']].append(
            {'id': len(vkapi.comment_threads[user['uid']]), 'interrupt': kill, 'group_name': group['name'],
             'photo_url': group['photo_medium'], 'post_time': post_time, 'comment_text': comment_text, 'group_link': 'https://vk.com/'+group['screen_name']})

        for i in range(0, len(vkapi.comment_threads[user['uid']])):
            vkapi.comment_threads[user['uid']][i]['id'] = i

        return render(request, "vkapp/view_scheduled_comments.html",
                      {'user': user, 'comment_threads': vkapi.comment_threads[user['uid']]})
    else:
        if 'token_expire' in request.session:
            if request.session['token_expire'] is None or datetime.now() > datetime.fromtimestamp(
                    int(request.session['token_expire'])):
                return logout(request)

            user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]
            if not (user['uid'] in vkapi.comment_threads):
                vkapi.comment_threads[user['uid']] = []

            return render(request, "vkapp/view_scheduled_comments.html",
                          {'user': user, 'comment_threads': vkapi.comment_threads[user['uid']]})
        else:
            return logout(request)


def delete_comment(request):
    if request.method == 'POST':
        comment_delete_id = request.POST['comment_delete']
        user = vkapi.get_user(request.session['access_token'], request.session['user_id'])[0]

        if comment_delete_id == '':
            return render(request, "vkapp/view_scheduled_comments.html",
                          {'user': user, 'comment_threads': vkapi.comment_threads[user['uid']]})

        comment_delete_id = int(comment_delete_id)
        if comment_delete_id < 0 or comment_delete_id >= len(vkapi.comment_threads[user['uid']]):
            return render(request, "vkapp/view_scheduled_comments.html",
                          {'user': user, 'comment_threads': vkapi.comment_threads[user['uid']]})

        vkapi.comment_threads[user['uid']][comment_delete_id]['interrupt'].set()
        del vkapi.comment_threads[user['uid']][comment_delete_id]

        for i in range(0, len(vkapi.comment_threads[user['uid']])):
            vkapi.comment_threads[user['uid']][i]['id'] = i

        return render(request, "vkapp/view_scheduled_comments.html",
                      {'user': user, 'comment_threads': vkapi.comment_threads[user['uid']]})
    else:
        return HttpResponseRedirect("/vk/scheduledcomments")
