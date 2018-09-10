import os
from pkg_resources import resource_filename
import shutil
import textwrap

import click

ENV_VAR_PREFIX = 'OPENCANARY_'
USER_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".opencanary.conf")


run_dev_app = start_app = stop_app = run_user_module = (
    lambda ctx: print({'ctx': ctx})
)


def config_exists(conf_path):
    return os.path.exists(conf_path)


def copy_config(ctx):
    if config_exists(USER_CONFIG_PATH):
        click.echo(
            "[e] A config file already exists at {}, please move it first".
            format(USER_CONFIG_PATH)
        )
        ctx.exit(1)

    default_conf = resource_filename('opencanary', 'data/settings.json')
    shutil.copy(default_conf, USER_CONFIG_PATH)
    click.echo(
        textwrap.dedent(
            '''
            [*] A sample config file is ready ({conf})
            [*] Edit your configuration, then launch with "{cmd} --start"
            '''.
            format(conf=USER_CONFIG_PATH, cmd=ctx.command_path)
        ).strip()
    )


@click.command()
@click.version_option()
@click.option(
    '--copyconfig', 'action',
    help='Create a default config file at {}'.format(USER_CONFIG_PATH),
    flag_value=copy_config,
)
@click.option(
    '--dev', 'action',
    help='Run the opencanaryd process in the foreground',
    flag_value=run_dev_app,
)
@click.option(
    '--start', 'action',
    help='Start the opencanaryd process',
    flag_value=start_app,
)
@click.option(
    '--stop', 'action',
    help='Stop the opencanaryd process',
    flag_value=stop_app,
)
@click.option(
    '--usermodule', 'action',
    help='Run opencanaryd in foreground with only usermodules enabled',
    flag_value=run_user_module,
)
@click.pass_context
def cli(ctx, action, **kwargs):
    action(ctx)
    ctx.obj.update(**kwargs)


def main():
    return cli(obj={}, auto_envvar_prefix=ENV_VAR_PREFIX)


__name__ == '__main__' and main()
