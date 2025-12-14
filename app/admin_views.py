from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, flash


class SecureModelView(ModelView):
    def is_accessible(self):

        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):

        flash('У вас немає прав доступу до панелі адміністратора.', 'danger')
        return redirect(url_for('auth.login'))


class UserView(SecureModelView):

    column_exclude_list = ['password', 'webhook_secret']
    

    column_searchable_list = ['username', 'email']
    

    column_editable_list = ['is_admin', 'telegram_chat_id']


class ProjectView(SecureModelView):
    column_searchable_list = ['name', 'repo_url']
    column_filters = ['author.username']