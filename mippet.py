from dataclasses import dataclass
from pathlib import Path
from pprint import pprint

from mippet import construct, lex, parse


@dataclass
class Arguments:
    executable: Path
    target: Path
    build_dir: Path

    @classmethod
    def parse(cls, argv: list[str]):
        executable = Path(argv[0]).resolve()
        target = Path(argv[1]).resolve()
        build_dir = Path.cwd() / 'build'
        return cls(executable, target, build_dir)


def main(argv: list[str]):
    args = Arguments.parse(argv)
    source = args.target.read_text()
    ast = parse(lex(source))
    result = construct(ast)
    target_path = args.target.relative_to(Path.cwd())
    build_target = args.build_dir / target_path
    build_target.parent.mkdir(parents=True, exist_ok=True)
    build_target.write_text(result)
    return None


if __name__ == "__main__":
    import sys
    exit(main(sys.argv))
