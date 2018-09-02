import click


ENV_VAR_PREFIX = 'OPENCANARY_'


copy_config = run_dev_app = start_app = stop_app = run_user_module = (
    lambda *a, **kw: print({'a': a, 'kw': kw})
)


@click.command()
@click.version_option()
@click.option('--copyconfig', 'action', flag_value=copy_config)
@click.option('--dev', 'action', flag_value=run_dev_app)
@click.option('--start', 'action', flag_value=start_app)
@click.option('--stop', 'action', flag_value=stop_app)
@click.option('--usermodule', 'action', flag_value=run_user_module)
@click.pass_context
def cli(ctx, action, **kwargs):
    action(ctx, action, **kwargs)
    ctx.obj.update(**kwargs)


def main():
    return cli(obj={}, auto_envvar_prefix=ENV_VAR_PREFIX)


__name__ == '__main__' and main()
