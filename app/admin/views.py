# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from . import admin
from .forms import PortalCSVForm
from .. import db, log
from ..models import Role, User, Permission, Portal, Have
from ..decorators import permission_required, admin_required


@admin.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/admin.html')


@admin.route('/agent_management')
@login_required
@permission_required(Permission.VERIFY_AGENTS)
def agent_manage():
    agents_wechat = User.query.filter_by(confirmed=False).all()
    agents_web = User.query.filter_by(login_request=True).all()
    return render_template('admin/agent_management.html',
                           agents_web=agents_web, agents_wechat=agents_wechat)


@admin.route('/agent_management/confirm/wechat/<user_id>')
@login_required
@permission_required(Permission.VERIFY_AGENTS)
def agent_confirm_wechat(user_id):
    user = User.query.filter_by(id=user_id).first()
    user.confirmed = True
    db.session.add(user)
    flash('已允许 %s 在微信提交keys.' % user.username)
    log(current_user, '已允许 %s 登陆微信端.' % user.username)
    return redirect(url_for('admin.agent_manage'))


@admin.route('/agent_management/confirm/web/<user_id>')
@login_required
@permission_required(Permission.VERIFY_AGENTS)
def agent_confirm_web(user_id):
    user = User.query.filter_by(id=user_id).first()
    user.login_confirmed = True
    user.login_request = False
    user.role_id = Role.query.filter_by(name='User').first().id
    db.session.add(user)
    flash('已允许 %s 登录网页端.' % user.username)
    log(current_user, '已允许 %s 登录网页端.' % user.username)
    return redirect(url_for('admin.agent_manage'))


@admin.route('/insert_portals', methods=['POST', 'GET'])
@login_required
@admin_required
def insert_portals():
    form = PortalCSVForm()
    if form.validate_on_submit():
        text = form.text.data
        # https://www.ingress.com/intel?ll=39.089453,117.178838&z=17&pll=39.089453,117.178838
        import re, csv
        p = re.compile(u'https://(www\.|)ingress\.com/intel\?ll=(\d+\.\d+),(\d+\.\d+)&z=\d+&pll=(\d+\.\d+),(\d+\.\d+)')
        portals = []
        cf = csv.reader(text.split('\r\n'))
        for row in cf:
            print(row)
            try:
                int(row[0])
                name, area, link = row[1], row[2], row[3]
            except ValueError:
                continue
            except IndexError:
                continue
            portals.append([name, area, link])
        if len(portals) == 0:
            log(current_user, '导入po list失败')
            flash('导入...失败!')
            return redirect(url_for('admin.insert_portals'))
        for portal in portals:
            name, area, link = u'%s' % portal[0], u'%s' % portal[1], u'%s' % portal[2]
            m = p.match(link)
            if m is None:
                link = None
            old_po = Portal.query.filter_by(link=link).first()
            if old_po:
                if old_po.name == name:
                    continue
                else:
                    link = None
            po = Portal(name=name, area=area, link=link)
            db.session.add(po)
        flash('导入成功! 共%d个po信息' % len(portals))
        log(current_user, '批量导入po成功，共导入%d个' % len(portals))
        return redirect(url_for('main.index'))
    return render_template('admin/insert_portals.html', form=form)


@admin.route('/get_csv/po_list')
@login_required
@permission_required(Permission.VIEW_ALL_POS)
def download_csv_po_list():
    import csv
    import time
    import urllib
    import StringIO
    filename = urllib.quote('all-portal-%s.csv' % time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()))
    io = StringIO.StringIO()
    writer = csv.writer(io)
    writer.writerow(['id', 'name', 'area', 'link'])
    for po in Portal.query.all():
        writer.writerow([po.id, po.name, po.area, po.link])
    response = make_response(io.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=%s;" % filename
    log(current_user, '下载了po list csv文件')
    return response


@admin.route('/agent-list')
@login_required
@permission_required(Permission.MANAGE_AGENTS)
def agent_list():
    """
    为管理员及超级管理员准备的用户名单
    允许封禁/解封用户 设定低权用户权限
    :return:
    """
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.last_seen.desc()).paginate(page, per_page=current_user.perpage or 20,
                                                                     error_out=False)
    agents = pagination.items
    return render_template('admin/agent_list.html',
                           agents=agents, pagination=pagination, page=page)



@admin.route('/agent_groups')
@login_required
@permission_required(Permission.MANAGE_GROUPS)
def agent_groups():
    """
    管理用户集合
    :return:
    """
    pass


@admin.route('/po-groups')
@login_required
@permission_required(Permission.MANAGE_GROUPS)
def po_groups():
    """
    管理po集合
    :return:
    """
    pass
