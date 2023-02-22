from ctypes import ArgumentError
from dataclasses import dataclass
from pathlib import Path

from mippet import construct, lex, parse, register


@dataclass
class Arguments:
    executable: Path
    target: Path
    build_dir: Path
    verbose: bool = False
    extension: str = '.asm'

    @classmethod
    def parse(cls, argv: list[str]):
        args = iter(argv)
        executable = Path(next(args)).resolve()
        target = None
        build_dir = Path.cwd() / 'build'
        verbose = False
        extension = '.asm'
        for arg in args:
            if not arg.startswith('-'):
                target = Path(arg).resolve()
            match arg:
                case '-d' | '--dir':
                    build_dir = Path(next(args)).resolve()
                case '-e' | '--extension':
                    extension = next(args)
                case '-v' | '--verbose':
                    verbose = True
        if target is None:
            raise ArgumentError(f'Could not find a target to build')
        return cls(executable, target, build_dir, verbose, extension)


def build_dir(args: Arguments, target: Path):
    target_relative = target.relative_to(Path.cwd())
    print(f'Entering {target_relative}')
    for child in target.glob('*'):
        build(args, child)


def build_file(args: Arguments, target: Path):
    target_relative = target.relative_to(Path.cwd())
    print(f'Building {target_relative}')
    source = target.read_text()
    ast = parse(lex(source))
    context = register(ast)
    context.validate()
    context.verbose = args.verbose
    result = construct(ast, context)
    target_path = target_relative
    build_target = (args.build_dir / target_path).with_suffix(args.extension)
    build_target.parent.mkdir(parents=True, exist_ok=True)
    build_target.write_text(result)


def build(args: Arguments, target: Path):
    if target.is_dir():
        return build_dir(args, target)
    if target.is_file():
        return build_file(args, target)
    target_relative = target.relative_to(Path.cwd())
    print(f'Skipping {target_relative}: not a file')


def main(argv: list[str]):
    args = Arguments.parse(argv)
    build(args, args.target)
    return None


if __name__ == "__main__":
    import sys
    exit(main(sys.argv))
