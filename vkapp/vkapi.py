import vk
from urllib.parse import parse_qs
from datetime import datetime
import time
import requests
import networkx
import matplotlib

matplotlib.use('Agg')
import pylab
from threading import Lock

APP_ID = '6231329'
STANDALONE_APP_ID = '6266014'


def get_auth_params_by_url(redirected_url):
    try:
        aup = parse_qs(redirected_url)
        aup['access_token'] = aup.pop('https://oauth.vk.com/blank.html#access_token')
        return aup['access_token'][0], aup['user_id'][0], aup['expires_in'][0]
    except:
        return None, None, None


def get_auth_params_by_login_and_password(login_name, password):
    try:
        session = vk.AuthSession(STANDALONE_APP_ID, login_name, password)
        api = vk.API(session, lang='en')
        return session.get_access_token(), api.users.get()[0]['uid'], '0'
    except:
        return None, None, None


def get_api(access_token):
    session = vk.Session(access_token=access_token)
    return vk.API(session, lang='en')


lock = Lock()


def invoke_api_request(type, api, params):
    lock.acquire()
    try:
        time.sleep(0.33)
        if type == 'users.get':
            if 'fields' in params:
                return api.users.get(user_ids=params['user_ids'], fields=params['fields'])
            else:
                return api.users.get(user_ids=params['user_ids'])
        elif type == 'friends.get':
            if 'fields' in params:
                return api.friends.get(user_id=params['user_id'], fields=params['fields'])
            else:
                return api.friends.get(user_id=params['user_id'])
        elif type == 'exec':
            r = requests.post(params['url'])
            return r.json()
        elif type == 'groups.get':
            if 'fields' in params:
                return api.groups.getById(group_id=params['group_id'], fields=params['fields'])
            else:
                return api.groups.getById(group_id=params['group_id'])
        elif type == 'wall.createComment':
            api.wall.createComment(owner_id=params['owner_id'], post_id=params['post_id'], message=params['message'])
        elif type == 'wall.get':
            return api.wall.get(owner_id=params['owner_id'])
        return None
    finally:
        lock.release()


def get_user(access_token, user_id):
    api = get_api(access_token)
    try:
        return invoke_api_request('users.get', api,
                                  {'user_ids': user_id, 'fields': 'photo_200, photo_max_orig, domain'})
    except:
        return None


def get_common_friends(access_token, u1_id, u2_id):
    api = get_api(access_token)
    try:
        users = []
        users.append(
            invoke_api_request('users.get', api, {'user_ids': u1_id, 'fields': 'photo_200, photo_max_orig, domain'})[0])
        users.append(
            invoke_api_request('users.get', api, {'user_ids': u2_id, 'fields': 'photo_200, photo_max_orig, domain'})[0])

        f1 = invoke_api_request('friends.get', api, {'user_id': users[0]['uid'],
                                                     'fields': 'user_id, first_name, last_name, photo_200, photo_max_orig, domain'})
        f2 = invoke_api_request('friends.get', api, {'user_id': users[1]['uid']})
    except:
        return None, None

    result = []
    for friend in f1:
        if friend['user_id'] in f2:
            result.append(friend)
    return users, result


def get_group(access_token, group_id):
    api = get_api(access_token)
    try:
        return invoke_api_request('groups.get', api,
                                  {'group_id': group_id})[0]
    except:
        return None


def get_all_friends(api, access_token, ids):
    ids = ids[:25]

    details = invoke_api_request('users.get', api, {'user_ids': ids})
    ids = []
    for user in details:
        if not 'deactivated' in user:
            ids.append(user['uid'])

    text = ''
    for id in ids:
        text += 'API.friends.get({"user_id":"' + str(id) + '"})'
        if id != ids[-1]:
            text += ','

    code = 'return [' + text + '];'
    response_data = invoke_api_request('exec', api, {
        'url': 'https://api.vk.com/method/execute?access_token=' + access_token + '&code=' + code})

    data = response_data['response']
    res = dict()
    i = 0
    for id in ids:
        res[id] = data[i]
        i += 1
    return res


def get_friend_path(access_token, u1_id, u2_id):
    api = get_api(access_token)
    users = []
    try:
        users.append(
            invoke_api_request('users.get', api, {'user_ids': u1_id, 'fields': 'photo_200, photo_max_orig, domain'})[0])
        users.append(
            invoke_api_request('users.get', api, {'user_ids': u2_id, 'fields': 'photo_200, photo_max_orig, domain'})[0])
    except:
        return None, None, None

    if 'deactivated' in users[0] or 'deactivated' in users[1]:
        return None, None, None

    u1_id = users[0]['uid']
    u2_id = users[1]['uid']

    if u1_id == u2_id:
        return users[0], users[0], users

    f1 = {u1_id}
    f2 = {u2_id}
    go_left = dict()
    go_right = dict()

    common_friend = None
    for i in range(0, 2):
        new_friends1 = set()
        curr_friends = []
        for old_friend in list(f1):
            curr_friends.append(old_friend)

            if len(curr_friends) == 25 or old_friend == list(f1)[-1]:

                set_of_friends = get_all_friends(api, access_token, curr_friends)
                ss = set()
                i = -1
                for ky in set_of_friends:
                    ss = ss.union(set_of_friends[ky])
                    i += 1
                    for cc in set_of_friends[ky]:
                        if cc in f1:
                            continue

                        go_left[cc] = ky
                        if cc in f2:
                            common_friend = cc
                            break

                if common_friend is not None:
                    break

                new_friends1 = new_friends1.union(ss)
                curr_friends = []

        f1 = f1.union(new_friends1)

        if common_friend is not None:
            break

        new_friends2 = set()
        curr_friends = []
        for old_friend in list(f2):
            curr_friends.append(old_friend)

            if len(curr_friends) == 25 or old_friend == list(f2)[-1]:
                set_of_friends = get_all_friends(api, access_token, curr_friends)

                i = -1
                ss = set()
                for ky in set_of_friends:
                    i += 1
                    ss = ss.union(set_of_friends[ky])
                    for cc in set_of_friends[ky]:
                        if cc in f2:
                            continue

                        go_right[cc] = ky
                        if cc in f1:
                            common_friend = cc
                            break

                if common_friend is not None:
                    break

                new_friends2 = new_friends2.union(ss)
                curr_friends = []

        f2 = f2.union(new_friends2)

        if common_friend is not None:
            break

    if common_friend is None:
        return users[0], users[-1], []

    path = [common_friend]
    curr = common_friend
    while curr != int(u1_id):
        curr = go_left[curr]
        path = [curr] + path

    curr = common_friend
    while curr != int(u2_id):
        curr = go_right[curr]
        path.append(curr)

    users = []
    details = invoke_api_request('users.get', api, {'user_ids': path, 'fields': 'photo_200, photo_max_orig, domain'})
    for x in path:
        for u in details:
            if int(u['uid']) == x:
                users.append(u)

    return users[0], users[-1], users


