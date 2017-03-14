# -*- coding: utf-8 -*-

from .. import db
from ..models import User, Portal, Have
from flask import render_template
from flask_login import login_user, current_user


def dosomething(source, content):
    # 大小写不敏感
    content = content.strip()

    # 设置/修改昵称
    if content[:len(u"设置昵称")] == u"设置昵称":
        username = content[len(u"设置昵称"):].strip()
        import re
        p = re.compile(u'^[a-zA-Z0-9\u4e00-\u9fa5]+$')
        if username == '':
            return '请使用 “设置昵称" + 空格 + 你想起的昵称 来设置昵称'
        elif not p.match(username):
            return '起名也要按基本法! 只允许使用大小写字母,数字及汉字'
        # elif user  # 正则匹配 u'^[a-zA-Z0-9\u4e00-\u9fa5]+$'
        user = User.query.filter_by(wechat_id=source).first()
        if user is not None:
            # 修改昵称
            if User.query.filter_by(username=username).first() is not None:
                # 已被占用，不允许重新设置
                return '此昵称已被占用=。=|||'
            else:
                # 未被占用，可以修改
                user.username = username
                db.session.add(user)
                return '昵称修改成功！'
        else:
            # 设置昵称
            if User.query.filter_by(username=username).first() is not None:
                # 已被占用，不允许重新设置
                return '此昵称已被占用=。=|||'
            else:
                user = User(username=username, wechat_id=source)
                db.session.add(user)
                return 'Agent code设置完成。\n' \
                       '请联系管理员获取操作权限\n' \
                       '命令如下:\n' \
                       '查看portal列表: "list"或"list <页数>"\n' \
                       '查看po信息: "po <po编号>"\n' \
                       '更改指定po你拥有的key数: "key <po编号> <key数量>"'

    # 拦截未设置昵称的和未通过验证的用户的请求
    user = User.query.filter_by(wechat_id=source).first()
    if user is None:  # 没昵称请去设置昵称
        return '请先使用 “设置昵称” + 空格 + 你想起的昵称 来设置昵称'
    if not user.confirmed:  # 没认证请联系管理员进行认证
        return '您没有该操作权限, 请联系管理员.'
    else:  # 认证了给个登录
        login_user(user, False)
    if content[:len(u"list")].lower() == u"list":
        prep = content.split(' ')
        try:
            page = int(prep[1])
        except IndexError:
            page = 1
        except ValueError:
            return '查看po列表: "list <页数>"\n' \
                   '页数请输入数字'
        if page <= 0:
            page = 1
        if current_user.perpage > 50:
            perpage = 50
        else:
            perpage = current_user.perpage
        pagination = Portal.query.order_by(Portal.id.asc()).\
            paginate(page, per_page=perpage or 20, error_out=False)
        portals = pagination.items
        if len(portals) == 0:
            page = pagination.pages
            pagination = Portal.query.order_by(Portal.id.asc()).\
                paginate(page, per_page=perpage or 20, error_out=False)
            portals = pagination.items
        return render_template('wechat/po.txt', pagination=pagination, portals=portals)
    elif content[:len(u"key")].lower() == u"key":
        prep = content.split(' ')
        try:
            po_id = prep[1]
            count = int(prep[2])
        except IndexError:
            return '更改指定po你拥有的key数: "key <po编号> <key数量>"'
        except ValueError:
            return '数量应为数字'
        if count < 0:
            return '数量应大于0'
        po = Portal.query.filter_by(id=po_id).first()
        if po is not None:
            ha = Have.query.filter_by(portal_id=po_id,
                                      user_id=current_user.id).first()
            if ha is not None:
                ha.count = count
            else:
                ha = Have(portal_id=po_id, user_id=current_user.id, count=count)
            db.session.add(ha)
            db.session.commit()
            return render_template('wechat/po.txt', portals=[po])
        else:
            return 'po编号错误!'
    elif content[:len(u"po")].lower() == u"po":
        prep = content.split(' ')
        try:
            po_id = prep[1]
        except IndexError:
            return '查看po信息: "po <po编号>"\n' \
                   '没找到po编号'
        po = Portal.query.filter_by(id=po_id).first()
        if po is None:
            return '没找到编号对应的po\n' \
                   '请试试"list"查看po列表'
        return render_template("wechat/po.txt", portals=[po], need_link=True)
    elif content[:len(u"perpage")].lower() == u"perpage":
        prep = content.split(' ')
        try:
            perpage = int(prep[1])
        except IndexError:
            return '参数不全\n' \
                   '用法：perpage <分页数(10~100)>'
        except ValueError:
            return '分页数应该是一个十进制数～'
        if 10 <= perpage <= 100:
            current_user.perpage = perpage
            db.session.add(current_user)
            return '分页数已经设置为%d' % perpage
        else:
            return '分页数应在10~100之间'

    elif content[:len(u"whoami")].lower() == u"whoami":
        return '我认得你, 你是%s' % current_user.username
    elif content[:len(u"申请后台权限")] == u"申请后台权限":
        if current_user.login_confirmed:
            return '已经获得登录权限了'
        if current_user.login_request:
            return '请求已提交给管理员, 稍安毋躁'
        import random
        random_passwd = ''.join([random.choice("abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789")
                                 for i in range(8)])
        # 去掉了可能会引起误会的Oo0iIl1L
        current_user.login_request = True
        current_user.password = random_passwd
        current_user.passwd_changed = False
        db.session.add(current_user)
        return '您的请求已提交, 请联(督)系(促)管理员审核. 您的初始随机密码是%s.(密码只显示一次)' % random_passwd

    return '蛤?\n' \
           '命令如下:\n' \
           '查看portal列表: "list"\n' \
           '查看po信息: "po <po编号>"\n' \
           '更改指定po你拥有的key数: "key <po编号> <key数量>"\n' \
           '设置查看列表的分页数: "perpage <分页数(10~100)>"' \
           '请注意，因为微信消息有最大字符限制，微信端的分页数最高为50'
