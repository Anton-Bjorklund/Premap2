from pathlib import Path
import sys
from typing import Callable
import yaml


class PremapInPath:
    """
    Add the src folder of the premap repo to the path temporarily.
    So that the local imports continue working (without dots).
    """

    def __init__(self, path: None | str = None):
        if path is not None:
            self.path = path
        else:
            import premap

            self.path = premap.__path__[0]

    def __enter__(self):
        sys.path.insert(0, self.path)

    def __exit__(self, exception_type, exception_value, exception_traceback):
        sys.path.remove(self.path)


def construct_config(
    command_line: bool = False,
    post_config: None | Callable[[object], None] = None,
    defaults: None | dict[str, object] = None,
    **kwargs,
):
    """Construct the `arguments.Config` object for `premap_main`.
    NOTE: This function assumes it is called from within a `with PremapInPath():`.

    Args:
        command_line: Also read commandline arguments.
        post_config: Optional post processing function that takes `arguments.Config`.
        defaults: Keyword arguments with lower priority than a config file.
        **kwargs: Keyword arguments with higher priority than commandline and config file (run `premap --help` for options).
    """
    import arguments  # type: ignore

    # Load default config.
    default_kwargs = vars(arguments.Config.defaults_parser.parse_args([]))
    if defaults is not None:
        default_kwargs.update(defaults)
    arguments.Config.construct_config_dict(default_kwargs)
    # Load command line args.
    if command_line:
        kwargs = vars(arguments.Config.no_defaults_parser.parse_args()) | kwargs
    # Read the yaml config files.
    if "config" in kwargs:
        with open(kwargs["config"], "r") as config_file:
            loaded_args = yaml.safe_load(config_file)
            arguments.Config.update_config_dict(arguments.Config.all_args, loaded_args)
    # Override with keyword args.
    arguments.Config.construct_config_dict(kwargs, nonexist_ok=False)
    if post_config is not None:
        post_config(arguments.Config)


def premap(
    command_line: bool = False,
    post_config: None | Callable[[object], None] = None,
    premap_path: None | str = None,
    defaults: dict[str, object] = {},
    **kwargs,
) -> list[Path]:
    """Wrapper for PREMAP that takes keyword arguments (instead of commandline arguments).

    Args:
        command_line: Also read commandline arguments.
        post_config: Optional post processing function that takes `arguments.Config`.
        premap_path: Path to the `src` folder of the PREMAP package.
        defaults: Keyword arguments with lower priority than a config file.
        **kwargs: Keyword arguments with higher priority than commandline and config file (run `premap --help` for options).

    Returns:
        List of paths to the result files (typically just one).
    """
    with PremapInPath(premap_path):
        import preimage_main  # type: ignore

        construct_config(
            command_line=command_line,
            post_config=post_config,
            defaults=defaults,
            **kwargs,
        )
        return preimage_main.main()


def cli():
    """Command line interface for PREMAP (reads arguments from `sys.argv`)."""
    with PremapInPath():
        import preimage_main  # type: ignore

        construct_config(command_line=True)
        preimage_main.main()
