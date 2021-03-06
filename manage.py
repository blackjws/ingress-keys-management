# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os
from app import create_app, db
from app.models import User, Role, Permission
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('ENL_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Permission=Permission)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
    from flask_migrate import upgrade
    from app.models import Role, User

    upgrade()

    Role.insert_roles()
    set_admin()


def set_admin():
    email = raw_input('admin email:')
    username = raw_input('admin username:')
    passwd = raw_input('passwd:')
    role = Role.query.filter_by(name='Administrator').first()
    u = User(email=email, username=username, password=passwd, confirmed=True, login_confirmed=True)
    u.role = role
    db.session.add(u)
    db.session.commit()

if __name__ == '__main__':
    manager.run()