def get_friends(api, access_token, ids):
    ids = ids[:25]

    details = invoke_api_request('users.get', api, {'user_ids': ids})
    ids = []
    for user in details:
        if not 'deactivated' in user:
            ids.append(user['uid'])

    text = ''
    for id in ids:
        text += 'API.friends.get({"user_id":"' + str(id) + '"})'
        if id != ids[-1]:
            text += ','

    code = 'return [' + text + '];'

    response_data = invoke_api_request('exec', api, {
        'url': 'https://api.vk.com/method/execute?access_token=' + access_token + '&code=' + code})

    res = dict()
    for i in range(0, len(ids)):
        res[ids[i]] = response_data['response'][i]
    return res


def get_friends_graph(access_token, user_id):
    api = get_api(access_token)
    try:
        user = invoke_api_request('users.get', api, {'user_ids': user_id})[0]
        user_id = user['uid']
    except:
        return None

    graph = {}
    friend_ids = invoke_api_request('friends.get', api, {'user_id': user_id})

    curr = []
    friends = []
    for f_id in friend_ids:
        curr.append(f_id)
        if len(curr) > 999 or f_id == friend_ids[-1]:
            friends = friends + invoke_api_request('users.get', api, {'user_ids': curr})
            curr = []

    curr = []
    labels = dict()
    for friend in friends:
        if 'deactivated' in friend:
            continue

        friend_id = friend['uid']
        labels[friend_id] = (friend['first_name'] + ' ' + friend['last_name'])

        curr.append(friend_id)
        graph[friend_id] = []
        if len(curr) == 25 or friend_id == friend_ids[-1]:
            tmp = get_friends(api, access_token, curr)
            for x in tmp:
                if type(tmp[x]) is list:
                    graph[x] = tmp[x]

            curr = []

    g = networkx.Graph(directed=False)
    for i in graph:
        g.add_node(i)
        if not (i in labels):
            labels[i] = 'no_name'

        for j in graph[i]:
            if i != j and i in friend_ids and j in friend_ids:
                g.add_edge(i, j)

    matplotlib.pyplot.figure(num=None, figsize=(20, 20), dpi=80)
    matplotlib.pyplot.axis('off')
    fig = matplotlib.pyplot.figure(1, encoding='utf-8')
    pos = networkx.spring_layout(g)
    networkx.draw_networkx_nodes(g, pos, node_color='r', node_size=700)
    networkx.draw_networkx_edges(g, pos, width=0.2)
    networkx.draw_networkx_labels(g, pos, labels=labels, font_family='fantasy', font_size=12, encoding='utf-8')

    cut = 1.00
    xmax = cut * max(xx for xx, yy in pos.values())
    ymax = cut * max(yy for xx, yy in pos.values())
    matplotlib.pyplot.xlim(-0.05, xmax + 0.05)
    matplotlib.pyplot.ylim(-0.05, ymax + 0.05)

    filename = './vkapp/static/vkapp/graph_pictures/graph_for_id_' + str(user_id) + '.png'
    matplotlib.pyplot.savefig(filename, bbox_inches="tight", encoding='utf-8')
    pylab.close()
    del fig

    return 'vkapp/graph_pictures/graph_for_id_' + str(user_id) + '.png'


comment_threads = dict()


def comment(kill, access_token, group, time_of_publish, comment_text, myid):
    myid = int(myid)
    api = get_api(access_token)
    while not kill.wait(1):
        if (time_of_publish - datetime.now()).seconds > 30:
            time.sleep(30)
        else:
            break

    post = None
    start_time = datetime.now()
    while not kill.wait(1):
        s = invoke_api_request('wall.get', api, {'owner_id': -group['gid']})

        for p in s[1:3]:
            post_date = datetime.fromtimestamp(int(p['date']))
            if post_date >= time_of_publish:
                post = p

        if post is not None:
            break

        if (datetime.now() - start_time).seconds > 180:
            break

    if not kill.wait(1):
        if post is not None:
            if post['comments']['can_post'] == 1:
                invoke_api_request('wall.createComment', api,
                                   {'owner_id': -group['gid'], 'post_id': post['id'], 'message': comment_text})

        ri = None
        for i in range(0, len(comment_threads[myid])):
            if comment_threads[myid][i]['interrupt'] == kill:
                ri = i

        del comment_threads[myid][ri]

        for i in range(0, len(comment_threads[myid])):
            comment_threads[myid][i]['id'] = i
