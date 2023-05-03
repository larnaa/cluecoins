import click


@click.command
@click.pass_context
@click.option('--db', type=click.Path(exists=True))
def cli(ctx: click.Context, db: str | None) -> None:
    from cluecoins.tui import TUI

    tui = TUI(db)
    tui.run_tui()
