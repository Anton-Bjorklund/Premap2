import sys
from pathlib import Path
from typing import Any, Callable

import torch
import yaml
from torch import LongTensor, Tensor


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
    defaults: dict[str, object] | None = None,
    **kwargs,
) -> list[Path]:
    """Wrapper for PREMAP that takes keyword arguments (instead of commandline arguments).
    For keyword arguments run `get_arguments()` or `uv run premap --help` for options.

    NOTE: The `model` argument can be a `torch.nn.Module` and `dataset` a `[X, labels, xmax, xmin]`.

    Args:
        command_line: Also read commandline arguments.
        post_config: Optional post processing function that takes `arguments.Config`.
        premap_path: Path to the `src` folder of the PREMAP package.
        defaults: Keyword arguments with lower priority than a config file.
        **kwargs: Keyword arguments with higher priority than commandline and config file.

    Returns:
        List of paths to the result files (typically just one) that can be loaded with `torch.load`.
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


def get_arguments(
    print: bool = False,
) -> None | list[tuple[str, type | list, str, Any]]:
    """List the available arguments for premap.
    See also `premap.arguments` and `uv run premap --help`.

    Args:
        print: Print the same message as `uv run premap --help` or return a list of arguments.

    Returns:
        If `print==False` then a list of arguments as tuples with `(argument_name, choices_or_type, help_text, default_value)`.
    """
    with PremapInPath():
        import arguments  # type: ignore

        if print:
            arguments.Config.defaults_parser.print_help()
        else:
            args = []
            for action in arguments.Config.defaults_parser._actions:
                if action.dest == "help":
                    continue
                elif action.choices is not None:
                    choice = action.choices
                elif action.dest == "model":
                    choice = str | torch.nn.Module
                elif action.dest == "dataset":
                    choice = str | tuple[Tensor, LongTensor, Tensor, Tensor]
                elif action.type == arguments.keyvaluef:
                    choice = list[tuple[str, float]]
                elif action.type == arguments.str2bool or action.nargs == 0:
                    choice = bool
                else:
                    choice = action.type
                args.append((action.dest, choice, action.help, action.default))
            return args


def cli():
    """Command line interface for PREMAP (reads arguments from `sys.argv`)."""
    with PremapInPath():
        import preimage_main  # type: ignore

        construct_config(command_line=True)
        preimage_main.main()
