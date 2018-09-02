import click


ENV_VAR_PREFIX = 'OPENCANARY_'


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx, **kwargs):
    ctx.obj.update(**kwargs)


def main():
    return cli(obj={}, auto_envvar_prefix=ENV_VAR_PREFIX)


__name__ == '__main__' and main()
