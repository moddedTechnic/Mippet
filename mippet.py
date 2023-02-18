from dataclasses import dataclass
from pathlib import Path

from mippet import construct, lex, parse, register


@dataclass
class Arguments:
    executable: Path
    target: Path
    build_dir: Path
    extension: str = '.asm'

    @classmethod
    def parse(cls, argv: list[str]):
        executable = Path(argv[0]).resolve()
        target = Path(argv[1]).resolve()
        build_dir = Path.cwd() / 'build'
        return cls(executable, target, build_dir)


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
