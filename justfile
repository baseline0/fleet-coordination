@default:
  @just --list

commit *ARGS:
  git commit {{ ARGS }}

test:
  uv run pytest tests/ -v

check: test
