# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request, make_response
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm
from .. import db
from ..models import Role, User, Portal, Permission
from ..decorators import admin_required, permission_required


@main.route('/')
def fake_index():
    return render_template('fake_index.html')


@main.route('/index')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Portal.query.order_by(Portal.timestamp.asc()).\
        paginate(page, per_page=current_user.perpage or 20, error_out=False)
    portals = pagination.items  # enumerate(pagination.items)
    return render_template('index.html', page=page, portals=portals, pagination=pagination)


@main.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        perpage = form.perpage.data
        if 10 <= perpage <= 100:
            current_user.perpage = form.perpage.data
        else:
            return make_response('不要总想着搞个大新闻')
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    form.perpage.data = current_user.perpage
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MANAGE_AGENTS)
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    if user.role.permissions >= current_user.role.permissions and user != current_user:
        abort(403)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        if Role.query.get(form.role.data).permissions > current_user.role.permissions:
            abort(403)
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)
